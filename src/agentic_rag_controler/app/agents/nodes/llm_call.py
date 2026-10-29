from langchain.messages import SystemMessage
from app.agents.state import AgentState
from app.services import SYSTEM_PROMPT


def make_llm_call_node(llm_client):
    async def llm_call_node(state: AgentState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        response = await llm_client.ainvoke(messages)
        return {"messages": [response]}

    return llm_call_node
