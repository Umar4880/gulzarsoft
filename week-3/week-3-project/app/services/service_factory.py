from functools import lru_cache

from app.services.chat_service import ChatService
from app.services.read_graph import GraphRunner


@lru_cache(maxsize=1)
def build_chat_service() -> ChatService:
    """Build and cache the chat service singleton for the app process."""
    graph_runner = GraphRunner()
    return ChatService(graph_runner=graph_runner)