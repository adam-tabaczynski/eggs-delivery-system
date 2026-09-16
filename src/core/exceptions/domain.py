"""HTTP-shaped domain error buckets."""

from src.core.exceptions.base import DomainError


class ConflictError(DomainError):
    """Raised when a write would violate uniqueness or occupancy."""

    code = "conflict"


class NotFoundError(DomainError):
    """Raised when a referenced entity does not exist."""

    code = "not_found"
