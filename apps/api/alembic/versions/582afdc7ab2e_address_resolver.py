"""address resolver

Revision ID: 582afdc7ab2e
Revises: 93091655a083
Create Date: 2026-06-07 01:01:20.583119
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = '582afdc7ab2e'
down_revision: str | None = '93091655a083'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "address_resolution",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("apartment_number_claimed", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("resolved_gush", sa.String(), nullable=True),
        sa.Column("resolved_chelka", sa.String(), nullable=True),
        sa.Column("resolved_tat_chelka", sa.String(), nullable=True),
        sa.Column("coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolution_time_ms", sa.Integer(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("cases", sa.Column("resolved_gush", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("resolved_chelka", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("resolved_tat_chelka", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("apartment_number_claimed", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("property_coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.alter_column("cases", "block", existing_type=sa.String(), nullable=True)
    op.alter_column("cases", "parcel", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("cases", "parcel", existing_type=sa.String(), nullable=False)
    op.alter_column("cases", "block", existing_type=sa.String(), nullable=False)
    op.drop_column("cases", "property_coordinates")
    op.drop_column("cases", "apartment_number_claimed")
    op.drop_column("cases", "resolved_tat_chelka")
    op.drop_column("cases", "resolved_chelka")
    op.drop_column("cases", "resolved_gush")
    op.drop_table("address_resolution")
