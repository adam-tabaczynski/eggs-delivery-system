from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models import DeliveryCycle, DeliveryCycleStatus


class CustomerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    updated_at: datetime


class DeliveryCycleCreate(BaseModel):
    delivery_at: datetime
    cutoff_at: datetime
    max_eggs: int = Field(ge=1)

    @field_validator("delivery_at", "cutoff_at")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("must be timezone-aware")
        return value

    @model_validator(mode="after")
    def cutoff_before_delivery(self) -> "DeliveryCycleCreate":
        if self.cutoff_at >= self.delivery_at:
            raise ValueError("cutoff_at must be before delivery_at")
        return self


class DeliveryCycleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[DeliveryCycleStatus.CLOSED]


class DeliveryCycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    delivery_at: datetime
    cutoff_at: datetime
    max_eggs: int
    status: DeliveryCycleStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: DeliveryCycle, *, now: datetime) -> Self:
        return cls.model_validate(model).model_copy(
            update={"status": model.effective_status(now)}
        )
