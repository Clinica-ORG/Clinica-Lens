"""
Custom pipeline exception classes to ensure consistent JSON responses from the error handler
and contextual logging (identifying which stage failed).
"""


class PipelineError(Exception):
    """Base class for errors in extraction pipeline."""

    error_code: str = "PIPELINE_ERROR"
    status_code: int = 500

    def __init__(self, message: str, stage: str | None = None):
        self.message = message
        self.stage = stage
        super().__init__(message)


class InferenceTimeoutError(PipelineError):
    error_code = "INFERENCE_TIMEOUT"
    status_code = 504


class ServiceBusyError(PipelineError):
    """Queue is full - refuse request."""

    error_code = "SERVICE_BUSY"
    status_code = 503
