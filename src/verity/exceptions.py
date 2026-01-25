"""Exceptions for Verity SDK."""

from typing import Any, Dict, Optional


class VerityError(Exception):
    """Base exception for all Verity SDK errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.hint = hint
        self.details = details or {}


class AuthenticationError(VerityError):
    """Raised when API key is missing or invalid."""

    pass


class ValidationError(VerityError):
    """Raised when request parameters are invalid."""

    pass


class NotFoundError(VerityError):
    """Raised when a resource is not found."""

    pass


class RateLimitError(VerityError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.limit = limit
        self.remaining = remaining
        self.reset = reset
