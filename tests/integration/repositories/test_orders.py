from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestOrderRepository:
    def test_sum_open_quantity_excludes_cancelled_and_other_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=4)
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )
        make_order(cycle_id=other_cycle.id, customer_id=customer.id, quantity=8)

        with SqlAlchemyUnitOfWork() as uow:
            assert uow.orders.sum_open_quantity(cycle.id) == 4

    def test_get_open_order_for_customer_ignores_cancelled_and_other_cycles(
        self,
    ) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            status=OrderStatus.CANCELLED,
        )
        make_order(cycle_id=other_cycle.id, customer_id=customer.id)
        other_order = make_order(cycle_id=cycle.id, customer_id=other_customer.id)

        with SqlAlchemyUnitOfWork() as uow:
            assert (
                uow.orders.get_open_order_for_customer(
                    customer_id=customer.id, cycle_id=cycle.id
                )
                is None
            )
            found = uow.orders.get_open_order_for_customer(
                customer_id=other_customer.id, cycle_id=cycle.id
            )
            assert found is not None
            assert found.id == other_order.id
