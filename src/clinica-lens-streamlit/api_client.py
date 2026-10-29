"""Thin HTTP client for the Clinica-lens FastAPI service.

The UI never talks to the database. It only calls the API with a Bearer token,
and the API derives the user (and tenant) from that token.
"""

import json
import os
from collections.abc import Iterator

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1").rstrip("/")

# Short connect/write timeouts, no read timeout (answers stream for several seconds).
_STREAM_TIMEOUT = httpx.Timeout(10.0, read=None)
_TIMEOUT = httpx.Timeout(15.0)


class AuthError(Exception):
    """Token missing, expired or rejected (HTTP 401/403)."""


class ApiError(Exception):
    """Any other API failure, with a message safe to show to the user."""


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _check(r: httpx.Response) -> None:
    if r.status_code in (401, 403):
        raise AuthError("Session expired or not authorized.")
    if r.status_code == 429:
        raise ApiError("Rate limit reached, please wait a moment.")
    if r.status_code >= 400:
        raise ApiError(f"Request failed ({r.status_code}).")


def login(user_name: str, password: str) -> str:
    """POST /auth/login -> access token. Raises AuthError on bad credentials."""
    try:
        r = httpx.post(
            f"{API_BASE}/auth/login",
            json={"user_name": user_name, "password": password},
            timeout=_TIMEOUT,
        )
    except httpx.HTTPError as e:
        raise ApiError("Cannot reach the API.") from e
    if r.status_code in (400, 401, 403):
        raise AuthError("Invalid user name or password.")
    _check(r)
    return r.json()["access_token"]


def list_conversations(token: str) -> list[dict]:
    """GET /conversations -> [{id, title, updated_at}]. Empty list if not available."""
    try:
        r = httpx.get(
            f"{API_BASE}/conversations", headers=_headers(token), timeout=_TIMEOUT
        )
    except httpx.HTTPError:
        return []
    if r.status_code in (401, 403):
        raise AuthError("Session expired or not authorized.")
    if r.status_code >= 400:
        return []
    return r.json()


def get_messages(token: str, conversation_id: str) -> list[dict]:
    """GET /conversations/{id} -> [{role, content}]. 404 means empty/new."""
    try:
        r = httpx.get(
            f"{API_BASE}/conversations/{conversation_id}",
            headers=_headers(token),
            timeout=_TIMEOUT,
        )
    except httpx.HTTPError as e:
        raise ApiError("Cannot reach the API.") from e
    if r.status_code == 404:
        return []
    _check(r)
    return r.json().get("messages", [])


def stream_answer(token: str, question: str, conversation_id: str) -> Iterator[dict]:
    """POST /query/stream and yield parsed SSE events.

    Events: {"token": str} | {"status": str} | {"done": true, ...} | {"error": str}
    """
    try:
        with httpx.stream(
            "POST",
            f"{API_BASE}/query/stream",
            headers=_headers(token),
            json={"question": question, "conversation_id": conversation_id},
            timeout=_STREAM_TIMEOUT,
        ) as r:
            if r.status_code >= 400:
                r.read()
                _check(r)
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    yield json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
    except httpx.HTTPError as e:
        raise ApiError("Connection to the API was interrupted.") from e
