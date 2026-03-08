"""사용자 라우터 — M02 USER.

엔드포인트:
  GET  /api/v1/users/me             — 내 프로필 조회
  PUT  /api/v1/users/me             — 내 프로필 수정
  POST /api/v1/users/me/role-switch — 역할 전환
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import RoleSwitchRequest, RoleSwitchResponse, UserResponse, UserUpdate
from app.services.user_service import switch_user_role, update_user

router = APIRouter(prefix="/users")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str) -> dict:
    return {"success": False, "data": None, "error": {"code": code, "message": message}}


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="내 프로필 조회",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """인증된 사용자의 프로필을 반환합니다."""
    return success_response(UserResponse.model_validate(current_user).model_dump())


@router.put(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="내 프로필 수정",
)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """이름, 프로필 이미지 URL을 수정합니다."""
    updated = await update_user(db, current_user, update_data)
    return success_response(UserResponse.model_validate(updated).model_dump())


@router.post(
    "/me/role-switch",
    status_code=status.HTTP_200_OK,
    summary="역할 전환 (의뢰자 ↔ 작업자)",
)
async def switch_role(
    request: RoleSwitchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """사용자 역할을 전환합니다.

    동일 계정이 의뢰자와 작업자 역할을 모두 수행할 수 있습니다.
    """
    try:
        updated = await switch_user_role(db, current_user, request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                "DNNG-USER-002",
                f"이미 '{request.role.value}' 역할입니다.",
            ),
        )

    return success_response(RoleSwitchResponse(current_role=updated.current_role).model_dump())
