import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AddressResolution(Base):
    """One address→gush/chelka resolution attempt (audit + retry history). Step 5.5."""

    __tablename__ = "address_resolution"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    # Inputs actually used
    city: Mapped[str] = mapped_column(String, nullable=False)
    street: Mapped[str] = mapped_column(String, nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    apartment_number_claimed: Mapped[str | None] = mapped_column(String, nullable=True)
    # Outputs
    status: Mapped[str] = mapped_column(String, nullable=False)
    resolved_gush: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_tat_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Metadata
    method: Mapped[str] = mapped_column(String, nullable=False, default="rest")
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
