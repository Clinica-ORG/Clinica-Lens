from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    stage: str | None = None
    request_id: str


class LivenessResponse(BaseModel):
    status: str = Field(examples=["alive"])


class ReadinessResponse(BaseModel):
    status: str = Field(examples=["ready", "not_ready"])
    checks: dict[str, str] | None = None


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    version: str
