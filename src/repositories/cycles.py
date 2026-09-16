from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.interfaces.cycle_repository import DeliveryCycleRepository
from src.models import DeliveryCycle


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

    def list_by_provider_id(self, provider_id: int) -> list[DeliveryCycle]:
        stmt = (
            select(DeliveryCycle)
            .where(DeliveryCycle.provider_id == provider_id)
            .order_by(DeliveryCycle.delivery_at, DeliveryCycle.id)
        )
        return list(self.session.scalars(stmt).all())
