from pydantic import BaseModel
from pydantic import ConfigDict, Field
from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass
class Context:
    """Run context filled by the API from the bearer token (LangChain runtime context)."""

    user_id: str


class AgentResponse(BaseModel):
    reply: str
    request_id: str
    conversation_id: UUID


class Ask(BaseModel):
    question: str
    user_id: UUID
    user_role: str
    conversation_id: UUID


class Thread(BaseModel):
    thread_id: str
    title: str
    created_at: str
    status: Literal["idle", "busy", "interrupted"] = "idle"


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str
    name: str | None = None  # tool name for role="tool"
    tool_calls: list[dict] = []


class ThreadDetail(Thread):
    messages: list[Message]
    interrupt: dict | None = None


class RunRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )  # no user_id here: the user comes from the token
    message: str = Field(
        min_length=1,
        max_length=4000,
        examples=["Brief on how well heat pumps work below 0°C."],
    )


class ResumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    message: str | None = Field(
        None, max_length=500, description="Reason sent to the agent when rejecting."
    )
