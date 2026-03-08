"""알림 라우터 — M06 NOTIFY.

엔드포인트:
  POST /api/v1/notifications/fcm-token  — FCM 토큰 등록
  GET  /api/v1/notifications             — 알림 목록
  POST /api/v1/notifications/{id}/read   — 읽음 처리
"""

import base64
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import FCMTokenRequest, NotificationListResponse, NotificationResponse
from app.services.notification_service import register_fcm_token

router = APIRouter(prefix="/notifications")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def _encode_cursor(dt: datetime) -> str:
    return base64.b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.b64decode(cursor.encode()).decode())


@router.post("/fcm-token", status_code=status.HTTP_200_OK, summary="FCM 디바이스 토큰 등록")
async def register_token(
    request: FCMTokenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """FCM 푸시 알림을 위한 디바이스 토큰을 등록합니다.

    TODO: Lv2 — 실제 FCM 발송 시 이 토큰 사용
    """
    await register_fcm_token(db, current_user.id, request.token, request.device_type)
    return success_response({"message": "FCM 토큰이 등록되었습니다."})


@router.get("", status_code=status.HTTP_200_OK, summary="알림 목록")
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """내 알림 목록을 최신순으로 조회합니다."""
    stmt = select(Notification).where(Notification.user_id == current_user.id)

    if cursor:
        try:
            cursor_dt = _decode_cursor(cursor)
            stmt = stmt.where(Notification.created_at < cursor_dt)
        except Exception:
            pass

    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit + 1)
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    next_cursor = None
    if len(notifications) > limit:
        notifications = notifications[:limit]
        next_cursor = _encode_cursor(notifications[-1].created_at)

    # 읽지 않은 알림 수
    unread_result = await db.execute(
        select(func.count()).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
    )
    unread_count = unread_result.scalar() or 0

    return success_response(
        NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in notifications],
            next_cursor=next_cursor,
            unread_count=unread_count,
        ).model_dump()
    )


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK, summary="알림 읽음 처리")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DNNG-NOTIFY-001", "message": "알림을 찾을 수 없습니다."}},
        )

    notification.is_read = True
    return success_response({"id": str(notification_id), "is_read": True})
