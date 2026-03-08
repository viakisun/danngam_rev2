"""사용자 관련 Pydantic 스키마 — M02 USER."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole


class UserResponse(BaseModel):
    """사용자 프로필 응답."""

    id: uuid.UUID
    phone: str
    name: str | None
    profile_image_url: str | None
    current_role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """사용자 프로필 수정 요청."""

    name: str | None = Field(None, min_length=1, max_length=20)
    profile_image_url: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("이름에 공백만 포함될 수 없습니다.")
        return v.strip() if v else v


class RoleSwitchRequest(BaseModel):
    """역할 전환 요청."""

    role: UserRole


class RoleSwitchResponse(BaseModel):
    """역할 전환 응답."""

    current_role: UserRole
