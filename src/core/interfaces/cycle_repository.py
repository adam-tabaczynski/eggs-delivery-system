from typing import Protocol

from src.models import DeliveryCycle


class DeliveryCycleRepository(Protocol):
    def add(self, cycle: DeliveryCycle) -> DeliveryCycle: ...

    def list_by_provider_id(self, provider_id: int) -> list[DeliveryCycle]: ...
