from typing import Protocol

from src.models import Provider


class ProviderRepository(Protocol):
    def get(self, provider_id: int) -> Provider | None: ...

    def add(self, provider: Provider) -> Provider: ...
