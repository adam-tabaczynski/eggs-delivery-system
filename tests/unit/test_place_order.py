import pytest

from src.commands.customers import register_customer
from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.commands.orders import place_order, update_order
from src.core.clock import Clock
from src.exceptions import (
    CycleAlreadyClosed,
    CycleCapacityExceeded,
    CycleNotFound,
    CustomerNotFound,
    OrderAlreadyCancelled,
    OrderNotFound,
)
from src.models import OrderStatus, Provider
from src.schemas import CustomerRead, DeliveryCycleRead
from tests.fakes import FakeUnitOfWork
from tests.helpers import future_cycle_window, past_cycle_window, unique_email


def _add_provider(uow: FakeUnitOfWork) -> Provider:
    provider = Provider(name="Test Farm", email=unique_email(prefix="provider"))
    return uow.providers.add(provider)


def _add_customer(uow: FakeUnitOfWork) -> CustomerRead:
    return register_customer(
        first_name="Ada",
        last_name="Lovelace",
        email=unique_email(prefix="customer"),
        uow=uow,
    )


def _add_open_cycle(
    uow: FakeUnitOfWork, provider_id: int, *, max_eggs: int = 48
) -> DeliveryCycleRead:
    cutoff_at, delivery_at = future_cycle_window()
    return create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=max_eggs,
        uow=uow,
        clock=Clock(),
    )


def test_place_order_commits() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)

    result = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    assert result.customer_id == customer.id
    assert result.cycle_id == cycle.id
    assert result.quantity == 6
    assert result.status == OrderStatus.OPEN
    assert result.id == 1
    assert uow.committed
    stored = uow.orders.get(result.id)
    assert stored is not None
    assert stored.quantity == 6


