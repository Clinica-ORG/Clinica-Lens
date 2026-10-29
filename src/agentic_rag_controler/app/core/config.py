"""
Inference-time parameters (conf, iou, etc), one block per stage.
Values come from env vars injected by Helm from
helm/.../vision-service/values.yaml -> values-{local,cloud}.yaml overrides.
"""

import os
from dataclasses import field
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parents[1]


def _env_list(name: str, default: list[str]) -> list[str]:
    """Read a list from an environment variable, split by commas, e.g., CORS_ORIGINS=a.com,b.com"""
    v = os.environ.get(name)
    if v is None:
        return default
    return [x.strip() for x in v.split(",") if x.strip()]


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Clinica-lens"
    APP_VERSION: str = "v1"
    API_V1_PREFIX: str = "/api/v1"
    SERVICE_NAME: str = "agent-rag-service"
    # LLM
    LLM_MODEL: str = "openai:gpt-6-luna"
    OPENAI_API_KEY: str = ""
    # POSGRES DB
    PG_DB_URL: str = ""
    # Obs
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""
    LANGSMITH_ENDPOINT: str = "https://eu.api.smith.langchain.com"
    # Middleware
    INFERENCE_MAX_WORKERS: int = 1
    INFERENCE_MAX_QUEUE: int = 10
    RATE_LIMIT_EXTRACT: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"
    # --- CORS ---
    CORS_ORIGINS: list[str] = field(
        default_factory=lambda: _env_list("CORS_ORIGINS", ["*"])
    )
    TRUSTED_HOSTS: list[str] = field(
        default_factory=lambda: _env_list("TRUSTED_HOSTS", ["*"])
    )

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    LOG_DIR: str = str(ROOT_DIR / "logs")
    LOG_RETENTION_DAYS: int = 3

    class Config:
        env_prefix = "AGENT_"  # reads RAG_<ENV>
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
if settings.LANGSMITH_TRACING:
    os.environ["LANGSMITH_TRACING_V2"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
    # os.environ["LANGSMITH_AGENT_ID"] = 'clinica-lens'
    # os.environ["LANGSMITH_ENDPOINT"] = 'https://api.smith.langchain.com'
