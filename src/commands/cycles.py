from datetime import datetime

from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import CycleAlreadyClosed, CycleNotFound, ProviderNotFound
from src.models import DeliveryCycle, DeliveryCycleStatus
from src.schemas import DeliveryCycleRead


def create_delivery_cycle(
    *,
    provider_id: int,
    delivery_at: datetime,
    cutoff_at: datetime,
    max_eggs: int,
    uow: UnitOfWork,
    clock: Clock,
) -> DeliveryCycleRead:
    now = clock.datetime_now()
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        cycle = DeliveryCycle(
            provider_id=provider_id,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=max_eggs,
            status=DeliveryCycleStatus.OPEN,
        )
        uow.cycles.add(cycle)
        uow.commit()
        return DeliveryCycleRead.from_model(cycle, now=now)


def update_delivery_cycle(
    *,
    provider_id: int,
    cycle_id: int,
    uow: UnitOfWork,
    clock: Clock,
) -> DeliveryCycleRead:
    now = clock.datetime_now()
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        cycle = uow.cycles.get(cycle_id)
        if cycle is None or cycle.provider_id != provider_id:
            raise CycleNotFound()
        if cycle.effective_status(now) is DeliveryCycleStatus.CLOSED:
            raise CycleAlreadyClosed()
        cycle.status = DeliveryCycleStatus.CLOSED
        uow.commit()
        return DeliveryCycleRead.from_model(cycle, now=now)
