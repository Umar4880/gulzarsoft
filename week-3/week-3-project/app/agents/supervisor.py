import json
import re

from app.agents.graph.state import AgentState
from app.core.prompt_loader import PromptManager

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END
from langgraph.types import Command
class SupervisorAgent:
    def __init__(
            self, 
            llm: BaseChatModel, 
            prompt_manager: PromptManager):
        
        self.prompt_mng = prompt_manager
        self.llm = llm
        self._chain = self._build_chain()

    def _build_chain(self) -> Runnable:
        prompt = self.prompt_mng.load_agent_system_prompt(agent_name="supervisor", include_history=True)

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

    @staticmethod
    def _extract_route_and_reason(response_text: str) -> tuple[str, str]:
        text = (response_text or "").strip()
        if not text:
            return END, "No route reason was provided."

        # Prefer JSON when present.
        if "{" in text and "}" in text:
            try:
                json_str = text[text.find("{") : text.rfind("}") + 1]
                parsed = json.loads(json_str)
                route = str(parsed.get("next_agent", "end")).strip().lower()
                reason = str(parsed.get("reason", "No route reason was provided.")).strip()
                return route, reason
            except (ValueError, TypeError, json.JSONDecodeError):
                pass

        # Fallback: parse route labels from plain text.
        route_match = re.search(r"\b(researcher|writer|critic|end|finish)\b", text, re.IGNORECASE)
        route = route_match.group(1).lower() if route_match else "end"

        reason_match = re.search(r"reason\s*:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if reason_match:
            reason = reason_match.group(1).strip()
        else:
            # Keep reason concise and avoid dumping full generated report into route reason.
            first_line = text.splitlines()[0].strip() if text.splitlines() else text
            reason = first_line[:220]

        return route, (reason or "No route reason was provided.")

    async def supervise(self, state: AgentState):
        print("====== in sepervisor ======")
        result = await self._chain.ainvoke(
            {
                "user_input": self._state_value(state, "user_query", ""),
                "history": self._state_value(state, "messages", []),
            }
        )
        
        response_text = result.content if hasattr(result, "content") else str(result)
        next_agent_raw, reason = self._extract_route_and_reason(response_text)
        next_agent = self._normalize_route(next_agent_raw)

        return Command(
            goto=next_agent,
            update={
                "next_agent": next_agent,
                "route_reason": reason,
                "messages": [
                    AIMessage(
                        content=f"Supervisor routed to {next_agent}: {reason}"
                    )
                ],
            },
        )
