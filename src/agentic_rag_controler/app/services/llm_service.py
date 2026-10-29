from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool

from app.core.logging import get_logger

logger = get_logger("app.services.rag_service")


class LLMService:
    def __init__(self, model: str, api_key: str, tools: list[BaseTool]):
        self._model = init_chat_model(model=model, api_key=api_key)
        self.tools_by_name = {t.name: t for t in tools}
        self._model_with_tools = self._model.bind_tools(tools)

    async def ainvoke(self, message: str):
        return await self._model_with_tools.ainvoke(message)

    def get_model(self):
        return self._model
