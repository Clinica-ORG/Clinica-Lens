from pydantic import BaseModel


class AuthResponse(BaseModel):
    status: str
    access_token: str