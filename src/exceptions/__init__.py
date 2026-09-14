"""Domain / business-rule errors."""


class DomainError(Exception):
    """Raised when a business rule is violated."""


class ConflictError(DomainError):
    """Raised when a write would violate uniqueness or occupancy."""


class NotFoundError(DomainError):
    """Raised when a referenced entity does not exist."""
