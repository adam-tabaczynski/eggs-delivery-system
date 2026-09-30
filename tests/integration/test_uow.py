import pytest
from sqlalchemy import select

from src.core.clock import Clock
from src.core.exceptions import ConflictError, NotFoundError
from src.core.integrations.sqlalchemy.session import SessionFactory
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Customer, DeliveryCycle
from tests.generators import make_customer


def _find_email(email: str) -> Customer | None:
    with SessionFactory() as session:
        return session.scalar(select(Customer).where(Customer.email == email))


class TestUnitOfWork:
    def test_commit_persists(self) -> None:
        email = "committed@example.com"

        with SqlAlchemyUnitOfWork() as uow:
            uow.customers.add(
                Customer(first_name="Ada", last_name="Lovelace", email=email)
            )
            uow.commit()

        assert _find_email(email) is not None

    def test_rolls_back_uncommitted_work(self) -> None:
        email = "uncommitted@example.com"

        with SqlAlchemyUnitOfWork() as uow:
            uow.customers.add(
                Customer(first_name="Ada", last_name="Lovelace", email=email)
            )

        assert _find_email(email) is None

    def test_rolls_back_on_error(self) -> None:
        class Boom(Exception):
            pass

        email = "failed@example.com"

        with pytest.raises(Boom), SqlAlchemyUnitOfWork() as uow:
            uow.customers.add(
                Customer(first_name="Ada", last_name="Lovelace", email=email)
            )
            raise Boom()

        assert _find_email(email) is None

    def test_maps_unique_violation_to_conflict(self) -> None:
        existing = make_customer()

        with (
            pytest.raises(ConflictError, match="Unique constraint violated"),
            SqlAlchemyUnitOfWork() as uow,
        ):
            uow.customers.add(
                Customer(first_name="Ada", last_name="Lovelace", email=existing.email)
            )
            uow.commit()

    def test_maps_foreign_key_violation_to_not_found(self) -> None:
        clock = Clock()

        with (
            pytest.raises(NotFoundError, match="Referenced entity does not exist"),
            SqlAlchemyUnitOfWork() as uow,
        ):
            uow.cycles.add(
                DeliveryCycle(
                    provider_id=0,
                    cutoff_at=clock.move_datetime_forward(days=5),
                    delivery_at=clock.move_datetime_forward(days=7),
                    max_eggs=12,
                )
            )
            uow.commit()
