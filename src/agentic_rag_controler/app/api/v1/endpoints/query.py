from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from langfuse.langchain import CallbackHandler
from langfuse import propagate_attributes

from app.dependencies import get_agent, get_obs_client
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
    request: Request,
    payload: Ask,
    agent_client=Depends(get_agent),
    langfuse_client=Depends(get_obs_client),
) -> AgentResponse:
    request_id = getattr(request.state, "request_id", None)
    handler = CallbackHandler()

    # reply = await graph_client.invoke(payload.question)
    with langfuse_client.start_as_current_observation(
        name="general-help", as_type="agent", input={"question": payload.question}
    ) as root:
        with propagate_attributes(
            user_id=str(payload.user_id),
            session_id=str(payload.conversation_id),
            tags=["prompt-v1"],
            metadata={"team": payload.user_role, "request_id": request_id},
        ):
            reply = await agent_client.ainvoke(
                payload.question, config={"callbacks": [handler]}
            )
            answer = reply["messages"][-1].text
            root.update(output=answer)
    res = AgentResponse(
        reply=answer, request_id=request_id, conversation_id=payload.conversation_id
    )
    return res
