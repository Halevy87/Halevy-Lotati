import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResolveAddressRequest(BaseModel):
    # All optional: missing street/number are parsed from the case's property_address.
    street: str | None = None
    number: str | None = None
    apartment_number_claimed: str | None = None


class ManualResolutionRequest(BaseModel):
    gush: str
    chelka: str
    tat_chelka: str | None = None


class AddressResolutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    city: str
    street: str
    number: str
    apartment_number_claimed: str | None
    status: str
    resolved_gush: str | None
    resolved_chelka: str | None
    resolved_tat_chelka: str | None
    coordinates: dict | None
    method: str
    resolution_time_ms: int
    resolved_at: datetime
