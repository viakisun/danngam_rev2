"""create drying tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-01 10:10:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drying_facilities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("operator_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location_address", sa.String(200), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=False),
        sa.Column("location_lng", sa.Float(), nullable=False),
        sa.Column("capacity_kg", sa.Integer(), nullable=False),
        sa.Column("available_crops", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drying_facilities_operator_id", "drying_facilities", ["operator_id"])

    op.create_table(
        "drying_reservations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("facility_id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("input_kg", sa.Integer(), nullable=False),
        sa.Column("output_kg", sa.Integer(), nullable=True),
        sa.Column("yield_pct", sa.Float(), nullable=True),
        sa.Column("moisture_pct", sa.Float(), nullable=True),
        sa.Column("color_grade", sa.String(10), nullable=True),
        sa.Column("quality_grade", sa.String(10), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["drying_facilities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drying_reservations_facility_id", "drying_reservations", ["facility_id"])
    op.create_index("ix_drying_reservations_requester_id", "drying_reservations", ["requester_id"])


def downgrade() -> None:
    op.drop_table("drying_reservations")
    op.drop_table("drying_facilities")
