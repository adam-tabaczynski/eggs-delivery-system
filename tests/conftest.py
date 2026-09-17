"""Shared pytest fixtures."""

import pytest

from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Customer, Provider
from tests.helpers import unique_email


@pytest.fixture
def provider_id() -> int:
    uow = SqlAlchemyUnitOfWork()
    with uow:
        provider = Provider(name="Test Farm", email=unique_email(prefix="provider"))
        uow.providers.add(provider)
        uow.commit()
        return provider.id


@pytest.fixture
def customer_id() -> int:
    uow = SqlAlchemyUnitOfWork()
    with uow:
        customer = Customer(
            first_name="Ada",
            last_name="Lovelace",
            email=unique_email(prefix="customer"),
        )
        uow.customers.add(customer)
        uow.commit()
        return customer.id
