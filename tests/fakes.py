from datetime import UTC, datetime
from types import TracebackType
from typing import Self

from src.core.interfaces.customer_repository import CustomerRepository
from src.core.interfaces.unit_of_work import UnitOfWork
from src.models import Customer


class FakeCustomerRepository(CustomerRepository):
    def __init__(self) -> None:
        self._by_email: dict[str, Customer] = {}
        self._next_id = 1

    def get_by_email(self, email: str) -> Customer | None:
        return self._by_email.get(email)

    def add(self, customer: Customer) -> Customer:
        now = datetime.now(UTC)
        customer.id = self._next_id
        self._next_id += 1
        customer.created_at = now
        customer.updated_at = now
        self._by_email[customer.email] = customer
        return customer


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.customers = FakeCustomerRepository()
        self.committed = False

    def __enter__(self) -> Self:
        self.committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass
