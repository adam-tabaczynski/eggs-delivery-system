import pytest

from src.commands.cycles import create_delivery_cycle
from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import CycleCutoffNotInFuture, ProviderNotFound
from src.models import DeliveryCycleStatus
from tests.generators import make_provider


class TestCreateDeliveryCycle:
    def test_creates_cycle(self) -> None:
        clock = Clock()
        provider = make_provider()
        cutoff_at = clock.move_datetime_forward(days=5)
        delivery_at = clock.move_datetime_forward(days=7)
        max_eggs = 48

        result = create_delivery_cycle(
            provider_id=provider.id,
            delivery_at=delivery_at,
            cutoff_at=cutoff_at,
            max_eggs=max_eggs,
            uow=SqlAlchemyUnitOfWork(),
            clock=clock,
        )

        assert result.provider_id == provider.id
        assert result.delivery_at == delivery_at
        assert result.cutoff_at == cutoff_at
        assert result.max_eggs == max_eggs
        assert result.status is DeliveryCycleStatus.OPEN

    def test_unknown_provider(self) -> None:
        clock = Clock()

        with pytest.raises(ProviderNotFound):
            create_delivery_cycle(
                provider_id=0,
                delivery_at=clock.move_datetime_forward(days=7),
                cutoff_at=clock.move_datetime_forward(days=5),
                max_eggs=48,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )

    def test_rejects_cutoff_in_past(self) -> None:
        clock = Clock()
        provider = make_provider()

        with pytest.raises(CycleCutoffNotInFuture):
            create_delivery_cycle(
                provider_id=provider.id,
                delivery_at=clock.move_datetime_forward(days=1),
                cutoff_at=clock.move_datetime_backward(hours=1),
                max_eggs=48,
                uow=SqlAlchemyUnitOfWork(),
                clock=clock,
            )
