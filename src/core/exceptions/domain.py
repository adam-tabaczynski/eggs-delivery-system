"""HTTP-shaped domain error buckets."""

from src.core.exceptions.base import DomainError


class ConflictError(DomainError):
    """Raised when a write would violate uniqueness or occupancy."""

    code = "conflict"


class NotFoundError(DomainError):
    """Raised when a referenced entity does not exist."""

    code = "not_found"


class UnprocessableError(DomainError):
    """Raised when well-formed input breaks a rule that depends on current state."""

    code = "unprocessable"
