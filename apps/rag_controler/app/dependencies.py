"""
Dependency injection: FastAPI Depends() takes service instance (loaded in lifespan function)
from app.state, instead of creating new one for every request.
"""

from fastapi import Request

from app.services.rag_service import RagService


def get_segmentation_service(request: Request) -> RagService:
    return request.app.state.segmentation_service


def get_inference_executor(request: Request):
    return request.app.state.inference_executor
