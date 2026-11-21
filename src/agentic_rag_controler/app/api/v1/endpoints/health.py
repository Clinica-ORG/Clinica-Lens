import logging
from fastapi import APIRouter, HTTPException

from app.dependencies import Store
from app.core.config import get_settings
from app.schemas.health_schemas import (
    HealthResponse,
    ReadinessResponse,
    LivenessResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Quick health check (legacy compatibility)",
)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.APP_VERSION)


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe - checks if the process is alive (does not check models)",
)
async def liveness() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(store: Store) -> ReadinessResponse:
    try:
        await store.conn.execute("SELECT 1")  # the database answers
    except Exception as exc:
        logger.error("readiness check failed: %r", exc)
        raise HTTPException(503, "storage not ready")  # details stay in the log
    return ReadinessResponse(status="ready", checks={"store": "ok"})
