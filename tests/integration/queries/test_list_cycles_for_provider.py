import pytest

from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import ProviderNotFound
from src.models import DeliveryCycleStatus, OrderStatus
from src.queries.cycles import list_cycles_for_provider
from tests.generators import make_customer, make_cycle, make_order, make_provider


class TestListCyclesForProvider:
    def test_lists_cycles_by_delivery_date(self) -> None:
        clock = Clock()
        provider = make_provider()
        later = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_forward(days=8),
            delivery_at=clock.move_datetime_forward(days=10),
        )
        earlier = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_forward(days=3),
            delivery_at=clock.move_datetime_forward(days=5),
        )

        result = list_cycles_for_provider(
            provider_id=provider.id, uow=SqlAlchemyUnitOfWork(), clock=clock
        )

        assert [cycle.id for cycle in result] == [earlier.id, later.id]

    def test_isolates_providers(self) -> None:
        provider = make_provider()
        own = make_cycle(provider_id=provider.id)
        other_provider = make_provider()
        make_cycle(provider_id=other_provider.id)

        result = list_cycles_for_provider(
            provider_id=provider.id, uow=SqlAlchemyUnitOfWork(), clock=Clock()
        )

        assert [cycle.id for cycle in result] == [own.id]

    def test_reports_past_cutoff_as_closed(self) -> None:
        clock = Clock()
        provider = make_provider()
        cycle = make_cycle(
            provider_id=provider.id,
            cutoff_at=clock.move_datetime_backward(days=2),
            delivery_at=clock.move_datetime_backward(days=1),
        )

        result = list_cycles_for_provider(
            provider_id=provider.id, uow=SqlAlchemyUnitOfWork(), clock=clock
        )

        assert cycle.status is DeliveryCycleStatus.OPEN
        assert [listed.status for listed in result] == [DeliveryCycleStatus.CLOSED]

    def test_reports_allocated_eggs(self) -> None:
        provider = make_provider()
        customer = make_customer()
        other_customer = make_customer()
        open_cycle = make_cycle(provider_id=provider.id)
        make_order(
            cycle_id=open_cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=open_cycle.id,
            customer_id=other_customer.id,
            quantity=12,
            status=OrderStatus.OPEN,
        )
        make_order(
            cycle_id=open_cycle.id,
            customer_id=customer.id,
            quantity=30,
            status=OrderStatus.CANCELLED,
        )
        closed_cycle = make_cycle(
            provider_id=provider.id, status=DeliveryCycleStatus.CLOSED
        )
        make_order(
            cycle_id=closed_cycle.id,
            customer_id=customer.id,
            quantity=10,
            status=OrderStatus.OPEN,
        )
        empty_cycle = make_cycle(provider_id=provider.id)

        result = list_cycles_for_provider(
            provider_id=provider.id, uow=SqlAlchemyUnitOfWork(), clock=Clock()
        )

        by_id = {listed.id: listed.allocated_eggs for listed in result}
        assert by_id == {open_cycle.id: 18, closed_cycle.id: 10, empty_cycle.id: 0}

    def test_unknown_provider(self) -> None:
        with pytest.raises(ProviderNotFound):
            list_cycles_for_provider(
                provider_id=0, uow=SqlAlchemyUnitOfWork(), clock=Clock()
            )
