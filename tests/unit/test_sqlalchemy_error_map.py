from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError, OperationalError as SAOperationalError

from src.core.integrations.sqlalchemy.errors import map_sqlalchemy_error
from src.core.exceptions import ConflictError, NotFoundError, OperationalError


def test_map_unique_violation() -> None:
    exc = IntegrityError("INSERT", {}, UniqueViolation("duplicate"))
    mapped = map_sqlalchemy_error(exc)
    assert isinstance(mapped, ConflictError)
    assert mapped.message == "Unique constraint violated"


def test_map_foreign_key_violation() -> None:
    exc = IntegrityError("INSERT", {}, ForeignKeyViolation("fk"))
    mapped = map_sqlalchemy_error(exc)
    assert isinstance(mapped, NotFoundError)
    assert mapped.message == "Referenced entity does not exist"


def test_map_other_integrity_to_operational() -> None:
    exc = IntegrityError("INSERT", {}, CheckViolation("check"))
    mapped = map_sqlalchemy_error(exc)
    assert isinstance(mapped, OperationalError)
    assert mapped.code == "internal_error"


def test_map_sqlalchemy_operational() -> None:
    mapped = map_sqlalchemy_error(SAOperationalError("SELECT", {}, Exception("down")))
    assert isinstance(mapped, OperationalError)
