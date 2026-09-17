import pytest

from src.commands.customers import register_customer
from src.exceptions import EmailAlreadyRegistered
from tests.fakes import FakeUnitOfWork


def test_register_customer_commits() -> None:
    uow = FakeUnitOfWork()
    result = register_customer(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        uow=uow,
    )
    assert result.email == "ada@example.com"
    assert result.first_name == "Ada"
    assert result.last_name == "Lovelace"
    assert result.id == 1
    assert uow.committed
    assert uow.customers.get_by_email("ada@example.com") is not None


def test_register_customer_duplicate_email() -> None:
    uow = FakeUnitOfWork()
    register_customer(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        uow=uow,
    )
    with pytest.raises(EmailAlreadyRegistered, match="Email already registered"):
        register_customer(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            uow=uow,
        )
