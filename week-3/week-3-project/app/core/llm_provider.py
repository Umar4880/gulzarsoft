from app.core.config import setting
from app.core.callbacks.limiter_handler import RateLimitCallbackHandler
from app.core.callbacks.logging_handler import LoggingCallbackHandler

from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(agent_name: str, user_id: str):

    rate_limiter = RateLimitCallbackHandler(
        user_id = user_id,
        model_name = setting.MODEL_NAME
    )
    logger = LoggingCallbackHandler(
        agent_name =  agent_name,
        user_id = user_id
    )

    return ChatGoogleGenerativeAI(
        api_key = setting.GEMINI_API_KEY,
        model = setting.MODEL_NAME,
        temperature = 1,
        streaming = True,
        callbacks=[rate_limiter, logger]        
    )