from logging.config import fileConfig
from collections.abc import MutableMapping
from typing import Literal

from sqlalchemy import create_engine
from sqlalchemy import pool
from sqlalchemy.schema import SchemaItem

from alembic import context

from src.settings import get_settings
from src.core.integrations.sqlalchemy import Base
from src.models import Customer, Provider  # noqa: F401 — register metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

database_url = get_settings().database_url

_IncludeType = Literal[
    "schema",
    "table",
    "column",
    "index",
    "unique_constraint",
    "foreign_key_constraint",
    "check_constraint",
]


def include_name(
    name: str | None,
    type_: _IncludeType,
    parent_names: MutableMapping[
        Literal["schema_name", "table_name", "schema_qualified_table_name"],
        str | None,
    ],
) -> bool:
    # Called before reflection. False for a schema skips that schema entirely.
    if type_ == "schema":
        return name in (None, "public")
    return True


def include_object(
    object: SchemaItem,
    name: str | None,
    type_: _IncludeType,
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
