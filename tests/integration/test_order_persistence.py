import pytest

from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.commands.orders import place_order, update_order
from src.core.clock import Clock
from src.core.exceptions import ConflictError, NotFoundError
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Customer, Order, OrderStatus
from src.queries.orders import list_orders_for_customer
from tests.helpers import future_cycle_window, past_cycle_window, unique_email


def test_order_persists(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with SqlAlchemyUnitOfWork() as uow:
        created = uow.orders.add(
            Order(
                cycle_id=cycle.id,
                customer_id=customer_id,
                quantity=6,
                status=OrderStatus.OPEN,
            )
        )
        uow.commit()
        order_id = created.id

    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.orders.get(order_id)
        assert stored is not None
        assert stored.cycle_id == cycle.id
        assert stored.customer_id == customer_id
        assert stored.quantity == 6
        assert stored.status == OrderStatus.OPEN
        assert stored.created_at is not None
        assert stored.updated_at is not None


def test_order_unknown_cycle(customer_id: int) -> None:
    with pytest.raises(NotFoundError, match="Referenced entity does not exist"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.orders.add(
                Order(
                    cycle_id=0,
                    customer_id=customer_id,
                    quantity=6,
                    status=OrderStatus.OPEN,
                )
            )
            uow.commit()


def test_order_unknown_customer(provider_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with pytest.raises(NotFoundError, match="Referenced entity does not exist"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.orders.add(
                Order(
                    cycle_id=cycle.id,
                    customer_id=0,
                    quantity=6,
                    status=OrderStatus.OPEN,
                )
            )
            uow.commit()


def test_place_order_persists(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    placed = place_order(
        customer_id=customer_id,
        cycle_id=cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.orders.get(placed.id)
        assert stored is not None
        assert stored.cycle_id == cycle.id
        assert stored.customer_id == customer_id
        assert stored.quantity == 6
        assert stored.status == OrderStatus.OPEN


def test_update_order_quantity_persists(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    placed = place_order(
        customer_id=customer_id,
        cycle_id=cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    updated = update_order(
        customer_id=customer_id,
        order_id=placed.id,
        quantity=12,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    assert updated.quantity == 12
    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.orders.get(placed.id)
        assert stored is not None
        assert stored.quantity == 12
        assert stored.status == OrderStatus.OPEN


def test_update_order_soft_cancel_persists(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    placed = place_order(
        customer_id=customer_id,
        cycle_id=cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    updated = update_order(
        customer_id=customer_id,
        order_id=placed.id,
        status=OrderStatus.CANCELLED,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    assert updated.status == OrderStatus.CANCELLED
    assert updated.quantity == 6
    with SqlAlchemyUnitOfWork() as uow:
        stored = uow.orders.get(placed.id)
        assert stored is not None
        assert stored.status == OrderStatus.CANCELLED
        assert stored.quantity == 6


def test_place_order_unknown_cycle(customer_id: int) -> None:
    with pytest.raises(NotFoundError, match="Cycle not found"):
        place_order(
            customer_id=customer_id,
            cycle_id=0,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )


def test_place_order_closed_cycle(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    update_delivery_cycle(
        provider_id=provider_id,
        cycle_id=cycle.id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with pytest.raises(ConflictError, match="Cycle is already closed"):
        place_order(
            customer_id=customer_id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )


def test_list_orders_for_customer_includes_open_and_cancelled(
    provider_id: int, customer_id: int
) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    first_cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    second_cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    cancelled = place_order(
        customer_id=customer_id,
        cycle_id=first_cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    update_order(
        customer_id=customer_id,
        order_id=cancelled.id,
        status=OrderStatus.CANCELLED,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    opened = place_order(
        customer_id=customer_id,
        cycle_id=second_cycle.id,
        quantity=12,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_orders_for_customer(
        customer_id=customer_id,
        uow=SqlAlchemyUnitOfWork(),
    )
    by_id = {order.id: order for order in listed}

    assert by_id[cancelled.id].status == OrderStatus.CANCELLED
    assert by_id[cancelled.id].quantity == 6
    assert by_id[opened.id].status == OrderStatus.OPEN
    assert by_id[opened.id].quantity == 12


def test_list_orders_for_customer_isolates_customers(
    provider_id: int, customer_id: int
) -> None:
    other_uow = SqlAlchemyUnitOfWork()
    with other_uow:
        other = Customer(
            first_name="Grace",
            last_name="Hopper",
            email=unique_email(prefix="customer"),
        )
        other_uow.customers.add(other)
        other_uow.commit()
        other_id = other.id

    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    place_order(
        customer_id=customer_id,
        cycle_id=cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    place_order(
        customer_id=other_id,
        cycle_id=cycle.id,
        quantity=12,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_orders_for_customer(
        customer_id=customer_id,
        uow=SqlAlchemyUnitOfWork(),
    )
    assert [order.quantity for order in listed] == [6]


def test_list_orders_for_customer_includes_orders_after_cycle_closed(
    provider_id: int, customer_id: int
) -> None:
    cutoff_at, delivery_at = future_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    placed = place_order(
        customer_id=customer_id,
        cycle_id=cycle.id,
        quantity=6,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )
    update_delivery_cycle(
        provider_id=provider_id,
        cycle_id=cycle.id,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    listed = list_orders_for_customer(
        customer_id=customer_id,
        uow=SqlAlchemyUnitOfWork(),
    )
    assert [order.id for order in listed] == [placed.id]
    assert listed[0].status == OrderStatus.OPEN


def test_list_orders_for_customer_unknown_customer() -> None:
    with pytest.raises(NotFoundError, match="Customer not found"):
        list_orders_for_customer(
            customer_id=0,
            uow=SqlAlchemyUnitOfWork(),
        )


def test_place_order_after_cutoff(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = past_cycle_window()
    cycle = create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=delivery_at,
        cutoff_at=cutoff_at,
        max_eggs=48,
        uow=SqlAlchemyUnitOfWork(),
        clock=Clock(),
    )

    with pytest.raises(ConflictError, match="Cycle is already closed"):
        place_order(
            customer_id=customer_id,
            cycle_id=cycle.id,
            quantity=6,
            uow=SqlAlchemyUnitOfWork(),
            clock=Clock(),
        )
