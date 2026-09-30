from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RecursiveConfig(BaseModel):
    chunk_size: int = 450
    chunk_overlap: int = 50
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
        env_prefix="CHUNK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    openai_api_key: str = ""

    # --- VLM / ToC extraction ---
    # # https://docling-project.github.io/docling/reference/pipeline_options/#docling.datamodel.pipeline_options.VlmExtractionPipelineOptions
    vlm_repo_id: str = "jwindle47/chandra-ocr-2-8bit-mlx"  # "datalab-to/chandra-ocr-2"
    vlm_prompt: str = (
        "Convert this page of table of contents to markdown. "
        "Do not miss any text and only output the bare markdown!"
    )
    vlm_device: str = "mps"  # "mps" | "cuda" | "cpu" | "auto"
    vlm_inference_framework: str = "mlx"  # "mlx" | "transformers" | "vllm"
    vlm_response_format: str = "markdown"
    vlm_scale: float = 1.0
    vlm_temperature: float = 0.0
    vlm_max_new_tokens: int = 2048
    vlm_torch_dtype: str = "bfloat16"
    vlm_use_kv_cache: bool = True

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
