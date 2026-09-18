from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHUNK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
