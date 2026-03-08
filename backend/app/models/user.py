"""User 모델 — M01 AUTH, M02 USER, M07 REVIEW."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, PyEnum):
    """사용자 역할."""

    REQUESTER = "requester"  # 의뢰자
    WORKER = "worker"  # 작업자


class User(Base):
    """사용자 모델.

    양방향 역할: 동일 계정이 의뢰자이면서 작업자가 될 수 있음.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    phone: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.REQUESTER,
        nullable=False,
    )
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # M07 REVIEW — 평균 평점 (후기 작성 시 자동 업데이트)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # M09 ADMIN — 관리자 권한
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone}>"
