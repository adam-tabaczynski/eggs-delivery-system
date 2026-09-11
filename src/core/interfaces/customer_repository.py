from typing import Protocol

from src.models import Customer


class CustomerRepository(Protocol):
    def get_by_email(self, email: str) -> Customer | None: ...

    def add(self, customer: Customer) -> Customer: ...
