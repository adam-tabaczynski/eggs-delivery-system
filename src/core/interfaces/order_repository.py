from typing import Protocol

from src.models import Order, OrderStatus


class OrderRepository(Protocol):
    def add(self, order: Order) -> Order: ...

    def get(self, order_id: int) -> Order | None: ...

    def refresh(self, order: Order) -> Order: ...

    def list_by_customer_id(
        self, customer_id: int, *, status: OrderStatus | None = None
    ) -> list[Order]: ...

    def list_by_cycle_id(
        self, cycle_id: int, *, status: OrderStatus | None = None
    ) -> list[Order]: ...

    def get_open_order_for_customer(
        self, *, customer_id: int, cycle_id: int
    ) -> Order | None: ...

    def update(
        self,
        order: Order,
        *,
        quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Order: ...
