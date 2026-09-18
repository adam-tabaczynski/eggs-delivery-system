from types import TracebackType
from typing import Self

from src.core.clock import Clock
from src.core.interfaces.customer_repository import CustomerRepository
from src.core.interfaces.cycle_repository import DeliveryCycleRepository
from src.core.interfaces.order_repository import OrderRepository
from src.core.interfaces.provider_repository import ProviderRepository
from src.core.interfaces.unit_of_work import UnitOfWork
from src.models import (
    Customer,
    DeliveryCycle,
    DeliveryCycleStatus,
    Order,
    OrderStatus,
    Provider,
)


class FakeCustomerRepository(CustomerRepository):
    def __init__(self) -> None:
        self._by_id: dict[int, Customer] = {}
        self._by_email: dict[str, Customer] = {}
        self._next_id = 1

    def get(self, customer_id: int) -> Customer | None:
        return self._by_id.get(customer_id)

    def get_by_email(self, email: str) -> Customer | None:
        return self._by_email.get(email)

    def add(self, customer: Customer) -> Customer:
        now = Clock().datetime_now()
        customer.id = self._next_id
        self._next_id += 1
        customer.created_at = now
        customer.updated_at = now
        self._by_id[customer.id] = customer
        self._by_email[customer.email] = customer
        return customer


class FakeProviderRepository(ProviderRepository):
    def __init__(self) -> None:
        self._by_id: dict[int, Provider] = {}
        self._next_id = 1

    def get(self, provider_id: int) -> Provider | None:
        return self._by_id.get(provider_id)

    def add(self, provider: Provider) -> Provider:
        now = Clock().datetime_now()
        provider.id = self._next_id
        self._next_id += 1
        provider.created_at = now
        provider.updated_at = now
        self._by_id[provider.id] = provider
        return provider


class FakeDeliveryCycleRepository(DeliveryCycleRepository):
    def __init__(self) -> None:
        self._by_id: dict[int, DeliveryCycle] = {}
        self._next_id = 1

    def add(self, cycle: DeliveryCycle) -> DeliveryCycle:
        now = Clock().datetime_now()
        cycle.id = self._next_id
        self._next_id += 1
        if getattr(cycle, "status", None) is None:
            cycle.status = DeliveryCycleStatus.OPEN
        cycle.created_at = now
        cycle.updated_at = now
        self._by_id[cycle.id] = cycle
        return cycle

    def get(self, cycle_id: int) -> DeliveryCycle | None:
        return self._by_id.get(cycle_id)

    def list_all(self) -> list[DeliveryCycle]:
        return sorted(
            self._by_id.values(), key=lambda cycle: (cycle.delivery_at, cycle.id)
        )

    def list_by_provider_id(self, provider_id: int) -> list[DeliveryCycle]:
        cycles = [
            cycle for cycle in self._by_id.values() if cycle.provider_id == provider_id
        ]
        return sorted(cycles, key=lambda cycle: (cycle.delivery_at, cycle.id))


class FakeOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._by_id: dict[int, Order] = {}
        self._next_id = 1

    def add(self, order: Order) -> Order:
        now = Clock().datetime_now()
        order.id = self._next_id
        self._next_id += 1
        if getattr(order, "status", None) is None:
            order.status = OrderStatus.OPEN
        order.created_at = now
        order.updated_at = now
        self._by_id[order.id] = order
        return order

    def get(self, order_id: int) -> Order | None:
        return self._by_id.get(order_id)

    def list_by_customer_id(self, customer_id: int) -> list[Order]:
        orders = [
            order for order in self._by_id.values() if order.customer_id == customer_id
        ]
        return sorted(orders, key=lambda order: (order.created_at, order.id))

    def sum_open_quantity(self, cycle_id: int) -> int:
        return sum(
            order.quantity
            for order in self._by_id.values()
            if order.cycle_id == cycle_id and order.status is OrderStatus.OPEN
        )

    def update(
        self,
        order: Order,
        *,
        quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Order:
        if quantity is not None:
            order.quantity = quantity
        if status is not None:
            order.status = status
        order.updated_at = Clock().datetime_now()
        return order


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.customers = FakeCustomerRepository()
        self.providers = FakeProviderRepository()
        self.cycles = FakeDeliveryCycleRepository()
        self.orders = FakeOrderRepository()
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
