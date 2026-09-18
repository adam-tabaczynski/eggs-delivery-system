from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.interfaces.order_repository import OrderRepository
from src.models import Order, OrderStatus


class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)
        return order

    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def list_by_customer_id(self, customer_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at, Order.id)
        )
        return list(self.session.scalars(stmt).all())

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
        return order
