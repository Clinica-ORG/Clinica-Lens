"""Runs: send a message (or a decision) and receive the run as a text/event-stream."""

from collections.abc import AsyncIterable

from fastapi import APIRouter, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langgraph.types import Command

from app.core.config import get_settings
from app.core.security import CurrentUser
from app.dependencies import (
    Agent,
    IdleThread,
    InterruptedThread,
    Running,
    Store,
    ObsClient,
)
from app.schemas.agent_schemas import ResumeRequest, RunRequest
from app.services import threads
from app.services.streaming import run_events, short

router = APIRouter(prefix="/threads/{thread_id}", tags=["runs"])


@router.post("/runs", response_class=EventSourceResponse)
async def create_run(
    request: Request,
    body: RunRequest,
    thread: IdleThread,
    user: CurrentUser,
    agent: Agent,
    store: Store,
    running: Running,
    obs: ObsClient,
) -> AsyncIterable[ServerSentEvent]:
    """Send a message to the agent on this thread; the response streams the run as Server-Sent Events."""
    if thread.title == "New chat":  # the first message names the thread in the list
        await threads.set_title(store, user.user_id, thread, short(body.message, 60))
    request_id = getattr(request.state, "request_id", None)
    payload = {"messages": [{"role": "user", "content": body.message}]}
    async for event in run_events(
        agent=agent,
        running=running,
        user_id=user.user_id,
        user_group=user.group,
        thread_id=thread.thread_id,
        request_id=request_id,
        payload=payload,
        timeout_s=get_settings().RUN_TIMEOUT_S,
        obs=obs,
    ):
        yield event


@router.post("/resume", response_class=EventSourceResponse)
async def resume_run(
    body: ResumeRequest,
    thread: InterruptedThread,
    user: CurrentUser,
    agent: Agent,
    running: Running,
) -> AsyncIterable[ServerSentEvent]:
    """Answer the pending approval (approve or reject) and stream the rest of the run."""
    decision = {"type": body.decision}
    if body.decision == "reject" and body.message:
        decision["message"] = body.message  # the model reads the reason
    command = Command(
        resume={"decisions": [decision]}
    )  # the format HumanInTheLoopMiddleware expects
    async for event in run_events(
        agent,
        running,
        user.user_id,
        thread.thread_id,
        command,
        get_settings().RUN_TIMEOUT_S,
    ):
        yield event
