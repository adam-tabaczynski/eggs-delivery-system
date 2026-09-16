from datetime import UTC, datetime

from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import ProviderNotFound
from src.schemas import DeliveryCycleRead


def list_cycles_for_provider(
    *,
    provider_id: int,
    uow: UnitOfWork,
) -> list[DeliveryCycleRead]:
    now = datetime.now(UTC)
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        cycles = uow.cycles.list_by_provider_id(provider_id)
        return [DeliveryCycleRead.from_model(cycle, now=now) for cycle in cycles]
