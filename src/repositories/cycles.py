from datetime import datetime
from typing import Any

from sqlalchemy import ScalarSelect, func, select, update
from sqlalchemy.orm import Session

from src.core.interfaces.cycle_repository import (
    CycleWithAllocatedEggs,
    DeliveryCycleRepository,
)
from src.models import DeliveryCycle, DeliveryCycleStatus, Order, OrderStatus


class SqlAlchemyDeliveryCycleRepository(DeliveryCycleRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, cycle: DeliveryCycle) -> DeliveryCycle:
        self.session.add(cycle)
        self.session.flush()
        self.session.refresh(cycle)
        return cycle

    def get(self, cycle_id: int) -> DeliveryCycle | None:
        return self.session.get(DeliveryCycle, cycle_id)

    def get_for_update(self, cycle_id: int) -> DeliveryCycle | None:
        stmt = (
            select(DeliveryCycle).where(DeliveryCycle.id == cycle_id).with_for_update()
        )
        return self.session.scalars(stmt).first()

    def close_if_open(self, cycle: DeliveryCycle, *, now: datetime) -> bool:
        stmt = (
            update(DeliveryCycle)
            .where(
                DeliveryCycle.id == cycle.id,
                DeliveryCycle.status == DeliveryCycleStatus.OPEN,
                DeliveryCycle.cutoff_at > now,
            )
            .values(status=DeliveryCycleStatus.CLOSED)
            .returning(DeliveryCycle.id)
        )
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def get_allocated_eggs(
        self, cycle_id: int, *, exclude_order_id: int | None = None
    ) -> int:
        stmt = select(self._allocated_eggs(exclude_order_id=exclude_order_id)).where(
            DeliveryCycle.id == cycle_id
        )
        return self.session.scalars(stmt).one()

    def list_all_with_allocated_eggs(self) -> list[CycleWithAllocatedEggs]:
        stmt = select(DeliveryCycle, self._allocated_eggs()).order_by(
            DeliveryCycle.delivery_at, DeliveryCycle.id
        )
        return [
            CycleWithAllocatedEggs(cycle=cycle, allocated_eggs=allocated_eggs)
            for cycle, allocated_eggs in self.session.execute(stmt)
        ]

    def list_with_allocated_eggs_by_provider_id(
        self, provider_id: int
    ) -> list[CycleWithAllocatedEggs]:
        stmt = (
            select(DeliveryCycle, self._allocated_eggs())
            .where(DeliveryCycle.provider_id == provider_id)
            .order_by(DeliveryCycle.delivery_at, DeliveryCycle.id)
        )
        return [
            CycleWithAllocatedEggs(cycle=cycle, allocated_eggs=allocated_eggs)
            for cycle, allocated_eggs in self.session.execute(stmt)
        ]

    @staticmethod
    def _allocated_eggs(*, exclude_order_id: int | None = None) -> ScalarSelect[Any]:
        """Sum of `open` orders' quantity, correlated to the outer query's cycle."""
        stmt = (
            select(func.coalesce(func.sum(Order.quantity), 0))
            .where(
                Order.cycle_id == DeliveryCycle.id,
                Order.status == OrderStatus.OPEN,
            )
            .correlate(DeliveryCycle)
        )
        if exclude_order_id is not None:
            stmt = stmt.where(Order.id != exclude_order_id)
        return stmt.scalar_subquery()