def test_place_order_unknown_customer() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    cycle = _add_open_cycle(uow, provider.id)

    with pytest.raises(CustomerNotFound, match="Customer not found"):
        place_order(
            customer_id=99,
            cycle_id=cycle.id,
            quantity=6,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_place_order_unknown_cycle() -> None:
    uow = FakeUnitOfWork()
    customer = _add_customer(uow)

    with pytest.raises(CycleNotFound, match="Cycle not found"):
        place_order(
            customer_id=customer.id,
            cycle_id=99,
            quantity=6,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_place_order_closed_cycle() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    update_delivery_cycle(
        provider_id=provider.id,
        cycle_id=cycle.id,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed


def test_place_order_after_cutoff() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cutoff_at, delivery_at = past_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        place_order(
            customer_id=customer.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed


def test_update_order_quantity_commits() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    result = update_order(
        customer_id=customer.id,
        order_id=placed.id,
        quantity=12,
        uow=uow,
        clock=Clock(),
    )

    assert result.quantity == 12
    assert result.status == OrderStatus.OPEN
    stored = uow.orders.get(placed.id)
    assert stored is not None
    assert stored.quantity == 12
    assert uow.committed


def test_update_order_soft_cancel_keeps_row() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    result = update_order(
        customer_id=customer.id,
        order_id=placed.id,
        status=OrderStatus.CANCELLED,
        uow=uow,
        clock=Clock(),
    )

    assert result.status == OrderStatus.CANCELLED
    assert result.quantity == 6
    stored = uow.orders.get(placed.id)
    assert stored is not None
    assert stored.status == OrderStatus.CANCELLED
    assert stored.quantity == 6
    assert uow.committed


def test_update_order_already_cancelled() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )
    update_order(
        customer_id=customer.id,
        order_id=placed.id,
        status=OrderStatus.CANCELLED,
        uow=uow,
        clock=Clock(),
    )

    with pytest.raises(OrderAlreadyCancelled, match="Order is already cancelled"):
        update_order(
            customer_id=customer.id,
            order_id=placed.id,
            quantity=12,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_update_order_unknown_customer() -> None:
    uow = FakeUnitOfWork()

    with pytest.raises(CustomerNotFound, match="Customer not found"):
        update_order(
            customer_id=99,
            order_id=1,
            quantity=12,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_update_order_unknown_order() -> None:
    uow = FakeUnitOfWork()
    customer = _add_customer(uow)

    with pytest.raises(OrderNotFound, match="Order not found"):
        update_order(
            customer_id=customer.id,
            order_id=99,
            quantity=12,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed


def test_update_order_other_customer() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    owner = _add_customer(uow)
    other = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    placed = place_order(
        customer_id=owner.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    with pytest.raises(OrderNotFound, match="Order not found"):
        update_order(
            customer_id=other.id,
            order_id=placed.id,
            quantity=12,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed
    stored = uow.orders.get(placed.id)
    assert stored is not None
    assert stored.quantity == 6


def test_update_order_closed_cycle() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=clock,
    )
    update_delivery_cycle(
        provider_id=provider.id,
        cycle_id=cycle.id,
        uow=uow,
        clock=clock,
    )

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_order(
            customer_id=customer.id,
            order_id=placed.id,
            quantity=12,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed


def test_update_order_after_cutoff() -> None:
    uow = FakeUnitOfWork()
    clock = Clock()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider.id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=clock,
    )
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=clock,
    )
    stored_cycle = uow.cycles.get(cycle.id)
    assert stored_cycle is not None
    past_cutoff, past_delivery = past_cycle_window()
    stored_cycle.cutoff_at = past_cutoff
    stored_cycle.delivery_at = past_delivery

    with pytest.raises(CycleAlreadyClosed, match="Cycle is already closed"):
        update_order(
            customer_id=customer.id,
            order_id=placed.id,
            status=OrderStatus.CANCELLED,
            uow=uow,
            clock=clock,
        )
    assert not uow.committed
    stored = uow.orders.get(placed.id)
    assert stored is not None
    assert stored.status == OrderStatus.OPEN


def test_place_order_fills_remaining_capacity() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    first = _add_customer(uow)
    second = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id, max_eggs=12)
    place_order(
        customer_id=first.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    result = place_order(
        customer_id=second.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    assert result.quantity == 6
    assert uow.committed
    assert uow.orders.sum_open_quantity(cycle.id) == 12


def test_place_order_rejects_over_capacity() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    first = _add_customer(uow)
    second = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id, max_eggs=12)
    place_order(
        customer_id=first.id,
        cycle_id=cycle.id,
        quantity=8,
        uow=uow,
        clock=Clock(),
    )

    with pytest.raises(CycleCapacityExceeded, match="Cycle egg capacity exceeded"):
        place_order(
            customer_id=second.id,
            cycle_id=cycle.id,
            quantity=6,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed
    assert uow.orders.sum_open_quantity(cycle.id) == 8


def test_place_order_ignores_cancelled_quantity() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    first = _add_customer(uow)
    second = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id, max_eggs=6)
    placed = place_order(
        customer_id=first.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )
    update_order(
        customer_id=first.id,
        order_id=placed.id,
        status=OrderStatus.CANCELLED,
        uow=uow,
        clock=Clock(),
    )

    result = place_order(
        customer_id=second.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    assert result.quantity == 6
    assert uow.committed


def test_place_order_capacity_is_per_cycle() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    first = _add_customer(uow)
    second = _add_customer(uow)
    first_cycle = _add_open_cycle(uow, provider.id, max_eggs=6)
    second_cycle = _add_open_cycle(uow, provider.id, max_eggs=6)
    place_order(
        customer_id=first.id,
        cycle_id=first_cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    result = place_order(
        customer_id=second.id,
        cycle_id=second_cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    assert result.cycle_id == second_cycle.id
    assert uow.committed


def test_update_order_rejects_quantity_over_capacity() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    first = _add_customer(uow)
    second = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id, max_eggs=12)
    place_order(
        customer_id=first.id,
        cycle_id=cycle.id,
        quantity=8,
        uow=uow,
        clock=Clock(),
    )
    placed = place_order(
        customer_id=second.id,
        cycle_id=cycle.id,
        quantity=2,
        uow=uow,
        clock=Clock(),
    )

    with pytest.raises(CycleCapacityExceeded, match="Cycle egg capacity exceeded"):
        update_order(
            customer_id=second.id,
            order_id=placed.id,
            quantity=6,
            uow=uow,
            clock=Clock(),
        )
    assert not uow.committed
    stored = uow.orders.get(placed.id)
    assert stored is not None
    assert stored.quantity == 2


def test_update_order_can_decrease_when_at_capacity() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id, max_eggs=6)
    placed = place_order(
        customer_id=customer.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )

    result = update_order(
        customer_id=customer.id,
        order_id=placed.id,
        quantity=4,
        uow=uow,
        clock=Clock(),
    )

    assert result.quantity == 4
    assert uow.committed
