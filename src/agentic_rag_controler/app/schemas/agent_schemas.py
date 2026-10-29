from pydantic import BaseModel


class AgentResponse(BaseModel):
    reply: str
    request_id: str


class Ask(BaseModel):
    question: str
