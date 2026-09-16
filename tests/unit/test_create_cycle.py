import pytest

from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.exceptions import CycleAlreadyClosed, CycleNotFound, ProviderNotFound
from src.models import DeliveryCycleStatus, Provider
from src.queries.cycles import list_cycles_for_provider
from tests.fakes import FakeUnitOfWork
from tests.helpers import future_cycle_window, past_cycle_window, unique_email


def _add_provider(uow: FakeUnitOfWork) -> Provider:
    provider = Provider(name="Test Farm", email=unique_email(prefix="provider"))
    return uow.providers.add(provider)


def test_create_cycle_commits() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()

    result = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )

    assert result.provider_id == provider.id
    assert result.delivery_at == delivery_at
    assert result.cutoff_at == cutoff_at
    assert result.max_eggs == 48
    assert result.status == DeliveryCycleStatus.OPEN
    assert result.id == 1
    assert uow.committed
    assert len(uow.cycles.list_by_provider_id(provider.id)) == 1


def test_create_cycle_unknown_provider() -> None:
    uow = FakeUnitOfWork()
    cutoff_at, delivery_at = future_cycle_window()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        create_delivery_cycle(
            provider_id=99,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=48,
            uow=uow,
        )
    assert not uow.committed


def test_list_cycles_for_provider() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    other = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()

    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=12,
        uow=uow,
    )
    create_delivery_cycle(
        provider_id=other.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=24,
        uow=uow,
    )

    result = list_cycles_for_provider(provider_id=provider.id, uow=uow)

    assert len(result) == 1
    assert result[0].provider_id == provider.id
    assert result[0].max_eggs == 12


def test_list_cycles_unknown_provider() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        list_cycles_for_provider(provider_id=99, uow=uow)


def test_update_cycle_commits() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )

    result = update_delivery_cycle(
        provider_id=provider.id,
        cycle_id=created.id,
        uow=uow,
    )

    assert result.status == DeliveryCycleStatus.CLOSED
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.CLOSED
    assert uow.committed


def test_update_cycle_unknown_provider() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        update_delivery_cycle(provider_id=99, cycle_id=1, uow=uow)
    assert not uow.committed


def test_update_cycle_unknown_cycle() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)

    with pytest.raises(CycleNotFound, match="Cycle not found"):
        update_delivery_cycle(provider_id=provider.id, cycle_id=99, uow=uow)
    assert not uow.committed


def test_update_cycle_other_provider() -> None:
    uow = FakeUnitOfWork()
    owner = _add_provider(uow)
    other = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=owner.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )

    with pytest.raises(CycleNotFound, match="Cycle not found"):
        update_delivery_cycle(
            provider_id=other.id,
            cycle_id=created.id,
            uow=uow,
        )
    assert not uow.committed
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.OPEN


def test_update_cycle_already_closed() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )
    update_delivery_cycle(provider_id=provider.id, cycle_id=created.id, uow=uow)

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_delivery_cycle(provider_id=provider.id, cycle_id=created.id, uow=uow)
    assert not uow.committed


def test_update_cycle_after_cutoff() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = past_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_delivery_cycle(provider_id=provider.id, cycle_id=created.id, uow=uow)
    assert not uow.committed
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.OPEN


def test_list_treats_past_cutoff_as_closed() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = past_cycle_window()
    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
    )

    result = list_cycles_for_provider(provider_id=provider.id, uow=uow)

    assert result[0].status == DeliveryCycleStatus.CLOSED
    assert uow.cycles.list_by_provider_id(provider.id)[0].status == DeliveryCycleStatus.OPEN
