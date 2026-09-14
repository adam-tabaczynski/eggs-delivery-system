from sqlalchemy.orm import Session

from src.core.interfaces.provider_repository import ProviderRepository
from src.models import Provider


class SqlAlchemyProviderRepository(ProviderRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, provider_id: int) -> Provider | None:
        return self.session.get(Provider, provider_id)

    def add(self, provider: Provider) -> Provider:
        self.session.add(provider)
        self.session.flush()
        self.session.refresh(provider)
        return provider
