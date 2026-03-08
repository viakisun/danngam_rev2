"""채팅 관련 Pydantic 스키마 — M05 CHAT."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.chat import MESSAGE_MAX_LENGTH


class ChatRoomResponse(BaseModel):
    """채팅방 목록 응답."""

    id: uuid.UUID
    job_id: uuid.UUID
    requester_id: uuid.UUID
    worker_id: uuid.UUID
    created_at: datetime
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답."""

    id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    """메시지 전송 요청 (REST fallback)."""

    content: str = Field(..., min_length=1, max_length=MESSAGE_MAX_LENGTH)


class MessageListResponse(BaseModel):
    """메시지 목록 응답 (cursor-based)."""

    items: list[ChatMessageResponse]
    next_cursor: str | None


# WebSocket 메시지 스키마 (TypedDict 스타일)
class WSMessageIn(BaseModel):
    """WebSocket 수신 메시지."""

    type: str  # "message" | "ping"
    content: str | None = Field(None, max_length=MESSAGE_MAX_LENGTH)


class WSMessageOut(BaseModel):
    """WebSocket 송신 메시지."""

    type: str  # "message" | "read" | "error"
    message_id: str | None = None
    sender_id: str | None = None
    content: str | None = None
    created_at: str | None = None
    reader_id: str | None = None
    error: str | None = None
