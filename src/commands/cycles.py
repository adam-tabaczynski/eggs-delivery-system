from datetime import datetime
from typing import Literal

from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import (
    CycleAlreadyCancelled,
    CycleAlreadyClosed,
    CycleCutoffNotInFuture,
    CycleDeliveryPassed,
    CycleNotFound,
    ProviderNotFound,
)
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
        if cutoff_at <= now:
            raise CycleCutoffNotInFuture()
        cycle = DeliveryCycle(
            provider_id=provider_id,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=max_eggs,
            status=DeliveryCycleStatus.OPEN,
        )
        uow.cycles.add(cycle)
        uow.commit()
        return DeliveryCycleRead.from_model(cycle, now=now, allocated_eggs=0)


def update_delivery_cycle(
    *,
    provider_id: int,
    cycle_id: int,
    status: Literal[DeliveryCycleStatus.CLOSED, DeliveryCycleStatus.CANCELLED],
    uow: UnitOfWork,
    clock: Clock,
) -> DeliveryCycleRead:
    now = clock.datetime_now()
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        if status is DeliveryCycleStatus.CANCELLED:
            cycle = _cancel_cycle(
                provider_id=provider_id, cycle_id=cycle_id, uow=uow, now=now
            )
        else:
            cycle = _close_cycle(
                provider_id=provider_id, cycle_id=cycle_id, uow=uow, now=now
            )
        uow.commit()
        return DeliveryCycleRead.from_model(
            cycle, now=now, allocated_eggs=uow.cycles.get_allocated_eggs(cycle.id)
        )


def _close_cycle(
    *, provider_id: int, cycle_id: int, uow: UnitOfWork, now: datetime
) -> DeliveryCycle:
    cycle = uow.cycles.get(cycle_id)
    if cycle is None or cycle.provider_id != provider_id:
        raise CycleNotFound()
    if not uow.cycles.close_if_open(cycle, now=now):
        # Re-read to tell why: a concurrent cancel may have landed after `get`.
        uow.cycles.refresh(cycle)
        if cycle.status is DeliveryCycleStatus.CANCELLED:
            raise CycleAlreadyCancelled()
        raise CycleAlreadyClosed()
    return cycle


def _cancel_cycle(
    *, provider_id: int, cycle_id: int, uow: UnitOfWork, now: datetime
) -> DeliveryCycle:
    cycle = uow.cycles.get_for_update(cycle_id)
    if cycle is None or cycle.provider_id != provider_id:
        raise CycleNotFound()
    if cycle.status is DeliveryCycleStatus.CANCELLED:
        raise CycleAlreadyCancelled()
    if now >= cycle.delivery_at:
        raise CycleDeliveryPassed()
    uow.cycles.update(cycle, status=DeliveryCycleStatus.CANCELLED)
    uow.orders.cancel_open_by_cycle_id(cycle.id)
    return cycle
