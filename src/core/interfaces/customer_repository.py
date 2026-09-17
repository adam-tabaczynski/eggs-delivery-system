from typing import Protocol

from src.models import Customer


class CustomerRepository(Protocol):
    def get(self, customer_id: int) -> Customer | None: ...

    def get_by_email(self, email: str) -> Customer | None: ...

    def add(self, customer: Customer) -> Customer: ...
