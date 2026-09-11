import pytest
from sqlalchemy import select

from src.core.integrations.sqlalchemy import SessionFactory, SqlAlchemyUnitOfWork
from src.models import Customer
from tests.helpers import unique_email


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
