from collections.abc import Iterator

import pytest

from tests.conftest import truncate_tables


@pytest.fixture(scope="module", autouse=True)
def _truncate() -> Iterator[None]:
    truncate_tables()
    yield
    truncate_tables()
