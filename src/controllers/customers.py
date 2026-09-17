from fastapi import APIRouter, Depends, status

from src.commands.customers import register_customer
from src.core.interfaces.unit_of_work import UnitOfWork
from src.dependencies import get_uow
from src.schemas import CustomerCreate, CustomerRead

router = APIRouter()


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> CustomerRead:
    return register_customer(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        uow=uow,
    )
