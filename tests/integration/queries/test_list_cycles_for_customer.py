import pytest

from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import CustomerNotFound
from src.models import DeliveryCycleStatus
from src.queries.cycles import list_cycles_for_customer
from tests.generators import make_customer, make_cycle, make_provider


class TestListCyclesForCustomer:
    def test_lists_open_and_past_cycles(self) -> None:
        clock = Clock()
        provider = make_provider()
        opened = make_cycle(provider_id=provider.id)
        past = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=2),
            delivery_at=clock.move_datetime_backward(days=1),
        )
        customer = make_customer()

        result = list_cycles_for_customer(
            customer_id=customer.id, uow=SqlAlchemyUnitOfWork(), clock=clock
        )

        statuses = {
            cycle.id: cycle.status
            for cycle in result
            if cycle.id in {opened.id, past.id}
        }
        assert statuses == {
            past.id: DeliveryCycleStatus.CLOSED,
            opened.id: DeliveryCycleStatus.OPEN,
        }

    def test_unknown_customer(self) -> None:
        with pytest.raises(CustomerNotFound):
            list_cycles_for_customer(
                customer_id=0, uow=SqlAlchemyUnitOfWork(), clock=Clock()
            )
