import pytest

from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.core.clock import Clock
from src.commands.customers import register_customer
from src.exceptions import (
    CycleAlreadyClosed,
    CycleNotFound,
    CustomerNotFound,
    ProviderNotFound,
)
from src.models import DeliveryCycleStatus, Provider
from src.queries.cycles import list_cycles_for_customer, list_cycles_for_provider
from tests.fakes import FakeUnitOfWork
from tests.helpers import future_cycle_window, past_cycle_window, unique_email


def _add_provider(uow: FakeUnitOfWork) -> Provider:
    provider = Provider(name="Test Farm", email=unique_email(prefix="provider"))
    return uow.providers.add(provider)


def test_create_cycle_commits() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()

    result = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
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
    clock = Clock()
    cutoff_at, delivery_at = future_cycle_window()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        create_delivery_cycle(
            provider_id=99,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=48,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed


def test_list_cycles_for_provider() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    other = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()

    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=12,
        uow=uow,
        clock=clock,
    )
    create_delivery_cycle(
        provider_id=other.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=24,
        uow=uow,
        clock=clock,
    )

    result = list_cycles_for_provider(provider_id=provider.id, uow=uow, clock=clock)

    assert len(result) == 1
    assert result[0].provider_id == provider.id
    assert result[0].max_eggs == 12


def test_list_cycles_unknown_provider() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        list_cycles_for_provider(provider_id=99, uow=uow, clock=Clock())


def test_update_cycle_commits() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )

    result = update_delivery_cycle(
        provider_id=provider.id,
        cycle_id=created.id,
        uow=uow,
        clock=clock,
    )

    assert result.status == DeliveryCycleStatus.CLOSED
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.CLOSED
    assert uow.committed


def test_update_cycle_unknown_provider() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(ProviderNotFound, match="Provider not found"):
        update_delivery_cycle(provider_id=99, cycle_id=1, uow=uow, clock=Clock())
    assert not uow.committed


def test_update_cycle_unknown_cycle() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)

    with pytest.raises(CycleNotFound, match="Cycle not found"):
        update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=99,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_update_cycle_other_provider() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    owner = _add_provider(uow)
    other = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=owner.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleNotFound, match="Cycle not found"):
        update_delivery_cycle(
            provider_id=other.id,
            cycle_id=created.id,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.OPEN


def test_update_cycle_already_closed() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = future_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )
    update_delivery_cycle(
        provider_id=provider.id,
        cycle_id=created.id,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=created.id,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed


def test_update_cycle_after_cutoff() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = past_cycle_window()
    created = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_delivery_cycle(
            provider_id=provider.id,
            cycle_id=created.id,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed
    stored = uow.cycles.get(created.id)
    assert stored is not None
    assert stored.status == DeliveryCycleStatus.OPEN


def test_list_treats_past_cutoff_as_closed() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    cutoff_at, delivery_at = past_cycle_window()
    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )

    result = list_cycles_for_provider(provider_id=provider.id, uow=uow, clock=clock)

    assert result[0].status == DeliveryCycleStatus.CLOSED
    assert uow.cycles.list_by_provider_id(provider.id)[0].status == DeliveryCycleStatus.OPEN


def test_list_cycles_for_customer_includes_open_and_past() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    customer = register_customer(
        first_name="Ada",
        last_name="Lovelace",
        email=unique_email(prefix="customer"),
        uow=uow,
    )
    past_cutoff, past_delivery = past_cycle_window()
    open_cutoff, open_delivery = future_cycle_window()
    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=past_delivery,
        cutoff_at=past_cutoff,
        max_eggs=12,
        uow=uow,
        clock=clock,
    )
    create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=open_delivery,
        cutoff_at=open_cutoff,
        max_eggs=24,
        uow=uow,
        clock=clock,
    )

    result = list_cycles_for_customer(customer_id=customer.id, uow=uow, clock=clock)

    assert [cycle.max_eggs for cycle in result] == [12, 24]
    assert result[0].status == DeliveryCycleStatus.CLOSED
    assert result[1].status == DeliveryCycleStatus.OPEN


def test_list_cycles_for_customer_empty() -> None:
    uow = FakeUnitOfWork()
    customer = register_customer(
        first_name="Ada",
        last_name="Lovelace",
        email=unique_email(prefix="customer"),
        uow=uow,
    )

    result = list_cycles_for_customer(
        customer_id=customer.id, uow=uow, clock=Clock()
    )

    assert result == []


def test_list_cycles_for_customer_unknown_customer() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(CustomerNotFound, match="Customer not found"):
        list_cycles_for_customer(customer_id=99, uow=uow, clock=Clock())
