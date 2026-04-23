from app.agents.graph.state import AgentState
from app.core.prompt_loader import PromptManager

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

class WriterAgent:
    def __init__(self, llm: BaseChatModel, prompt_manager: PromptManager):
        self.prompt_mng = prompt_manager
        self.llm = llm
        self._chain = self._build_chain()

    def _build_chain(self) -> Runnable:
        prompt = self.prompt_mng.load_agent_system_prompt(agent_name="writer", include_history=False)
        # Note: Ollama doesn't support structured output, so we use with_retry only
        retry_llm = self.llm.with_retry(
            stop_after_attempt=3,
        )
        return prompt | retry_llm

    @staticmethod
    def _state_value(state: AgentState, key: str, default=None):
        if isinstance(state, dict):
            return state.get(key, default)

        return getattr(state, key, default)

    async def write(self, state: AgentState):
        print("======= in writer ========")
        query = self._state_value(state, "user_query", "")
        result = await self._chain.ainvoke({
            "user_input": query,
            "user_query": query,
            "research_findings": self._state_value(state, "research_findings", ""),
            "critic_feedback": "\n".join(self._state_value(state, "critic_feedback", []) or []),
        })
        # Handle response from Ollama (string, not structured object)
        draft = result.content if hasattr(result, 'content') else str(result)
        return {
            "report_draft": draft,
            "writer_output": {"summary": draft},
            "messages": [AIMessage(content=f"Writer draft: {draft}")],
        }