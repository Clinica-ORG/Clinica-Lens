from typing import Annotated
from pydantic import BaseModel, SecretStr
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
import asyncio
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.schemas.auth_schemas import AuthResponse, Token
from app.db.database import fetch_readonly
from app.core.security import authenticate, create_access_token

router = APIRouter()

_ph = PasswordHasher()


class AuthLogin(BaseModel):
    user_name: str
    password: SecretStr


@router.post(
    "/auth/login",
    response_model=Token,
    summary="Login the UI",
)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, expires_in = create_access_token(user)
    return Token(access_token=token, expires_in=expires_in)
