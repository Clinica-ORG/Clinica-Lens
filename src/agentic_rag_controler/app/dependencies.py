"""
Dependency injection: FastAPI Depends() takes service instance (loaded in lifespan function)
from app.state, instead of creating new one for every request.
"""

from fastapi import Request

from app.services import GraphService, AgentService


def get_agent_graph(request: Request) -> GraphService:
    return request.app.state.graph


def get_agent(request: Request) -> AgentService:
    return request.app.state.agent


def get_inference_executor(request: Request):
    return request.app.state.inference_executor
