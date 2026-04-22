from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Setting(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "Bravous Research Agent"
    ENV: Literal["prod", "dev", "staging"] = "dev"
    DEBUG: bool = False

    REDIS_URL: str = ""
    APP_DATABASE_URL: str = ""
    CHECKPOINT_CONN_STRING: str = ""
    CHECKPOINT_DATABASE_URL: str = ""

    TAVILY_SEARCH_API: str = ""

    GEMINI_API_KEY: str = ""
    MODEL_NAME: str = "gemini-1.5-flash"

    ALLOWED_ORIGINS: str = "*"

setting = Setting()