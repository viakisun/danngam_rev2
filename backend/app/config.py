"""애플리케이션 설정 모듈.

pydantic-settings 기반 환경변수 관리.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전역 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 앱 정보
    app_name: str = "단감(DANNGAM)"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # 데이터베이스
    database_url: str = "postgresql+asyncpg://danngam:danngam_secret@localhost:5432/danngam"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    secret_key: str = "dev_secret_key_minimum_32_chars_change"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # SMS
    sms_provider: str = "mock"  # mock | coolsms
    coolsms_api_key: str = ""
    coolsms_api_secret: str = ""
    coolsms_sender_phone: str = ""

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        """CORS 허용 오리진 목록."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """싱글턴 설정 인스턴스 반환."""
    return Settings()


settings = get_settings()
