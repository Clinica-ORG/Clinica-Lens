from pydantic import BaseModel, SecretStr


class AuthResponse(BaseModel):
    status: str
    access_token: str


class User(BaseModel):
    user_id: str
    name: str
    group: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AWS_Keys(BaseModel):
    qdrant_url: SecretStr
    qdrant_api_key: SecretStr
