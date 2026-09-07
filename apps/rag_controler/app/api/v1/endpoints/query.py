from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag_schemas import RAGResponse
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post(
    "/query",
    response_model=RAGResponse,
    summary="Query RAG",
    description=("Query"),
)
@limiter.limit(get_settings().RATE_LIMIT_EXTRACT)
async def query(
    request: Request,
) -> RAGResponse:
    request_id = getattr(request.state, "request_id", None)
    res = RAGResponse(reply="test", request_id=request_id)
    return res
