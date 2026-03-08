"""FastAPI 의존성 주입 함수 모음."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    """JWT 토큰을 검증하고 현재 사용자를 반환하는 의존성.

    M01 AUTH 모듈 구현 후 완성됨.
    """
    from app.models.user import User
    from app.utils.jwt import verify_token

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "DNNG-AUTH-008",
                "message": "유효하지 않은 토큰입니다.",
            },
        )

    from sqlalchemy import select

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "DNNG-AUTH-008",
                "message": "사용자를 찾을 수 없습니다.",
            },
        )

    return user
