import pytest

from src.commands.cycles import create_delivery_cycle
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import NotFoundError
from src.models import DeliveryCycleStatus, Provider
from src.queries.cycles import list_cycles_for_provider
from tests.helpers import future_cycle_window, unique_email


def test_create_cycle_persists(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
    )

    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
    )

    assert created.status == DeliveryCycleStatus.OPEN
    assert len(listed) == 1
    assert listed[0].id == created.id
    assert listed[0].max_eggs == 48


def test_list_cycles_isolates_providers(provider_id: int) -> None:
    other_uow = SqlAlchemyUnitOfWork()
    with other_uow:
        other = Provider(name="Other Farm", email=unique_email(prefix="provider"))
        other_uow.providers.add(other)
        other_uow.commit()
        other_id = other.id

    cutoff_at, delivery_at = future_cycle_window()
    create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=12,
        uow=SqlAlchemyUnitOfWork(),
    )
    create_delivery_cycle(
        provider_id=other_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=24,
        uow=SqlAlchemyUnitOfWork(),
    )

    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
    )
    assert [cycle.max_eggs for cycle in listed] == [12]


def test_create_cycle_unknown_provider() -> None:
    cutoff_at, delivery_at = future_cycle_window()
    with pytest.raises(NotFoundError, match="Provider not found"):
        create_delivery_cycle(
            provider_id=0,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=48,
            uow=SqlAlchemyUnitOfWork(),
        )
