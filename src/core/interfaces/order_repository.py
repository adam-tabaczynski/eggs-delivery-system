from typing import Protocol

from src.models import Order, OrderStatus


class OrderRepository(Protocol):
    def add(self, order: Order) -> Order: ...

    def get(self, order_id: int) -> Order | None: ...

    def list_by_customer_id(self, customer_id: int) -> list[Order]: ...

    def get_open_order_for_customer(
        self, *, customer_id: int, cycle_id: int
    ) -> Order | None: ...

    def sum_open_quantity(
        self, cycle_id: int, *, exclude_order_id: int | None = None
    ) -> int: ...

    def update(
        self,
        order: Order,
        *,
        quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Order: ...
