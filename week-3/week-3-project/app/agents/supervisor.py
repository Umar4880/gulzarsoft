from app.agents.graph.state import AgentState
from app.core.prompt_loader import PromptManager
from app.models.output import SupervisorOutput

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import Runnable
from langgraph.graph import END
from langgraph.types import Command
class SupervisorAgent:
    def __init__(
            self, 
            llm: ChatGoogleGenerativeAI, 
            prompt_manager: PromptManager):
        
        self.prompt_mng = prompt_manager
        self.llm = llm
        self._chain = self._build_chain()

    def _build_chain(self) -> Runnable:
        prompt = self.prompt_mng.load_agent_system_prompt(agent_name="supervisor", include_history=True)

        retry_llm = self.llm.with_structured_output(SupervisorOutput).with_retry(
            stop_after_attempt=3,
        )
        
        return prompt | retry_llm

    @staticmethod
    def _state_value(state: AgentState, key: str, default=None):
        if isinstance(state, dict):
            return state.get(key, default)

        return getattr(state, key, default)

    @staticmethod
    def _normalize_route(next_agent: str) -> str:
        route = (next_agent or "").strip().lower()

        if route in {"researcher", "__researcher__"}:
            return "researcher"
        if route in {"writer", "__writer__"}:
            return "writer"
        if route in {"critic", "__critic__"}:
            return "critic"
        if route in {"end", "finish", "__end__", "__finish__"}:
            return END

        return END

    async def supervise(self, state: AgentState):
        print("====== in sepervisor ======")
        result = await self._chain.ainvoke(
            {
                "user_input": self._state_value(state, "user_query", ""),
                "history": self._state_value(state, "messages", []),
            }
        )
        next_agent = self._normalize_route(result.next_agent)
        return Command(
            goto=next_agent,
            update={
                "next_agent": next_agent,
                "route_reason": result.reason,
                "messages": [
                    AIMessage(
                        content=f"Supervisor routed to {next_agent}: {result.reason}"
                    )
                ],
            },
        )
