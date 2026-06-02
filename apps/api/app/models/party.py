import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import IdentityCheckStatus, PartyRole


class Party(Base):
    """Buyer / seller / guarantor / spouse on a case.

    SECURITY: israeli_id is PLAINTEXT in Foundation. Synthetic/fake IDs only — no real
    PII. Application-layer encryption is delivered by the security/auth slice.
    """

    __tablename__ = "parties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[PartyRole] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    israeli_id: Mapped[str] = mapped_column(String, nullable=False)  # PLAINTEXT — fake only
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    identity_check_status: Mapped[IdentityCheckStatus] = mapped_column(
        String, default=IdentityCheckStatus.pending, nullable=False
    )
    identity_check_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="parties")  # noqa: F821
