from datetime import datetime
from typing import NamedTuple, Protocol

from src.models import DeliveryCycle, DeliveryCycleStatus


class CycleWithAllocatedEggs(NamedTuple):
    cycle: DeliveryCycle
    allocated_eggs: int


class DeliveryCycleRepository(Protocol):
    def add(self, cycle: DeliveryCycle) -> DeliveryCycle: ...

    def get(self, cycle_id: int) -> DeliveryCycle | None: ...

    def get_for_update(self, cycle_id: int) -> DeliveryCycle | None: ...

    def refresh(self, cycle: DeliveryCycle) -> DeliveryCycle: ...

    def close_if_open(self, cycle: DeliveryCycle, *, now: datetime) -> bool: ...

    def update(
        self, cycle: DeliveryCycle, *, status: DeliveryCycleStatus
    ) -> DeliveryCycle: ...

    def get_allocated_eggs(
        self, cycle_id: int, *, exclude_order_id: int | None = None
    ) -> int: ...

    def list_all_with_allocated_eggs(self) -> list[CycleWithAllocatedEggs]: ...

    def list_with_allocated_eggs_by_provider_id(
        self, provider_id: int
    ) -> list[CycleWithAllocatedEggs]: ...
