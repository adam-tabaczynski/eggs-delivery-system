"""SQLAlchemy models — domain tables added in Phase 1."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.integrations.sqlalchemy.base import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DeliveryCycleStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class DeliveryCycle(Base):
    __tablename__ = "delivery_cycles"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), index=True)
    delivery_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_eggs: Mapped[int]
    status: Mapped[DeliveryCycleStatus] = mapped_column(
        Enum(
            DeliveryCycleStatus,
            native_enum=False,
            length=16,
            values_callable=lambda members: [member.value for member in members],
        ),
        default=DeliveryCycleStatus.OPEN,
        server_default=DeliveryCycleStatus.OPEN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def effective_status(self, now: datetime) -> DeliveryCycleStatus:
        if self.status is DeliveryCycleStatus.CLOSED or now >= self.cutoff_at:
            return DeliveryCycleStatus.CLOSED
        return DeliveryCycleStatus.OPEN
