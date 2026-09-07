from app.core.config import get_settings
from app.schemas.health_schemas import HealthResponse, LivenessResponse
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Quick health check (legacy compatibility)",
)
async def health():
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.APP_VERSION)


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe - checks if the process is alive (does not check models)",
)
async def liveness():
    return LivenessResponse(status="alive")
