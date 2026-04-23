from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Setting(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "Bravous Research Agent"
    ENV: Literal["prod", "dev", "staging"] = "dev"
    DEBUG: bool = False

    REDIS_URL: str = ""
    APP_DATABASE_URL: str = ""
    CHECKPOINT_DATABASE_URL: str = ""

    TAVILY_SEARCH_API: str = ""

    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "llama3.2:latest"
    TEMPERATURE: float = 0.2

    ALLOWED_ORIGINS: str = "*"

    @property
    def CHECKPOINT_CONN_STRING(self) -> str:
        # Backward-compatible alias for older references.
        return self.CHECKPOINT_DATABASE_URL

setting = Setting()