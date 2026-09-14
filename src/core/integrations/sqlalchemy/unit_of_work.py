from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from src.core.integrations.sqlalchemy.session import SessionFactory
from src.core.interfaces.unit_of_work import UnitOfWork
from src.repositories.customers import SqlAlchemyCustomerRepository
from src.repositories.cycles import SqlAlchemyDeliveryCycleRepository
from src.repositories.providers import SqlAlchemyProviderRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self, session_factory: Callable[[], Session] = SessionFactory
    ) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> Self:
        self.session = self._session_factory()
        self.customers = SqlAlchemyCustomerRepository(self.session)
        self.providers = SqlAlchemyProviderRepository(self.session)
        self.cycles = SqlAlchemyDeliveryCycleRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            self.rollback()
        finally:
            if self.session is not None:
                self.session.close()
            self.session = None

    def commit(self) -> None:
        self._require_session().commit()

    def rollback(self) -> None:
        self._require_session().rollback()

    def _require_session(self) -> Session:
        if self.session is None:
            raise RuntimeError("Unit of work is not active")
        return self.session
