from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
