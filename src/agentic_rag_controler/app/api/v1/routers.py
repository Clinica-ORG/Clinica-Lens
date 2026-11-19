from fastapi import APIRouter

from app.api.v1.endpoints import health, query, auth, runs, threads

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(query.router, tags=["Agentic RAG"])
api_router.include_router(runs.router, tags=["Runs"])
api_router.include_router(threads.router, tags=["Threads"])
