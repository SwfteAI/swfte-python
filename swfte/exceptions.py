"""
Exceptions for the Swfte SDK.
"""

from typing import Any, Optional


class SwfteError(Exception):
    """Base exception for Swfte SDK."""
    pass


class AuthenticationError(SwfteError):
    """Raised when authentication fails."""
    pass


class RateLimitError(SwfteError):
    """Raised when rate limit is exceeded."""
    pass


class APIError(SwfteError):
    """Raised when the API returns an error.

    ``status_code`` and ``body`` (the parsed JSON, or the raw text) are set
    when the error came from an HTTP response.
    """

    def __init__(self, message: str = "", status_code: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class InvalidRequestError(SwfteError):
    """Raised when the request is invalid."""
    pass


class WorkflowExecutionError(SwfteError, RuntimeError):
    """A workflow run reached a terminal status other than success
    (FAILED, TIMEOUT, CANCELLED/CANCELED). ``execution`` holds the final status.

    Also a ``RuntimeError``, which is what ``wait_for_completion`` raised before.
    """

    def __init__(self, message: str, execution_id: str, status: str, execution: Any = None):
        super().__init__(message)
        self.execution_id = execution_id
        self.status = status
        self.execution = execution


class WorkflowTimeoutError(SwfteError, TimeoutError):
    """Polling gave up before the workflow run finished. The run is NOT
    cancelled; poll ``execution_id`` again to follow it.

    Also a ``TimeoutError``, which is what ``wait_for_completion`` raised before.
    """

    def __init__(self, message: str, execution_id: str, last_status: Any = None):
        super().__init__(message)
        self.execution_id = execution_id
        self.last_status = last_status
