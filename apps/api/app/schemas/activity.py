import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActivityType


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID | None
    type: ActivityType
    description: str
    metadata: dict | None = Field(default=None, validation_alias="activity_metadata")
    created_at: datetime
