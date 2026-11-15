from pydantic import BaseModel
from typing import Literal
from uuid import UUID


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
