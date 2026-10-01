from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestDeliveryCycleRepository:
    def test_get_allocated_eggs_excludes_cancelled_and_other_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=4,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )
        make_order(
            cycle_id=other_cycle.id,
            customer_id=customer.id,
            quantity=8,
            status=OrderStatus.OPEN,
        )

        with SqlAlchemyUnitOfWork() as uow:
            assert uow.cycles.get_allocated_eggs(cycle.id) == 4

    def test_get_allocated_eggs_excludes_given_order(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=4)
        make_order(cycle_id=cycle.id, customer_id=other_customer.id, quantity=6)

        with SqlAlchemyUnitOfWork() as uow:
            assert (
                uow.cycles.get_allocated_eggs(cycle.id, exclude_order_id=order.id) == 6
            )

    def test_list_with_allocated_eggs_by_provider_id(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        empty_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=4,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        with SqlAlchemyUnitOfWork() as uow:
            rows = uow.cycles.list_with_allocated_eggs_by_provider_id(provider.id)
            by_id = {row.cycle.id: row.allocated_eggs for row in rows}

        assert by_id == {cycle.id: 4, empty_cycle.id: 0}

    def test_list_all_with_allocated_eggs(self) -> None:
        provider = make_provider()
        other_provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_provider_cycle = make_cycle(provider_id=other_provider.id)
        customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=4,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        with SqlAlchemyUnitOfWork() as uow:
            rows = uow.cycles.list_all_with_allocated_eggs()
            created = {cycle.id, other_provider_cycle.id}
            by_id = {
                row.cycle.id: row.allocated_eggs
                for row in rows
                if row.cycle.id in created
            }

        assert by_id == {cycle.id: 4, other_provider_cycle.id: 0}
