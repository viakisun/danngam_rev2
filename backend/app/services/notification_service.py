"""알림 서비스 — M06 NOTIFY.

FCM 실제 발송은 Lv2에서 구현 예정 (Firebase Admin SDK).
현재는 DB 저장 + 로그 출력만 수행.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import FCMToken, Notification, NotificationType

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    body: str,
) -> Notification:
    """알림 DB 저장 + 푸시 발송 (stub)."""
    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()

    # 푸시 발송 (stub)
    await send_push(db, user_id, title, body)

    return notification


async def send_push(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
) -> None:
    """FCM 푸시 발송.

    TODO: Lv2 — Firebase Admin SDK 연동
    현재: 로그 출력만 수행. FCM 토큰이 있는 경우에만 발송 예정.
    """
    # FCM 토큰 조회
    result = await db.execute(
        select(FCMToken).where(FCMToken.user_id == user_id)
    )
    tokens = result.scalars().all()

    if not tokens:
        logger.debug(f"[NOTIFY] user={user_id} FCM 토큰 없음 → 발송 스킵")
        return

    for token_obj in tokens:
        # TODO: Lv2 — Firebase Admin SDK로 실제 발송
        # messaging.send(Message(notification=Notification(title=title, body=body), token=token))
        logger.info(
            f"[NOTIFY stub] user={user_id} device={token_obj.device_type} "
            f"title='{title}' body='{body}'"
        )


async def register_fcm_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    device_type: str,
) -> FCMToken:
    """FCM 토큰 등록 (기존 토큰 업데이트 or 신규 생성)."""
    existing = await db.execute(
        select(FCMToken).where(FCMToken.token == token)
    )
    fcm_token = existing.scalar_one_or_none()

    if fcm_token is None:
        fcm_token = FCMToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token=token,
            device_type=device_type,
            created_at=datetime.now(timezone.utc),
        )
        db.add(fcm_token)
    else:
        fcm_token.user_id = user_id
        fcm_token.device_type = device_type

    await db.flush()
    return fcm_token
