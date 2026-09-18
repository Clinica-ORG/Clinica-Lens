from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    VlmPipelineOptions,
)
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options_vlm_model import (
    InlineVlmOptions,
    InferenceFramework,
    TransformersModelType,
    ResponseFormat,
)
from langchain_community.document_loaders import PyPDFLoader
import pymupdf4llm
import pymupdf

from config import get_settings


class VlmTocExtractor:
    def __init__(
        self,
        repo_id: str | None = None,
        prompt: str | None = None,
        device: AcceleratorDevice | None = None,
    ):
        settings = get_settings()

        repo_id = repo_id or settings.vlm_repo_id
        prompt = prompt or settings.vlm_prompt
        device = device or AcceleratorDevice(settings.vlm_device)

        inference_framework = InferenceFramework(settings.vlm_inference_framework)
        response_format = ResponseFormat(settings.vlm_response_format)
        accelerator_options = AcceleratorOptions(device=device)
        pipeline_options = VlmPipelineOptions(
            vlm_options=InlineVlmOptions(
                repo_id=repo_id,
                prompt=prompt,
                response_format=response_format,
                inference_framework=inference_framework,
                transformers_model_type=TransformersModelType.AUTOMODEL_IMAGETEXTTOTEXT,
                supported_devices=[device],
                scale=settings.vlm_scale,
                temperature=settings.vlm_temperature,
                load_in_8bit=False,
                quantized=False,
                torch_dtype=settings.vlm_torch_dtype,
                max_new_tokens=settings.vlm_max_new_tokens,
                use_kv_cache=settings.vlm_use_kv_cache,
            )
        )
        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                    accelerator_options=accelerator_options,
                )
            }
        )

    def extract_page_markdown(
        self, file_path: str, page_start_no: int, page_end_no: int
    ) -> str:
        result = self._converter.convert(
            file_path, page_range=(page_start_no, page_end_no)
        )
        return result.document.export_to_markdown()


class DocLoader:
    def __init__(self):
        self._vlm_extractor: VlmTocExtractor | None = None

    def _get_vlm_extractor(self) -> VlmTocExtractor:
        if self._vlm_extractor is None:
            self._vlm_extractor = VlmTocExtractor()
        return self._vlm_extractor

    def to_docs(self, file_path):
        return PyPDFLoader(file_path).load()

    def to_markdown(self, file_path: str, page_chunks: bool) -> str | list[dict]:
        return pymupdf4llm.to_markdown(file_path, page_chunks=page_chunks)

    def get_toc(
        self, file_path: str, use_vlm: bool = False, toc_page: int | None = None
    ) -> list[list]:
        if not use_vlm:
            return pymupdf.open(file_path).get_toc()
        if toc_page is None:
            raise ValueError("toc_page is required when use_vlm=True")
        # suppose that the toc is spanned only in 1 page
        return self._get_vlm_extractor().extract_page_markdown(
            file_path, toc_page, toc_page
        )
