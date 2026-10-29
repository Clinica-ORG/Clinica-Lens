from typing import Literal
from langchain.messages import ToolMessage
from langgraph.types import Send
from langgraph.graph import END

from app.tools import TOOLS_BY_NAME
from app.agents.state import AgentState


def make_tool_call_node():
    async def tool_call_node(tool_call: dict) -> dict:
        observation = await TOOLS_BY_NAME[tool_call["name"]].ainvoke(tool_call["args"])
        return {
            "messages": [
                ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
            ]
        }

    return tool_call_node


def should_continue(state: AgentState) -> list[Send] | Literal["__end__"]:
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    return [Send("tool_node", call) for call in tool_calls]
