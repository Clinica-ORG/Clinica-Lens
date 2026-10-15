from functools import lru_cache
from typing import Literal
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RecursiveConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100
    separators: list[str] = ["\n\n", "\n", " ", ""]


class CharacterConfig(BaseModel):
    chunk_size: int = 450
    chunk_overlap: int = 50
    separator: str = "\n\n"


class TokenConfig(BaseModel):
    chunk_size: int = 450
    chunk_overlap: int = 50


class HeaderConfig(BaseModel):
    headers_to_split_on: list[tuple[str, str]] = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    strip_headers: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INGEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # aws
    aws_region: str = "eu-west-3"
    # datalab
    datalab_api_key_secret_name: str = "/clinica-lens/datalab-api-key"
    # OpenAI
    openai_api_key_secret_name: str = "/clinica-lens/openai-api-key"
    openai_emb_model_name: Literal[
        "text-embedding-3-small", "text-embedding-3-large"
    ] = "text-embedding-3-small"
    openai_llm_model_name: Literal["gpt-4o-mini", "gpt-4o"] = "gpt-4o-mini"
    # vector db
    vectordb_api_key_secret_name: str = "/clinica-lens/qdrant-api-key"
    vectordb_endpoint: str = "https://ef914b8a-6ca1-4294-ba19-1b156e3ce8d2.eu-central-1-0.aws.cloud.qdrant.io"
    # doc processing
    vlm_toc: bool = True

    # splitter
    strategies: list[str] = ["recursive", "character", "token", "header"]

    recursive: RecursiveConfig = RecursiveConfig()
    character: CharacterConfig = CharacterConfig()
    token: TokenConfig = TokenConfig()
    header: HeaderConfig = HeaderConfig()

    def get_splitter_params(self) -> dict:
        """get params of splitting strategy."""
        dict_params = {}
        for strat in self.strategies:
            dict_params[strat] = getattr(self, strat).model_dump()
        return dict_params


@lru_cache
def get_settings() -> Settings:
    return Settings()
