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


class CustomerNotFound(NotFoundError):
    code = "customer_not_found"

    def __init__(self, message: str = "Customer not found") -> None:
        super().__init__(message)


class CycleNotFound(NotFoundError):
    code = "cycle_not_found"

    def __init__(self, message: str = "Cycle not found") -> None:
        super().__init__(message)


class CycleAlreadyClosed(ConflictError):
    code = "cycle_already_closed"

    def __init__(self, message: str = "Cycle is already closed") -> None:
        super().__init__(message)


class OrderNotFound(NotFoundError):
    code = "order_not_found"

    def __init__(self, message: str = "Order not found") -> None:
        super().__init__(message)


class OrderAlreadyCancelled(ConflictError):
    code = "order_already_cancelled"

    def __init__(self, message: str = "Order is already cancelled") -> None:
        super().__init__(message)
