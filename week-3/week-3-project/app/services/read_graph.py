from __future__ import annotations

from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.graph.graph import AgentGraph
from app.core.config import setting
from app.core.prompt_loader import PromptManager


class GraphRunner:
    """Lazy wrapper around AgentGraph used by the service layer."""

    def __init__(self, graph: Optional[AgentGraph] = None) -> None:
        self._graph = graph

    def _build_llm(self) -> ChatGoogleGenerativeAI:
        temperature = float(getattr(setting, "TEMPRATURE", 0.2))
        model_name = getattr(setting, "MODEL_NAME", "") or "gemini-1.5-flash"

        return ChatGoogleGenerativeAI(
            api_key=setting.GEMINI_API_KEY,
            model=model_name,
            temperature=temperature,
        )

    async def _ensure_graph(self) -> AgentGraph:
        if self._graph is not None:
            return self._graph

        llm = self._build_llm()
        prompt_manager = PromptManager()
        self._graph = await AgentGraph.create(llm=llm, prompt_manager=prompt_manager)
        return self._graph

    async def run(self, user_query: str, thread_id: str) -> dict[str, Any]:
        """Execute the graph and return the final state dict."""
        graph = await self._ensure_graph()

        try:
            result = await graph.ainvoke(user_query=user_query, thread_id=thread_id)
        except TypeError:
            result = await graph.ainvoke(user_query, thread_id)

        if isinstance(result, dict):
            return result

        if hasattr(result, "model_dump"):
            return result.model_dump()

        return {"result": result}
