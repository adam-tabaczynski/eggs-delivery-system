from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.integrations.sqlalchemy.errors import map_sqlalchemy_error
from src.core.integrations.sqlalchemy.session import SessionFactory
from src.core.interfaces.unit_of_work import UnitOfWork
from src.repositories.customers import SqlAlchemyCustomerRepository
from src.repositories.cycles import SqlAlchemyDeliveryCycleRepository
from src.repositories.orders import SqlAlchemyOrderRepository
from src.repositories.providers import SqlAlchemyProviderRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: Callable[[], Session] = SessionFactory) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> Self:
        self.session = self._session_factory()
        self.customers = SqlAlchemyCustomerRepository(self.session)
        self.providers = SqlAlchemyProviderRepository(self.session)
        self.cycles = SqlAlchemyDeliveryCycleRepository(self.session)
        self.orders = SqlAlchemyOrderRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Always rollback + close first. `exc` is whatever the `with` body raised
        # (or None). Mapping happens *after* cleanup so a failed rollback cannot
        # leave the session open.
        rollback_error: BaseException | None = None
        try:
            self.rollback()
        except SQLAlchemyError as rollback_exc:
            rollback_error = rollback_exc
        finally:
            if self.session is not None:
                self.session.close()
            self.session = None

        if rollback_error is not None:
            # Caller sees the *rollback* failure. If `exc` is not None, then it's set
            # as the cause, otherwise the rollback error is the cause.
            cause = exc if exc is not None else rollback_error
            raise map_sqlalchemy_error(rollback_error) from cause

        if exc is not None:
            if isinstance(exc, SQLAlchemyError):
                raise map_sqlalchemy_error(exc) from exc

        # Allow other errors to propagate as is.

    def commit(self) -> None:
        self._require_session().commit()

    def rollback(self) -> None:
        self._require_session().rollback()

    def _require_session(self) -> Session:
        if self.session is None:
            raise RuntimeError("Unit of work is not active")
        return self.session
