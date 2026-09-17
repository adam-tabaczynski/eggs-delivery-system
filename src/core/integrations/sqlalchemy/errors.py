from psycopg.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import ConflictError, NotFoundError, OperationalError


def map_sqlalchemy_error(
    exc: BaseException,
) -> ConflictError | NotFoundError | OperationalError:
    if isinstance(exc, IntegrityError):
        orig = exc.orig
        if isinstance(orig, UniqueViolation):
            return ConflictError("Unique constraint violated")
        if isinstance(orig, ForeignKeyViolation):
            return NotFoundError("Referenced entity does not exist")
    return OperationalError()
