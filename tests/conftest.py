"""Shared pytest fixtures."""

import pytest

from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.models import Provider
from tests.helpers import unique_email


@pytest.fixture
def provider_id() -> int:
    uow = SqlAlchemyUnitOfWork()
    with uow:
        provider = Provider(name="Test Farm", email=unique_email(prefix="provider"))
        uow.providers.add(provider)
        uow.commit()
        return provider.id
