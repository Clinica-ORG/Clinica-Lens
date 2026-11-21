from typing import Any
import logging
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.db.vector_database import hybrid_search

log = logging.getLogger("agent.tools")


@tool
def retrieve(
    query: str, config: RunnableConfig, k: int = 8, effective_after: str | None = None
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from the vector database using hybrid search (dense + BM25).

    Args:
        query: The query string to search for.
        k: Number of top results to return.
        effective_after: Optional ISO date; only return chunks from documents effective on or after it.
    """
    access_groups = config["configurable"]["access_groups"]
    results = hybrid_search(query, access_groups, k=k, effective_after=effective_after)
    return [
        {
            "text": p["section_path"] + "\n" + p["text"],
            "source": p.get("source", ""),
            "file_location": p.get("s3_key", ""),
        }
        for p in (point.payload for point in results)
    ]


def get_retrieval_tools():
    """Return the tools that can be used to retrieve information from the vector database."""
    return [retrieve]
