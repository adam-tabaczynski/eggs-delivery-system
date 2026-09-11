from sqlalchemy.exc import IntegrityError

from src.core.interfaces.unit_of_work import UnitOfWork
from src.exceptions import ConflictError
from src.models import Customer
from src.schemas import CustomerRead


def register_customer(
    *,
    first_name: str,
    last_name: str,
    email: str,
    uow: UnitOfWork,
) -> CustomerRead:
    try:
        with uow:
            if uow.customers.get_by_email(email) is not None:
                raise ConflictError("Email already registered")
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            uow.customers.add(customer)
            uow.commit()
            return CustomerRead.model_validate(customer)
    except IntegrityError as exc:
        raise ConflictError("Email already registered") from exc
