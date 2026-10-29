from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services import AgentService
from app.dependencies import get_agent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.agent_schemas import AgentResponse, Ask

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post(
    "/query",
    response_model=AgentResponse,
    summary="Query RAG",
    description=("Query"),
)
@limiter.limit(get_settings().RATE_LIMIT_EXTRACT)
async def query(
    request: Request, payload: Ask, agent_client: AgentService = Depends(get_agent)
) -> AgentResponse:
    request_id = getattr(request.state, "request_id", None)
    # reply = await graph_client.invoke(payload.question)
    reply = await agent_client.ainvoke(payload.question, config={})
    res = AgentResponse(reply=reply["messages"][-1].text, request_id=request_id)
    return res
