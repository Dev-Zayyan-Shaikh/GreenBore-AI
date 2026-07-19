import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GreenBore AI"
    ENV: str = "development"
    API_V1_STR: str = "/api/v1"

    # Parses JSON array strings for CORS origins
    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/greenbore"

    # RAG & LLM Configurations
    GEMINI_API_KEY: str = ""
    RAG_EMBEDDING_DIMENSION: int = 128
    RAG_KNOWLEDGE_DIR: str = "datasets/geological_knowledge"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
