"""
Middleware log access: method, path, status_code, latency_ms.
"""

import time

from app.core.logging import get_logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = get_logger("app.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "client_ip": request.client.host if request.client else None,
                }
            },
        )
        response.headers["X-Process-Time-Ms"] = str(latency_ms)
        return response
