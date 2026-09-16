"""Concrete business-rule errors."""

from src.core.exceptions import ConflictError, NotFoundError


class EmailAlreadyRegistered(ConflictError):
    code = "email_already_registered"

    def __init__(self, message: str = "Email already registered") -> None:
        super().__init__(message)


class ProviderNotFound(NotFoundError):
    code = "provider_not_found"

    def __init__(self, message: str = "Provider not found") -> None:
        super().__init__(message)
