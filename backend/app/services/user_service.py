"""사용자 서비스 — M02 USER."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """ID로 사용자 조회."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, update_data: UserUpdate) -> User:
    """사용자 프로필 수정.

    Args:
        db: DB 세션
        user: 수정할 사용자 인스턴스
        update_data: 수정 데이터 (None 필드는 무시)

    Returns:
        수정된 사용자 인스턴스
    """
    if update_data.name is not None:
        user.name = update_data.name
    if update_data.profile_image_url is not None:
        user.profile_image_url = update_data.profile_image_url

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user


async def switch_user_role(db: AsyncSession, user: User, new_role: UserRole) -> User:
    """사용자 역할 전환.

    Args:
        db: DB 세션
        user: 역할을 전환할 사용자
        new_role: 새 역할

    Returns:
        역할이 전환된 사용자

    Raises:
        ValueError: 현재 역할과 동일한 역할로 전환 시도
    """
    if user.current_role == new_role:
        raise ValueError(f"이미 '{new_role.value}' 역할입니다.")

    user.current_role = new_role
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user
