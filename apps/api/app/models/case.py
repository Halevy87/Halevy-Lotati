import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CaseStatus, DealType


class Case(Base):
    """The central entity. Per-step JSONB columns are nullable and filled by later slices."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # YYYY-NNNN
    status: Mapped[CaseStatus] = mapped_column(
        String, default=CaseStatus.intake_pending, nullable=False
    )
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Property
    block: Mapped[str | None] = mapped_column(String, nullable=True)  # gush
    parcel: Mapped[str | None] = mapped_column(String, nullable=True)  # chelka
    sub_parcel: Mapped[str | None] = mapped_column(String, nullable=True)  # tat chelka
    property_address: Mapped[str] = mapped_column(String, nullable=False)
    property_city: Mapped[str] = mapped_column(String, nullable=False)

    # Resolved property identifiers (Step 5.5 — Address Resolver)
    resolved_gush: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_tat_chelka: Mapped[str | None] = mapped_column(String, nullable=True)
    apartment_number_claimed: Mapped[str | None] = mapped_column(String, nullable=True)
    property_coordinates: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Deal
    deal_type: Mapped[DealType] = mapped_column(String, default=DealType.purchase, nullable=False)
    deal_value_ils: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Assigned lawyer
    primary_lawyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Counterparty
    counterparty_lawyer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    counterparty_lawyer_phone: Mapped[str | None] = mapped_column(String, nullable=True)

    # Dates
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    signing_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    handover_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Per-step data (JSONB) — filled by their respective slices
    intake_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tax_calculation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    municipal_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    identity_checks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    taboo_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    condo_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    contract_review: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    addenda_checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Computed (denormalized; recomputed by later slices)
    red_flags_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parties: Mapped[list["Party"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
    activities: Mapped[list["Activity"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
