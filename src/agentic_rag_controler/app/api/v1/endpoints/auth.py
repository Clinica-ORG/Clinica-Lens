from pydantic import BaseModel, SecretStr
from fastapi import APIRouter, Request, HTTPException
import asyncio
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.schemas.auth_schemas import AuthResponse
from app.db.database import fetch_readonly

router = APIRouter()

_ph = PasswordHasher()


class AuthLogin(BaseModel):
    user_name: str
    password: SecretStr


async def authenticate(user_name: str, password: str) -> dict | None:
    rows = await fetch_readonly(
        "SELECT id, user_name, hashed_password, role FROM clinical_conversations.users WHERE user_name = $1",
        user_name,
    )
    user = rows[0] if rows else None
    if user is None:
        return None
    stored_hash = user["hashed_password"]

    try:
        await asyncio.to_thread(_ph.verify, stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return None

    return {"id": user["id"], "user_name": user["user_name"], "role": user["role"]}


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Login the UI",
)
async def login(request: Request, payload: AuthLogin):
    user = await authenticate(payload.user_name, payload.password.get_secret_value())
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "ok", "access_token": str(user["id"]), "role": user["role"]}
