from datetime import datetime

from sqlalchemy.exc import IntegrityError

from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import NotFoundError
from src.models import DeliveryCycle, DeliveryCycleStatus
from src.schemas import DeliveryCycleRead


def create_delivery_cycle(
    *,
    provider_id: int,
    delivery_at: datetime,
    cutoff_at: datetime,
    max_eggs: int,
    uow: UnitOfWork,
) -> DeliveryCycleRead:
    try:
        with uow:
            if uow.providers.get(provider_id) is None:
                raise NotFoundError("Provider not found")
            cycle = DeliveryCycle(
                provider_id=provider_id,
                delivery_at=delivery_at,
                cutoff_at=cutoff_at,
                max_eggs=max_eggs,
                status=DeliveryCycleStatus.OPEN,
            )
            uow.cycles.add(cycle)
            uow.commit()
            return DeliveryCycleRead.model_validate(cycle)
    except IntegrityError as exc:
        raise NotFoundError("Provider not found") from exc
