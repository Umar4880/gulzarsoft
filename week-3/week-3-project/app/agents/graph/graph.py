import logging
import asyncio
from typing import Any, AsyncIterator, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from app.agents.critic import CriticAgent
from app.agents.graph.state import AgentState
from app.agents.researcher import ResearchAgent
from app.agents.supervisor import SupervisorAgent
from app.agents.writer import WriterAgent
from app.core.prompt_loader import PromptManager
from app.db.engine import get_checkpoint_pool

logger = logging.getLogger(__name__)


class AgentGraph:
    def __init__(self, llm: ChatGoogleGenerativeAI, prompt_manager: PromptManager, checkpointer: AsyncPostgresSaver):
        self.llm = llm
        self.prompt_mng = prompt_manager
        self.checkpointer = checkpointer

        self.supervisor = SupervisorAgent(llm=self.llm, prompt_manager=self.prompt_mng)
        self.researcher = ResearchAgent(llm=self.llm, prompt_manager=self.prompt_mng)
        self.writer = WriterAgent(llm=self.llm, prompt_manager=self.prompt_mng)
        self.critic = CriticAgent(llm=self.llm, prompt_manager=self.prompt_mng)

        self.graph = self._build_state_graph()

    @classmethod
    async def create(cls, llm: ChatGoogleGenerativeAI, prompt_manager: PromptManager) -> "AgentGraph":
        checkpoint_pool = get_checkpoint_pool()
        await checkpoint_pool.open()

        checkpointer = AsyncPostgresSaver(conn=checkpoint_pool)
        await checkpointer.setup()

        return cls(llm=llm, prompt_manager=prompt_manager, checkpointer=checkpointer)

    def _build_state_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("supervisor", self.supervisor.supervise)
        graph.add_node("researcher", self.researcher.research)
        graph.add_node("writer", self.writer.write)
        graph.add_node("critic", self.critic.critic)

        graph.set_entry_point("supervisor")

        graph.add_edge("researcher", "supervisor")
        graph.add_edge("writer", "supervisor")
        graph.add_edge("critic", "supervisor")

        return graph.compile(checkpointer=self.checkpointer)

    def _build_config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}

    def _build_initial_state(self, user_query: str) -> dict:
        return AgentState(
            user_query=user_query,
            messages=[HumanMessage(content=user_query)],
        ).model_dump()

    @staticmethod
    def _merge_update(state: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(state)

        for key, value in update.items():
            if key == "messages" and isinstance(value, list):
                merged[key] = list(merged.get(key, [])) + value
            else:
                merged[key] = value

        return merged

    @staticmethod
    def _bump_iteration(state: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        updated = dict(state)
        updated["iteration_count"] = int(updated.get("iteration_count", 0) or 0) + 1
        updated["last_agent"] = agent_name
        return updated

    def invoke(self, user_query: str, thread_id: str) -> Dict[str, Any]:
        return asyncio.run(self.ainvoke(user_query=user_query, thread_id=thread_id))

    async def ainvoke(self, user_query: str, thread_id: str) -> Dict[str, Any]:
        print("======= in graph ainvoke ========")

        state: Dict[str, Any] = self._build_initial_state(user_query)
        state = self._bump_iteration(state, "user")

        for _ in range(6):
            decision = await self.supervisor.supervise(state)
            if isinstance(decision, Command):
                state = self._merge_update(state, decision.update or {})
                next_agent = decision.goto
            else:
                state = self._merge_update(state, decision if isinstance(decision, dict) else {})
                next_agent = state.get("next_agent", END)

            if next_agent == END:
                break

            state = self._bump_iteration(state, str(next_agent))

            if next_agent == "researcher":
                result = await self.researcher.research(state)
            elif next_agent == "writer":
                result = await self.writer.write(state)
            elif next_agent == "critic":
                result = await self.critic.critic(state)
            else:
                break

            state = self._merge_update(state, result)

            if bool(state.get("is_approved", False)) and next_agent == "critic":
                break

        return state

    async def astream(self, user_query: str, thread_id: str):
        async for event in self.graph.astream_events(
            input=self._build_initial_state(user_query),
            config=self._build_config(thread_id),
            version="v2",
        ):
            transformed = self._transform_event(event)
            if transformed:
                yield transformed

    def _transform_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        kind = event.get("event")
        node = event.get("metadata", {}).get("langgraph_node", "")

        if kind == "on_chain_start" and node in ("supervisor", "researcher", "writer", "critic"):
            return {"type": "node_start", "node": node}

        if kind == "on_chain_end" and node in ("supervisor", "researcher", "writer", "critic"):
            return {"type": "node_end", "node": node, "output": event.get("data", {}).get("output")}

        if kind == "on_tool_start":
            return {"type": "tool_start", "tool": event.get("name"), "input": event.get("data", {}).get("input")}

        if kind == "on_tool_end":
            return {"type": "tool_end", "tool": event.get("name"), "output": event.get("data", {}).get("output")}

        return None

    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        state = await self.graph.aget_state(self._build_config(thread_id))
        return state.values if state else None

    async def get_state_history(self, thread_id: str) -> AsyncIterator[Dict[str, Any]]:
        async for snapshot in self.graph.aget_state_history(self._build_config(thread_id)):
            yield {
                "checkpoint_id": snapshot.config["configurable"]["checkpoint_id"],
                "values": snapshot.values,
                "next": snapshot.next,
                "created_at": snapshot.created_at,
            }

    async def resume_from_checkpoint(self, thread_id: str, checkpoint_id: str, resume_value: Any = None) -> Dict[str, Any]:
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }
        command = Command(resume=resume_value) if resume_value else None
        return await self.graph.ainvoke(command, config)