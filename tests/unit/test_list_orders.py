import pytest

from src.commands.customers import register_customer
from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.commands.orders import place_order, update_order
from src.core.clock import Clock
from src.exceptions import CustomerNotFound
from src.models import OrderStatus, Provider
from src.queries.orders import list_orders_for_customer
from src.schemas import CustomerRead, DeliveryCycleRead
from tests.fakes import FakeUnitOfWork
from tests.helpers import future_cycle_window, unique_email


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


def _add_open_cycle(uow: FakeUnitOfWork, provider_id: int) -> DeliveryCycleRead:
    cutoff_at, delivery_at = future_cycle_window()
    return create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=uow,
        clock=Clock(),
    )


def test_list_orders_includes_open_and_cancelled() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    customer = _add_customer(uow)
    first_cycle = _add_open_cycle(uow, provider.id)
    second_cycle = _add_open_cycle(uow, provider.id)
    cancelled = place_order(
        customer_id=customer.id,
        cycle_id=first_cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )
    update_order(
        customer_id=customer.id,
        order_id=cancelled.id,
        status=OrderStatus.CANCELLED,
        uow=uow,
        clock=Clock(),
    )
    opened = place_order(
        customer_id=customer.id,
        cycle_id=second_cycle.id,
        quantity=12,
        uow=uow,
        clock=Clock(),
    )

    listed = list_orders_for_customer(customer_id=customer.id, uow=uow)
    by_id = {order.id: order for order in listed}

    assert by_id[cancelled.id].status == OrderStatus.CANCELLED
    assert by_id[opened.id].status == OrderStatus.OPEN


def test_list_orders_isolates_customers() -> None:
    uow = FakeUnitOfWork()
    provider = _add_provider(uow)
    owner = _add_customer(uow)
    other = _add_customer(uow)
    cycle = _add_open_cycle(uow, provider.id)
    place_order(
        customer_id=owner.id,
        cycle_id=cycle.id,
        quantity=6,
        uow=uow,
        clock=Clock(),
    )
    place_order(
        customer_id=other.id,
        cycle_id=cycle.id,
        quantity=12,
        uow=uow,
        clock=Clock(),
    )

    listed = list_orders_for_customer(customer_id=owner.id, uow=uow)
    assert [order.quantity for order in listed] == [6]


def test_list_orders_includes_orders_after_cycle_closed() -> None:
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

    listed = list_orders_for_customer(customer_id=customer.id, uow=uow)
    assert [order.id for order in listed] == [placed.id]
    assert listed[0].status == OrderStatus.OPEN


def test_list_orders_unknown_customer() -> None:
    uow = FakeUnitOfWork()
    with pytest.raises(CustomerNotFound, match="Customer not found"):
        list_orders_for_customer(customer_id=99, uow=uow)
