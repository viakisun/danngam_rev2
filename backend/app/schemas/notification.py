"""알림 관련 Pydantic 스키마 — M06 NOTIFY."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """알림 응답."""

    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    body: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """알림 목록 응답 (cursor-based)."""

    items: list[NotificationResponse]
    next_cursor: str | None
    unread_count: int


class FCMTokenRequest(BaseModel):
    """FCM 토큰 등록 요청."""

    token: str = Field(..., min_length=1)
    device_type: str = Field(..., pattern="^(ios|android)$")
