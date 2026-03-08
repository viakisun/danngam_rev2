"""알림 모델 — M06 NOTIFY."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, PyEnum):
    """알림 유형."""

    JOB_APPLICATION = "job_application"  # 작업 지원
    JOB_MATCHED = "job_matched"  # 매칭 완료
    CHAT_MESSAGE = "chat_message"  # 채팅 메시지
    REVIEW_RECEIVED = "review_received"  # 후기 수신
    SYSTEM = "system"  # 시스템 공지


class Notification(Base):
    """알림 모델."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.type} user_id={self.user_id}>"


class FCMToken(Base):
    """FCM 디바이스 토큰 — TODO: Lv2 Firebase 연동 시 활성화."""

    __tablename__ = "fcm_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ios | android
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
