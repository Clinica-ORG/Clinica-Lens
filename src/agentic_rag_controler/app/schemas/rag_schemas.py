from pydantic import BaseModel


class RAGResponse(BaseModel):
    reply: str
    request_id: str
