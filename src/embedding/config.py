from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EMB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    device: str = "cpu"  # "cuda", "cpu", "mps", "npu"
    model_name: str = "BAAI/bge-base-en-v1.5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
