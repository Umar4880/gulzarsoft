from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.graph.graph import AgentGraph
from app.core.llm_provider import get_llm
from app.core.prompt_loader import PromptManager


class GraphRunner:
    """Lazy wrapper around AgentGraph used by the service layer."""

    def __init__(self, graph: Optional[AgentGraph] = None) -> None:
        self._graph = graph

    def _build_llm(self) -> BaseChatModel:
        return get_llm(agent_name="graph", user_id="system")

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

        print("======= in graph runer ========")

        try:
            result = await graph.ainvoke(user_query=user_query, thread_id=thread_id)
        except TypeError:
            result = await graph.ainvoke(user_query, thread_id)

        if isinstance(result, dict):
            return result

        if hasattr(result, "model_dump"):
            return result.model_dump()

        return {"result": result}
