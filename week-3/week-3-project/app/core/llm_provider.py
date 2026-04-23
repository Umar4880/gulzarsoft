from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.core.callbacks.logging_handler import LoggingCallbackHandler
from app.core.config import setting


def get_llm(agent_name: str = "app", user_id: str = "system") -> BaseChatModel:
    logger = LoggingCallbackHandler(
        agent_name=agent_name,
        user_id=user_id,
    )

    return ChatOllama(
        base_url=setting.OLLAMA_BASE_URL,
        model=setting.OLLAMA_MODEL,
        temperature=setting.TEMPERATURE,
        streaming=True,
        callbacks=[logger],
    )