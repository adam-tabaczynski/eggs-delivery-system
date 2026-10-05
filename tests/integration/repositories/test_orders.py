from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestOrderRepository:
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

    def test_cancel_open_by_cycle_id(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        other_cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        open_order = make_order(cycle_id=cycle.id, customer_id=customer.id)
        cancelled_order = make_order(
            cycle_id=cycle.id,
            customer_id=other_customer.id,
            status=OrderStatus.CANCELLED,
        )
        other_cycle_order = make_order(cycle_id=other_cycle.id, customer_id=customer.id)

        with SqlAlchemyUnitOfWork() as uow:
            uow.orders.cancel_open_by_cycle_id(cycle.id)
            uow.commit()

        with SqlAlchemyUnitOfWork() as uow:
            cascaded = uow.orders.get(open_order.id)
            untouched = uow.orders.get(cancelled_order.id)
            other = uow.orders.get(other_cycle_order.id)
            assert cascaded is not None
            assert untouched is not None
            assert other is not None
            assert cascaded.status is OrderStatus.CANCELLED
            assert cascaded.updated_at > open_order.updated_at
            assert untouched.updated_at == cancelled_order.updated_at
            assert other.status is OrderStatus.OPEN
