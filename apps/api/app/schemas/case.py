import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CaseStatus, DealType
from app.schemas.activity import ActivityOut
from app.schemas.party import PartyCreate, PartyOut


class CaseCreate(BaseModel):
    deal_type: DealType = DealType.purchase
    block: str
    parcel: str
    sub_parcel: str | None = None
    property_address: str
    property_city: str
    deal_value_ils: int | None = None
    primary_lawyer_id: uuid.UUID | None = None
    counterparty_lawyer_name: str | None = None
    counterparty_lawyer_phone: str | None = None
    # Optional first party (the primary client) created together with the case.
    primary_client: PartyCreate | None = None


class CaseUpdate(BaseModel):
    status: CaseStatus | None = None
    current_step: int | None = None
    deal_type: DealType | None = None
    block: str | None = None
    parcel: str | None = None
    sub_parcel: str | None = None
    property_address: str | None = None
    property_city: str | None = None
    deal_value_ils: int | None = None
    primary_lawyer_id: uuid.UUID | None = None
    counterparty_lawyer_name: str | None = None
    counterparty_lawyer_phone: str | None = None


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_number: str
    status: CaseStatus
    current_step: int
    property_address: str
    property_city: str
    deal_type: DealType
    red_flags_count: int
    completion_percentage: int
    primary_lawyer_id: uuid.UUID | None
    opened_at: datetime


class CaseDetail(CaseListItem):
    block: str
    parcel: str
    sub_parcel: str | None
    deal_value_ils: int | None
    counterparty_lawyer_name: str | None
    counterparty_lawyer_phone: str | None
    signing_scheduled_at: datetime | None
    handover_scheduled_at: datetime | None
    parties: list[PartyOut] = []
    activities: list[ActivityOut] = []


class CaseList(BaseModel):
    items: list[CaseListItem]
    total: int
    page: int
    page_size: int
