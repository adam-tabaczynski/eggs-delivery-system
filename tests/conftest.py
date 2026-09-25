"""Shared pytest fixtures."""

import pytest
from sqlalchemy import text

import src.models  # noqa: F401  # registers tables on Base.metadata
from src.core.integrations.sqlalchemy.base import Base
from src.core.integrations.sqlalchemy.session import engine
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Customer, Provider
from src.settings import get_settings
from tests.helpers import unique_email


def truncate_tables() -> None:
    # Guard against wiping the dev DB if pytest-env is not active and .env is used.
    assert get_settings().postgres_db.endswith("_test")
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


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
