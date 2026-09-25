"""Shared pytest helpers."""

from sqlalchemy import text

import src.models  # noqa: F401  # registers tables on Base.metadata
from src.core.integrations.sqlalchemy.base import Base
from src.core.integrations.sqlalchemy.session import engine
from src.settings import get_settings


def truncate_tables() -> None:
    # Guard against wiping the dev DB if pytest-env is not active and .env is used.
    assert get_settings().postgres_db.endswith("_test")
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
