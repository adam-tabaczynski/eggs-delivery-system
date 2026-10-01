from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import CustomerNotFound, CycleNotFound, ProviderNotFound
from src.models import OrderStatus
from src.schemas import OrderRead


def list_orders_for_customer(
    *,
    customer_id: int,
    status: OrderStatus | None = None,
    uow: UnitOfWork,
) -> list[OrderRead]:
    with uow:
        if uow.customers.get(customer_id) is None:
            raise CustomerNotFound()
        orders = uow.orders.list_by_customer_id(customer_id, status=status)
        return [OrderRead.model_validate(order) for order in orders]


def list_orders_for_cycle(
    *,
    provider_id: int,
    cycle_id: int,
    status: OrderStatus | None = None,
    uow: UnitOfWork,
) -> list[OrderRead]:
    with uow:
        if uow.providers.get(provider_id) is None:
            raise ProviderNotFound()
        cycle = uow.cycles.get(cycle_id)
        if cycle is None or cycle.provider_id != provider_id:
            raise CycleNotFound()
        orders = uow.orders.list_by_cycle_id(cycle_id, status=status)
        return [OrderRead.model_validate(order) for order in orders]
