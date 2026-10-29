from pydantic import BaseModel, SecretStr
from fastapi import APIRouter, Request, HTTPException
import asyncio
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.core.config import get_settings
from app.schemas.auth_schemas import AuthResponse
from app.db.database import fetch_readonly

router = APIRouter()

_ph = PasswordHasher()

class AuthLogin(BaseModel):
    username: str
    password: SecretStr

async def authenticate(username: str, password: str) -> dict | None:
    rows = await fetch_readonly(
        "SELECT id, username, password FROM clinica_user.users WHERE username = $1",
        username,
    )
    user = rows[0] if rows else None
    if user is None:
        return None
    stored_hash = user["password"]

    try:
        await asyncio.to_thread(_ph.verify, stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return None

    return {"id": user["id"], "username": user["username"]}

@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Login the UI",
)
async def health(request: Request, payload: AuthLogin):
    user = await authenticate(payload.username, payload.password.get_secret_value())
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "ok", "access_token": str(user['id'])}