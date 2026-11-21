from qdrant_client import models, QdrantClient
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings

settings = get_settings()

client: QdrantClient = None  # initialized in main.py, after settings are loaded
embedder: OpenAIEmbeddings = None  # initialized in main.py, after settings are loaded


def init_qdrant_client(url: str, api_key: str) -> None:
    """Initialize the Qdrant client with the endpoint and API key from settings."""
    global client
    client = QdrantClient(
        url=url,
        api_key=api_key,
        timeout=30,
    )


def init_embedder(api_key: str, model_name: str) -> None:
    """Initialize the OpenAI embeddings client with the API key and model name from settings."""
    global embedder
    embedder = OpenAIEmbeddings(openai_api_key=api_key, model=model_name)


COLLECTION = settings.VECTORDB_COLLECTION_NAME
DENSE, SPARSE = settings.VECTORDB_DENSE_NAME, settings.VECTORDB_SPARSE_NAME
PREFETCH_LIMIT = settings.VECTORDB_PREFETCH_LIMIT
TOP_K = settings.VECTORDB_TOP_K
BM25_OPTIONS = {
    "ascii_folding": True,
    "stopwords": {"custom": []},
    "stemmer": {"type": "none"},
}


def bm25(text: str) -> models.Document:
    """Text for the server-side BM25 model; Qdrant turns it into a sparse vector."""
    return models.Document(text=text, model="qdrant/bm25", options=BM25_OPTIONS)


# ── Search ───────────────────────────────────────────────────────────────────
def access_filter(
    access_groups: list[str], effective_after: str | None = None
) -> models.Filter:
    """Only chunks the user may read (and, optionally, documents that took effect on or after a date)."""
    must = [
        models.FieldCondition(
            key="access_group", match=models.MatchAny(any=access_groups)
        )
    ]
    if effective_after:
        must.append(
            models.FieldCondition(
                key="effective_date", range=models.DatetimeRange(gte=effective_after)
            )
        )
    return models.Filter(must=must)


def dense_search(query: str, k: int = 5, query_filter: models.Filter | None = None):
    return client.query_points(
        COLLECTION,
        query=embedder.embed_query(query),
        using=DENSE,
        query_filter=query_filter,
        limit=k,
    ).points


def bm25_search(query: str, k: int = 5, query_filter: models.Filter | None = None):
    return client.query_points(
        COLLECTION, query=bm25(query), using=SPARSE, query_filter=query_filter, limit=k
    ).points


def hybrid_search(
    query: str,
    access_groups: list[str],
    k: int = TOP_K,
    effective_after: str | None = None,
):
    """Dense and BM25 candidates (prefetch), fused by rank with RRF, in one Query API call.
    The top-level filter also applies inside both prefetches. RRF scores are ranks, not similarities."""
    return client.query_points(
        COLLECTION,
        prefetch=[
            models.Prefetch(
                query=embedder.embed_query(query), using=DENSE, limit=PREFETCH_LIMIT
            ),
            models.Prefetch(query=bm25(query), using=SPARSE, limit=PREFETCH_LIMIT),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=access_filter(access_groups, effective_after),
        limit=k,
    ).points
