import pytest

from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import ProviderNotFound
from src.models import DeliveryCycleStatus
from src.queries.cycles import list_cycles_for_provider
from tests.generators import make_cycle, make_provider


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
        make_cycle(provider_id=make_provider().id)

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

    def test_unknown_provider(self) -> None:
        with pytest.raises(ProviderNotFound):
            list_cycles_for_provider(
                provider_id=0, uow=SqlAlchemyUnitOfWork(), clock=Clock()
            )
