from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import ToolCallLimitMiddleware, ToolRetryMiddleware

from app.services.prompts import SYSTEM_PROMPT


class AgentMiddlewareService:
    @staticmethod
    def create_middleware(max_retries=2, run_limit=8) -> list:
        if max_retries <= 0:
            raise ValueError("max_retries must be greater than 0")
        if run_limit <= 0:
            raise ValueError("run_limit must be greater than 0")
        list_middleware = [
            ToolRetryMiddleware(max_retries=max_retries),
            ToolCallLimitMiddleware(run_limit=run_limit),
        ]
        return list_middleware


class AgentService:
    def __init__(self, model, tools, middleware, checkpointer=None):
        self.agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=middleware,
            checkpointer=checkpointer,
        )

    async def ainvoke(self, request: str, config: dict):
        rep = await self.agent.ainvoke(
            input={"messages": [HumanMessage(request)]}, config=config
        )
        return rep
