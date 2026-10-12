from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import truncate_tables


@pytest.fixture(scope="module", autouse=True)
def _truncate() -> Iterator[None]:
    truncate_tables()
    yield
    truncate_tables()


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
