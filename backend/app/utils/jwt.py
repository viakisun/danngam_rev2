"""JWT 발급/검증 유틸리티 — M01 AUTH."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


def create_access_token(user_id: str, role: str) -> str:
    """액세스 토큰 생성.

    Args:
        user_id: 사용자 UUID 문자열
        role: 현재 역할 ("requester" | "worker")

    Returns:
        JWT 액세스 토큰 문자열
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str) -> str:
    """리프레시 토큰 생성.

    Args:
        user_id: 사용자 UUID 문자열

    Returns:
        JWT 리프레시 토큰 문자열
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict[str, Any] | None:
    """JWT 토큰 검증.

    Args:
        token: JWT 토큰 문자열

    Returns:
        페이로드 딕셔너리 또는 None (유효하지 않은 경우)
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
