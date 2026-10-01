from typing import NamedTuple, Protocol

from src.models import DeliveryCycle


class CycleWithAllocatedEggs(NamedTuple):
    cycle: DeliveryCycle
    allocated_eggs: int


class DeliveryCycleRepository(Protocol):
    def add(self, cycle: DeliveryCycle) -> DeliveryCycle: ...

    def get(self, cycle_id: int) -> DeliveryCycle | None: ...

    def get_for_update(self, cycle_id: int) -> DeliveryCycle | None: ...

    def get_allocated_eggs(
        self, cycle_id: int, *, exclude_order_id: int | None = None
    ) -> int: ...

    def list_all(self) -> list[DeliveryCycle]: ...

    def list_with_allocated_eggs_by_provider_id(
        self, provider_id: int
    ) -> list[CycleWithAllocatedEggs]: ...
