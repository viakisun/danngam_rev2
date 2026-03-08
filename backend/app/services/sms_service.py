"""SMS 발송 서비스 — M01 AUTH.

개발 환경: MockSMSService (Redis에 코드 저장 + 로그 출력)
프로덕션: CoolSMSService (실제 API 연동)
"""

import logging
import random
import string
from abc import ABC, abstractmethod

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Redis 키 패턴
OTP_KEY = "sms:otp:{phone}"
COOLDOWN_KEY = "sms:cooldown:{phone}"
FAIL_COUNT_KEY = "sms:fail:{phone}"
BLOCK_KEY = "sms:block:{phone}"

# 상수
OTP_TTL_SECONDS = 180  # 3분
COOLDOWN_SECONDS = 60  # 60초 쿨다운
MAX_FAIL_COUNT = 5  # 최대 실패 횟수
BLOCK_TTL_SECONDS = 1800  # 30분 차단


def generate_otp(length: int = 6) -> str:
    """6자리 숫자 OTP 생성."""
    return "".join(random.choices(string.digits, k=length))


def normalize_phone(phone: str) -> str:
    """전화번호 정규화: 하이픈 제거, 11자리 형식 검증."""
    normalized = phone.replace("-", "").replace(" ", "")
    if not normalized.isdigit() or len(normalized) not in (10, 11):
        raise ValueError(f"유효하지 않은 전화번호: {phone}")
    return normalized


class AbstractSMSService(ABC):
    """SMS 서비스 인터페이스."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client

    async def is_blocked(self, phone: str) -> bool:
        """전화번호 차단 여부 확인."""
        return await self.redis.exists(BLOCK_KEY.format(phone=phone)) == 1

    async def is_on_cooldown(self, phone: str) -> bool:
        """쿨다운 여부 확인."""
        return await self.redis.exists(COOLDOWN_KEY.format(phone=phone)) == 1

    async def get_fail_count(self, phone: str) -> int:
        """인증 실패 횟수 조회."""
        count = await self.redis.get(FAIL_COUNT_KEY.format(phone=phone))
        return int(count) if count else 0

    async def increment_fail_count(self, phone: str) -> int:
        """실패 횟수 증가. 5회 초과 시 차단 처리."""
        key = FAIL_COUNT_KEY.format(phone=phone)
        count = await self.redis.incr(key)
        await self.redis.expire(key, BLOCK_TTL_SECONDS)

        if count >= MAX_FAIL_COUNT:
            await self.redis.setex(BLOCK_KEY.format(phone=phone), BLOCK_TTL_SECONDS, "1")
            await self.redis.delete(key)

        return count

    async def reset_fail_count(self, phone: str) -> None:
        """인증 성공 시 실패 횟수 초기화."""
        await self.redis.delete(FAIL_COUNT_KEY.format(phone=phone))

    async def verify_otp(self, phone: str, code: str) -> bool:
        """OTP 검증. 성공 시 코드 삭제."""
        stored = await self.redis.get(OTP_KEY.format(phone=phone))
        if stored and stored == code:
            await self.redis.delete(OTP_KEY.format(phone=phone))
            await self.reset_fail_count(phone)
            return True
        return False

    async def has_otp(self, phone: str) -> bool:
        """OTP 존재 여부 (만료 여부 포함)."""
        return await self.redis.exists(OTP_KEY.format(phone=phone)) == 1

    @abstractmethod
    async def send_otp(self, phone: str) -> str:
        """OTP 발송 후 코드 반환."""
        ...


class MockSMSService(AbstractSMSService):
    """개발용 Mock SMS 서비스.

    실제 SMS 발송 없이 Redis에 OTP 저장 + 로그 출력.
    """

    async def send_otp(self, phone: str) -> str:
        """OTP를 Redis에 저장하고 로그로 출력."""
        code = generate_otp()
        otp_key = OTP_KEY.format(phone=phone)
        cooldown_key = COOLDOWN_KEY.format(phone=phone)

        await self.redis.setex(otp_key, OTP_TTL_SECONDS, code)
        await self.redis.setex(cooldown_key, COOLDOWN_SECONDS, "1")

        logger.info(f"[MOCK SMS] {phone} → OTP: {code} (유효: {OTP_TTL_SECONDS}초)")
        return code


def get_sms_service(redis_client: aioredis.Redis) -> AbstractSMSService:
    """SMS 서비스 팩토리 함수."""
    if settings.sms_provider == "mock":
        return MockSMSService(redis_client)
    raise NotImplementedError(f"SMS provider '{settings.sms_provider}' not implemented")
