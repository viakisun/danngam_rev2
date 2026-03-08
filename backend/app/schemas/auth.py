"""인증 관련 Pydantic 스키마 — M01 AUTH."""

from pydantic import BaseModel, field_validator


class SMSSendRequest(BaseModel):
    """SMS 발송 요청."""

    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        from app.services.sms_service import normalize_phone

        try:
            return normalize_phone(v)
        except ValueError as e:
            raise ValueError(str(e)) from e


class SMSSendResponse(BaseModel):
    """SMS 발송 응답."""

    cooldown_seconds: int = 60


class SMSVerifyRequest(BaseModel):
    """SMS OTP 검증 요청."""

    phone: str
    code: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        from app.services.sms_service import normalize_phone

        try:
            return normalize_phone(v)
        except ValueError as e:
            raise ValueError(str(e)) from e

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("코드는 6자리 숫자여야 합니다.")
        return v


class TokenResponse(BaseModel):
    """JWT 토큰 응답."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool


class RefreshTokenRequest(BaseModel):
    """리프레시 토큰 갱신 요청."""

    refresh_token: str


class AccessTokenResponse(BaseModel):
    """새 액세스 토큰 응답."""

    access_token: str
    token_type: str = "bearer"
