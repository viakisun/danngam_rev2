"""채팅 REST 라우터 + WebSocket — M05 CHAT.

REST 엔드포인트:
  GET  /api/v1/chat/rooms                         — 채팅방 목록
  GET  /api/v1/chat/rooms/{room_id}/messages      — 메시지 히스토리
  POST /api/v1/chat/rooms/{room_id}/read          — 읽음 처리

WebSocket:
  WS   /ws/chat/{room_id}?token={access_token}   — 실시간 채팅
"""

import base64
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.dependencies import get_current_user
from app.models.chat import MESSAGE_MAX_LENGTH, ChatMessage, ChatRoom
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRoomResponse,
    MessageListResponse,
    WSMessageIn,
    WSMessageOut,
)
from app.utils.jwt import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat")


# ===== WebSocket 연결 관리 =====

class ConnectionManager:
    """WebSocket 연결 풀 관리."""

    def __init__(self) -> None:
        # room_id → {user_id: WebSocket}
        self.active: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        if room_id not in self.active:
            self.active[room_id] = {}
        self.active[room_id][user_id] = ws

    def disconnect(self, room_id: str, user_id: str) -> None:
        if room_id in self.active:
            self.active[room_id].pop(user_id, None)
            if not self.active[room_id]:
                del self.active[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude_user_id: str | None = None) -> None:
        if room_id not in self.active:
            return
        dead = []
        for uid, ws in self.active[room_id].items():
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.active[room_id].pop(uid, None)

    async def send_to(self, room_id: str, user_id: str, message: dict) -> None:
        ws = self.active.get(room_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                self.disconnect(room_id, user_id)


manager = ConnectionManager()


# ===== 헬퍼 =====

def _encode_cursor(dt: datetime) -> str:
    return base64.b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.b64decode(cursor.encode()).decode())


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


# ===== REST 엔드포인트 =====

@router.get("/rooms", status_code=status.HTTP_200_OK, summary="채팅방 목록")
async def list_chat_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """내가 참여한 채팅방 목록."""
    result = await db.execute(
        select(ChatRoom).where(
            (ChatRoom.requester_id == current_user.id)
            | (ChatRoom.worker_id == current_user.id)
        ).order_by(ChatRoom.created_at.desc())
    )
    rooms = result.scalars().all()

    items = []
    for room in rooms:
        # 마지막 메시지
        msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        # 읽지 않은 메시지 수
        unread_result = await db.execute(
            select(ChatMessage).where(
                and_(
                    ChatMessage.room_id == room.id,
                    ChatMessage.sender_id != current_user.id,
                    ChatMessage.is_read.is_(False),
                )
            )
        )
        unread_count = len(unread_result.scalars().all())

        room_resp = ChatRoomResponse.model_validate(room)
        if last_msg:
            room_resp.last_message = last_msg.content
            room_resp.last_message_at = last_msg.created_at
        room_resp.unread_count = unread_count
        items.append(room_resp.model_dump())

    return success_response({"items": items})


@router.get("/rooms/{room_id}/messages", status_code=status.HTTP_200_OK, summary="메시지 히스토리")
async def get_messages(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
) -> dict:
    """채팅방 메시지 히스토리 (cursor-based, 최신순)."""
    # 참여자 확인
    room_result = await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
    room = room_result.scalar_one_or_none()
    if room is None or (current_user.id not in (room.requester_id, room.worker_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "DNNG-CHAT-002", "message": "채팅방 접근 권한이 없습니다."}},
        )

    stmt = select(ChatMessage).where(ChatMessage.room_id == room_id)
    if cursor:
        try:
            cursor_dt = _decode_cursor(cursor)
            stmt = stmt.where(ChatMessage.created_at < cursor_dt)
        except Exception:
            pass

    stmt = stmt.order_by(ChatMessage.created_at.desc()).limit(limit + 1)
    result = await db.execute(stmt)
    messages = result.scalars().all()

    next_cursor = None
    if len(messages) > limit:
        messages = messages[:limit]
        next_cursor = _encode_cursor(messages[-1].created_at)

    return success_response(
        MessageListResponse(
            items=[ChatMessageResponse.model_validate(m) for m in messages],
            next_cursor=next_cursor,
        ).model_dump()
    )


@router.post("/rooms/{room_id}/read", status_code=status.HTTP_200_OK, summary="읽음 처리")
async def mark_as_read(
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """채팅방의 읽지 않은 메시지를 모두 읽음 처리합니다."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(ChatMessage)
        .where(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.sender_id != current_user.id,
                ChatMessage.is_read.is_(False),
            )
        )
        .values(is_read=True, read_at=now)
        .returning(ChatMessage.id)
    )
    read_ids = result.scalars().all()
    return success_response({"read_count": len(read_ids)})


# ===== WebSocket 엔드포인트 =====

@router.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: uuid.UUID,
    token: str = Query(...),
) -> None:
    """실시간 채팅 WebSocket.

    연결: ws://host/api/v1/chat/ws/chat/{room_id}?token={access_token}
    """
    # JWT 검증
    payload = verify_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    room_id_str = str(room_id)

    async with AsyncSessionLocal() as db:
        # 채팅방 참여자 확인
        room_result = await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
        room = room_result.scalar_one_or_none()

        if room is None:
            await websocket.close(code=4004, reason="Room not found")
            return

        if str(room.requester_id) != user_id and str(room.worker_id) != user_id:
            await websocket.close(code=4003, reason="Not a participant")
            return

        await manager.connect(room_id_str, user_id, websocket)
        logger.info(f"WebSocket connected: room={room_id_str} user={user_id}")

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = WSMessageIn.model_validate_json(raw)
                except Exception:
                    await websocket.send_text(
                        json.dumps({"type": "error", "error": "잘못된 메시지 형식입니다."})
                    )
                    continue

                if data.type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue

                if data.type == "message":
                    content = data.content or ""
                    if len(content) > MESSAGE_MAX_LENGTH:
                        await websocket.send_text(
                            json.dumps({"type": "error", "error": f"메시지는 {MESSAGE_MAX_LENGTH}자를 초과할 수 없습니다."})
                        )
                        continue

                    # DB 저장
                    msg = ChatMessage(
                        id=uuid.uuid4(),
                        room_id=room_id,
                        sender_id=uuid.UUID(user_id),
                        content=content,
                        is_read=False,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(msg)
                    await db.commit()
                    await db.refresh(msg)

                    # 브로드캐스트
                    out = WSMessageOut(
                        type="message",
                        message_id=str(msg.id),
                        sender_id=user_id,
                        content=content,
                        created_at=msg.created_at.isoformat(),
                    )
                    await manager.broadcast(room_id_str, out.model_dump())

        except WebSocketDisconnect:
            manager.disconnect(room_id_str, user_id)
            logger.info(f"WebSocket disconnected: room={room_id_str} user={user_id}")
