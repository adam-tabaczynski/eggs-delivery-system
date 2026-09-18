from typing import Protocol

from src.models import Order, OrderStatus


class OrderRepository(Protocol):
    def add(self, order: Order) -> Order: ...

    def get(self, order_id: int) -> Order | None: ...

    def update(
        self,
        order: Order,
        *,
        quantity: int | None = None,
        status: OrderStatus | None = None,
    ) -> Order: ...
