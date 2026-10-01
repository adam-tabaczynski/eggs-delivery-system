from src.core.clock import Clock
from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import CustomerNotFound, ProviderNotFound
from src.schemas import DeliveryCycleRead, ProviderDeliveryCycleRead


def list_cycles_for_provider(
    *,
    provider_id: int,
    uow: UnitOfWork,
    clock: Clock,
) -> list[ProviderDeliveryCycleRead]:
    now = clock.datetime_now()
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        cycles_with_allocated_eggs = uow.cycles.list_with_allocated_eggs_by_provider_id(
            provider_id
        )
        return [
            ProviderDeliveryCycleRead.from_model_with_allocated_eggs(
                row.cycle, now=now, allocated_eggs=row.allocated_eggs
            )
            for row in cycles_with_allocated_eggs
        ]


def list_cycles_for_customer(
    *,
    customer_id: int,
    uow: UnitOfWork,
    clock: Clock,
) -> list[DeliveryCycleRead]:
    now = clock.datetime_now()
    with uow:
        if uow.customers.get(customer_id) is None:
            raise CustomerNotFound()
        cycles = uow.cycles.list_all()
        return [DeliveryCycleRead.from_model(cycle, now=now) for cycle in cycles]
