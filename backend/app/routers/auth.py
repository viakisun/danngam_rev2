"""인증 라우터 — M01 AUTH.

엔드포인트:
  POST /api/v1/auth/sms/send      — SMS OTP 발송
  POST /api/v1/auth/sms/verify    — OTP 검증 + JWT 발급
  POST /api/v1/auth/token/refresh — 액세스 토큰 갱신
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    AccessTokenResponse,
    RefreshTokenRequest,
    SMSSendRequest,
    SMSSendResponse,
    SMSVerifyRequest,
    TokenResponse,
)
from app.services.sms_service import get_sms_service
from app.utils.jwt import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth")


async def get_redis() -> aioredis.Redis:
    """Redis 클라이언트 의존성."""
    from app.config import settings

    client = await aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def success_response(data: dict) -> dict:
    """표준 성공 응답 포맷."""
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str) -> dict:
    """표준 에러 응답 포맷."""
    return {"success": False, "data": None, "error": {"code": code, "message": message}}


@router.post(
    "/sms/send",
    status_code=status.HTTP_200_OK,
    summary="SMS OTP 발송",
)
async def send_sms_code(
    request: SMSSendRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> dict:
    """SMS OTP를 발송합니다.

    - 60초 쿨다운 적용
    - 30분 차단 상태 시 거부
    """
    sms_service = get_sms_service(redis)
    phone = request.phone

    # 차단 확인
    if await sms_service.is_blocked(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("DNNG-AUTH-003", "인증 실패 5회로 30분간 차단되었습니다."),
        )

    # 쿨다운 확인
    if await sms_service.is_on_cooldown(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("DNNG-AUTH-002", "60초 후 다시 시도해주세요."),
        )

    await sms_service.send_otp(phone)

    return success_response(SMSSendResponse().model_dump())


@router.post(
    "/sms/verify",
    status_code=status.HTTP_200_OK,
    summary="SMS OTP 검증 및 JWT 발급",
)
async def verify_sms_code(
    request: SMSVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> dict:
    """OTP를 검증하고 JWT 토큰을 발급합니다.

    - 신규 사용자: is_new_user=true
    - 기존 사용자: is_new_user=false
    """
    sms_service = get_sms_service(redis)
    phone = request.phone

    # 차단 확인
    if await sms_service.is_blocked(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("DNNG-AUTH-003", "인증 실패 5회로 30분간 차단되었습니다."),
        )

    # OTP 존재 여부 확인
    if not await sms_service.has_otp(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("DNNG-AUTH-005", "인증 코드가 만료되었습니다. 다시 요청해주세요."),
        )

    # OTP 검증
    is_valid = await sms_service.verify_otp(phone, request.code)
    if not is_valid:
        fail_count = await sms_service.increment_fail_count(phone)
        remaining = max(0, 5 - fail_count)

        if fail_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response("DNNG-AUTH-003", "인증 실패 5회로 30분간 차단되었습니다."),
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                "DNNG-AUTH-004",
                f"인증 코드가 일치하지 않습니다. (남은 시도: {remaining}회)",
            ),
        )

    # 사용자 조회 또는 생성
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    is_new_user = user is None

    if user is None:
        user = User(
            id=uuid.uuid4(),
            phone=phone,
            current_role=UserRole.REQUESTER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush()

    # JWT 발급
    access_token = create_access_token(str(user.id), user.current_role.value)
    refresh_token = create_refresh_token(str(user.id))

    # refresh_token DB 저장
    user.refresh_token = refresh_token
    user.updated_at = datetime.now(timezone.utc)

    return success_response(
        TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            is_new_user=is_new_user,
        ).model_dump()
    )


@router.post(
    "/token/refresh",
    status_code=status.HTTP_200_OK,
    summary="액세스 토큰 갱신",
)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """리프레시 토큰으로 새 액세스 토큰을 발급합니다."""
    payload = verify_token(request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("DNNG-AUTH-008", "유효하지 않은 리프레시 토큰입니다."),
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("DNNG-AUTH-007", "만료된 리프레시 토큰입니다."),
        )

    if user.refresh_token != request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("DNNG-AUTH-007", "만료된 리프레시 토큰입니다."),
        )

    new_access_token = create_access_token(str(user.id), user.current_role.value)

    return success_response(
        AccessTokenResponse(access_token=new_access_token).model_dump()
    )
