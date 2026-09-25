import pytest

from src.commands.customers import register_customer
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.exceptions import EmailAlreadyRegistered
from tests.generators import make_customer


class TestRegisterCustomer:
    def test_registers_customer(self) -> None:
        first_name = "Ada"
        last_name = "Lovelace"
        email = "ada@example.com"

        result = register_customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            uow=SqlAlchemyUnitOfWork(),
        )

        assert result.first_name == first_name
        assert result.last_name == last_name
        assert result.email == email

    def test_duplicate_email(self) -> None:
        existing = make_customer(email="grace@example.com")

        with pytest.raises(EmailAlreadyRegistered):
            register_customer(
                first_name="Grace",
                last_name="Hopper",
                email=existing.email,
                uow=SqlAlchemyUnitOfWork(),
            )
