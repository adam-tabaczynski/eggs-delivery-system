from fastapi import APIRouter, Depends, status

from src.commands.cycles import create_delivery_cycle, update_delivery_cycle
from src.core.interfaces.unit_of_work import UnitOfWork
from src.dependencies import get_uow
from src.queries.cycles import list_cycles_for_provider
from src.schemas import DeliveryCycleCreate, DeliveryCycleRead, DeliveryCycleUpdate

router = APIRouter()


@router.post(
    "/providers/{provider_id}/cycles",
    status_code=status.HTTP_201_CREATED,
)
def create_cycle(
    provider_id: int,
    body: DeliveryCycleCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveryCycleRead:
    return create_delivery_cycle(
        provider_id=provider_id,
        delivery_at=body.delivery_at,
        cutoff_at=body.cutoff_at,
        max_eggs=body.max_eggs,
        uow=uow,
    )


@router.get("/providers/{provider_id}/cycles")
def list_cycles(
    provider_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[DeliveryCycleRead]:
    return list_cycles_for_provider(provider_id=provider_id, uow=uow)


@router.patch("/providers/{provider_id}/cycles/{cycle_id}")
def update_cycle(
    provider_id: int,
    cycle_id: int,
    body: DeliveryCycleUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> DeliveryCycleRead:
    return update_delivery_cycle(
        provider_id=provider_id,
        cycle_id=cycle_id,
        uow=uow,
    )
