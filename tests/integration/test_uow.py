import pytest
from sqlalchemy import select

from src.core.integrations.sqlalchemy.session import SessionFactory
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.core.exceptions import ConflictError, NotFoundError
from src.models import Customer, DeliveryCycle, DeliveryCycleStatus
from tests.helpers import future_cycle_window, unique_email


def _customer(email: str) -> Customer:
    return Customer(first_name="Ada", last_name="Lovelace", email=email)


def _find_email(email: str) -> Customer | None:
    with SessionFactory() as session:
        return session.scalar(select(Customer).where(Customer.email == email))


def test_uow_commit_persists() -> None:
    email = unique_email(prefix="uow")
    uow = SqlAlchemyUnitOfWork()
    with uow:
        assert uow.session is not None
        uow.session.add(_customer(email))
        uow.commit()

    assert _find_email(email) is not None


def test_uow_rolls_back_uncommitted_work() -> None:
    email = unique_email(prefix="uow")
    uow = SqlAlchemyUnitOfWork()
    with uow:
        assert uow.session is not None
        uow.session.add(_customer(email))

    assert _find_email(email) is None


def test_uow_rolls_back_on_error() -> None:
    class Boom(Exception):
        pass

    email = unique_email(prefix="uow")
    uow = SqlAlchemyUnitOfWork()
    with pytest.raises(Boom):
        with uow:
            assert uow.session is not None
            uow.session.add(_customer(email))
            raise Boom()

    assert _find_email(email) is None


def test_uow_maps_unique_violation_to_conflict() -> None:
    email = unique_email(prefix="uow")
    with SqlAlchemyUnitOfWork() as uow:
        uow.customers.add(_customer(email))
        uow.commit()

    with pytest.raises(ConflictError, match="Unique constraint violated"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.customers.add(_customer(email))
            uow.commit()


def test_uow_maps_foreign_key_violation_to_not_found() -> None:
    cutoff_at, delivery_at = future_cycle_window()
    with pytest.raises(NotFoundError, match="Referenced entity does not exist"):
        with SqlAlchemyUnitOfWork() as uow:
            uow.cycles.add(
                DeliveryCycle(
                    provider_id=0,
                    delivery_at=delivery_at,
                    cutoff_at=cutoff_at,
                    max_eggs=12,
                    status=DeliveryCycleStatus.OPEN,
                )
            )
            uow.commit()
