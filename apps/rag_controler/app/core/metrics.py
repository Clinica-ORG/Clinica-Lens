"""
Prometheus metrics for the RAG pipeline.
"""

from prometheus_client import Counter, Gauge, Histogram

PIPELINE_STAGE_DURATION = Histogram(
    "rag_pipeline_stage_duration_seconds",
    "Duration of each RAG pipeline stage",
    ["stage"],  # list of stage names: "extraction", "retrieval", "answer_generation"
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60),
)

PIPELINE_ERRORS = Counter(
    "rag_pipeline_errors_total",
    "Pipeline errors by error_code and stage",
    ["error_code", "stage"],
)

IN_FLIGHT_REQUESTS = Gauge(
    "rag_pipeline_in_flight_requests",
    "Requests currently in the inference pipeline",
)
