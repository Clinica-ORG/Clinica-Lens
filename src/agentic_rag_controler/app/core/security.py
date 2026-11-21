from datetime import datetime, timedelta, timezone
from typing import Annotated
import asyncio
import jwt
from jwt.exceptions import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.db.database import fetch_readonly
from app.schemas.auth_schemas import User


_ph = PasswordHasher()
DUMMY_HASH = _ph.hash("dummy password")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def create_access_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    expires = timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    claims = {
        "sub": user.user_id,
        "name": user.name,
        "exp": datetime.now(timezone.utc) + expires,
    }
    token = jwt.encode(
        claims, settings.JWT_SECRET.get_secret_value(), algorithm=settings.JWT_ALGORITHM
    )
    return token, int(expires.total_seconds())


def decode_access_token(token: str) -> User:
    """Verify signature and expiry; raises InvalidTokenError otherwise."""
    settings = get_settings()
    claims = jwt.decode(
        token,
        settings.JWT_SECRET.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )
    return User(user_id=claims["sub"], name=claims.get("name", claims["sub"]))


async def authenticate(user_name: str, password: str) -> dict | None:
    rows = await fetch_readonly(
        "SELECT id, user_name, hashed_password, user_group FROM clinical_conversations.users WHERE user_name = $1",
        user_name,
    )
    user = rows[0] if rows else None
    if user is None:
        stored_hash = DUMMY_HASH  # prevent timing attacks
    else:
        stored_hash = user["hashed_password"]

    try:
        await asyncio.to_thread(_ph.verify, stored_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return None

    print(user)

    return User(
        user_id=str(user["id"]), name=user["user_name"], group=user["user_group"]
    )


async def current_user(
    request: Request, token: Annotated[str | None, Depends(oauth2_scheme)]
) -> User:
    unauthorized = HTTPException(
        401, "Missing, invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
    )
    if not token:
        raise unauthorized
    try:
        user = decode_access_token(token)
    except (InvalidTokenError, KeyError):
        raise unauthorized from None

    rows = await fetch_readonly(
        "SELECT id, user_name, user_group FROM clinical_conversations.users WHERE user_name = $1",
        user.name,
    )
    user = rows[0] if rows else None
    if user is None:  # account deleted since login
        raise unauthorized
    return User(
        user_id=str(user["id"]), name=user["user_name"], group=user["user_group"]
    )


CurrentUser = Annotated[User, Depends(current_user)]
