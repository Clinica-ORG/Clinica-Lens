from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from app.agents.state import AgentState
from app.agents.nodes import make_llm_call_node, make_tool_call_node, should_continue


def build_graph(llm_client, checkpointer=None):
    g = StateGraph(AgentState)
    # nodes
    g.add_node(node="llm_call", action=make_llm_call_node(llm_client))
    g.add_node(
        node="tool_node",
        action=make_tool_call_node(),
        retry_policy=RetryPolicy(max_attempts=3),
    )

    # edges
    g.add_edge(START, "llm_call")
    g.add_conditional_edges(
        source="llm_call", path=should_continue, path_map=["tool_node", END]
    )
    g.add_edge("tool_node", "llm_call")

    return g.compile(checkpointer=checkpointer)
