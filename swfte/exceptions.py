"""
Exceptions for the Swfte SDK.
"""


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
    """Raised when the API returns an error."""
    pass


class InvalidRequestError(SwfteError):
    """Raised when the request is invalid."""
    pass

