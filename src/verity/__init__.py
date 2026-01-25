"""Verity Python SDK - Medicare coverage policies and prior authorization."""

from .client import VerityClient
from .exceptions import (
    VerityError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
)

__version__ = "1.0.0"
__all__ = [
    "VerityClient",
    "VerityError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
]
