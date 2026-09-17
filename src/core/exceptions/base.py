"""Base application exception types."""


class DomainError(Exception):
    """Raised when a business rule is violated."""

    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class OperationalError(Exception):
    """Unexpected database or session failure."""

    code: str = "internal_error"

    def __init__(self, message: str = "Database operation failed") -> None:
        self.message = message
        super().__init__(message)
