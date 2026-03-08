"""create reviews table

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-01 10:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # avg_rating 컬럼이 users 테이블에 없으면 추가
    op.add_column("users", sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"))

    op.create_table(
        "reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("reviewee_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "reviewer_id", name="uq_review_job_reviewer"),
    )
    op.create_index("ix_reviews_reviewee_id", "reviews", ["reviewee_id"])
    op.create_index("ix_reviews_job_id", "reviews", ["job_id"])


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "avg_rating")
