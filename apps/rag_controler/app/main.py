from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.routers import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import Base, engine
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import AccessLogMiddleware
from app.middleware.request_tracing import RequestTracingMiddleware
from app.services.rag_service import RAGService

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init db
    Base.metadata.create_all(bind=engine)

    app.state.rag_service = RAGService()

    # app.state.inference_limiter = anyio.CapacityLimiter(settings.INFERENCE_MAX_WORKERS)
    app.state.inference_executor = ThreadPoolExecutor(
        max_workers=settings.INFERENCE_MAX_WORKERS, thread_name_prefix="inference"
    )

    app.state.pipeline_in_flight = 0

    logger.info("rag-service ready")
    yield
    logger.info("Shutting down rag-service...")
    app.state.inference_executor.shutdown(wait=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=("API queries LLM"),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # --- Rate limiting ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Middleware ---
    # The order of add_middleware is reversed relative to execution order (the last added
    # middleware runs first). MaxUploadSize + TrustedHost + CORS should run earliest
    # (blocking bad requests before wasting compute), while RequestTracing runs early so
    # all subsequent logs and middlewares have access to request_id.
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestTracingMiddleware)

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # --- Metrics ---
    Instrumentator().instrument(app).expose(
        app, endpoint="/metrics", include_in_schema=False
    )

    return app


app = create_app()


# uvicorn app.main:app --reload --port 8000
