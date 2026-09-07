from fastapi import APIRouter

from app.api.v1.endpoints import query, health, patients_admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(patients_admin.router, tags=["Patients"])
api_router.include_router(query.router, tags=["Query RAG"])