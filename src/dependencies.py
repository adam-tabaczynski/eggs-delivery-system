from src.core.clock import Clock
from src.core.integrations.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.core.interfaces.unit_of_work import UnitOfWork


def get_uow() -> UnitOfWork:
    return SqlAlchemyUnitOfWork()


def get_clock() -> Clock:
    return Clock()
