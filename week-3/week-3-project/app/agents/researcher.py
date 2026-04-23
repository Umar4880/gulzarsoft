from app.agents.graph.state import AgentState
from app.core.prompt_loader import PromptManager
from app.tools.web_search_tool import web_search_tool

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from langchain.agents import create_agent

class ResearchAgent:
    def __init__(self, llm: BaseChatModel, prompt_manager: PromptManager):
        self.prompt_mng = prompt_manager
        self.llm = llm
        self._chain = self._build_chain()

    def _build_chain(self) -> Runnable:
        system_prompt = self.prompt_mng.load_agent_system_prompt("researcher", include_history=False)

        agent = create_agent(
            self.llm,
            tools=[web_search_tool],
        )
        agent = agent.with_retry(
            stop_after_attempt=3,
        )
        return system_prompt | agent

    @staticmethod
    def _state_value(state: AgentState, key: str, default=None):
        if isinstance(state, dict):
            return state.get(key, default)

        return getattr(state, key, default)
    
    async def research(self, state: AgentState):

        print("====== in research ======")

        query = self._state_value(state, "user_query", "")
        result = await self._chain.ainvoke({
            "user_input": query,
            "user_query": query,
        })

        messages = result.get("messages") if isinstance(result, dict) else getattr(result, "messages", None)
        if not messages:
            research_text = ""
        else:
            last_message = messages[-1]
            research_text = last_message.content if hasattr(last_message, "content") else str(last_message)

        return {
            "research_findings": research_text,
            "messages": [AIMessage(content=f"Research findings: {research_text}")],
        }
