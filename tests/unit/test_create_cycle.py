import pytest

from src.commands.cycles import create_delivery_cycle
from src.exceptions import NotFoundError
from src.models import DeliveryCycleStatus, Provider
from src.queries.cycles import list_cycles_for_provider
from tests.fakes import FakeUnitOfWork
from tests.helpers import future_cycle_window, unique_email


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

    with pytest.raises(NotFoundError, match="Provider not found"):
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

    with pytest.raises(NotFoundError, match="Provider not found"):
        list_cycles_for_provider(provider_id=99, uow=uow)
