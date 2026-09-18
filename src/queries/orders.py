from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import CustomerNotFound
from src.schemas import OrderRead


def list_orders_for_customer(
    *,
    customer_id: int,
    uow: UnitOfWork,
) -> list[OrderRead]:
    with uow:
        if uow.customers.get(customer_id) is None:
            raise CustomerNotFound()
        orders = uow.orders.list_by_customer_id(customer_id)
        return [OrderRead.model_validate(order) for order in orders]
