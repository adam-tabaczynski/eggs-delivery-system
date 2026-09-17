import pytest

from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.core.exceptions import ConflictError, NotFoundError
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import DeliveryCycleStatus, Provider
from src.queries.cycles import list_cycles_for_provider
from tests.helpers import future_cycle_window, past_cycle_window, unique_email


def test_create_cycle_persists(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
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
        clock=Clock(),
    )
    create_delivery_cycle(
        provider_id=other_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=24,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
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
            clock=Clock(),
        )


def test_update_cycle_persists(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    updated = update_delivery_cycle(
        provider_id=provider_id,
        cycle_id=created.id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    assert updated.status == DeliveryCycleStatus.CLOSED
    assert listed[0].status == DeliveryCycleStatus.CLOSED


def test_update_cycle_unknown_cycle(provider_id: int) -> None:
    with pytest.raises(NotFoundError, match="Cycle not found"):
        update_delivery_cycle(
            provider_id=provider_id,
            cycle_id=0,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )


def test_update_cycle_already_closed(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    update_delivery_cycle(
        provider_id=provider_id,
        cycle_id=created.id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with pytest.raises(ConflictError, match="Cycle is already closed"):
        update_delivery_cycle(
            provider_id=provider_id,
            cycle_id=created.id,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )


def test_list_treats_past_cutoff_as_closed(provider_id: int) -> None:
    cutoff_at, delivery_at = past_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_cycles_for_provider(
        provider_id=provider_id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    assert created.status == DeliveryCycleStatus.CLOSED
    assert listed[0].status == DeliveryCycleStatus.CLOSED
    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.cycles.get(created.id)
        assert stored is not None
        assert stored.status == DeliveryCycleStatus.OPEN
