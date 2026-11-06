from pydantic import BaseModel
from uuid import UUID


class AgentResponse(BaseModel):
    reply: str
    request_id: str
    conversation_id: UUID


class Ask(BaseModel):
    question: str
    conversation_id: UUID
