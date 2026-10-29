from langchain.messages import HumanMessage
from app.services.llm_service import LLMService
from app.agents.graph import build_graph


class GraphService:
    def __init__(self, llm: LLMService):
        self._graph = build_graph(llm_client=llm)
        self._config = {"recursion_limit": 3}

    async def invoke(self, query):
        result = await self._graph.ainvoke(
            input={"messages": [HumanMessage(query)]}, config=self._config
        )
        return result["messages"][-1].text
