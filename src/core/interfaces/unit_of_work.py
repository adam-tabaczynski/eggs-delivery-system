from types import TracebackType
from typing import Protocol, Self

from src.core.interfaces.customer_repository import CustomerRepository
from src.core.interfaces.cycle_repository import DeliveryCycleRepository
from src.core.interfaces.order_repository import OrderRepository
from src.core.interfaces.provider_repository import ProviderRepository


class UnitOfWork(Protocol):
    """Transactional boundary; the only persistence entry point for use-cases."""

    customers: CustomerRepository
    providers: ProviderRepository
    cycles: DeliveryCycleRepository
    orders: OrderRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
