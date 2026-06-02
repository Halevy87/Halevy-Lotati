import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IdentityCheckStatus, PartyRole


class PartyCreate(BaseModel):
    role: PartyRole
    full_name: str
    israeli_id: str  # synthetic/fake only in Foundation
    phone: str | None = None
    email: str | None = None


class PartyUpdate(BaseModel):
    role: PartyRole | None = None
    full_name: str | None = None
    israeli_id: str | None = None
    phone: str | None = None
    email: str | None = None
    identity_check_status: IdentityCheckStatus | None = None


class PartyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    role: PartyRole
    full_name: str
    israeli_id: str
    phone: str | None
    email: str | None
    identity_check_status: IdentityCheckStatus
    created_at: datetime
