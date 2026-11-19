from pydantic import BaseModel


class AuthResponse(BaseModel):
    status: str
    access_token: str


class User(BaseModel):
    user_id: str
    name: str
    role: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
