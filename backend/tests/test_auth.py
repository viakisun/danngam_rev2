"""M01 AUTH 테스트 (TC01~TC07)."""

from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.services.sms_service import (
    BLOCK_KEY,
    COOLDOWN_KEY,
    FAIL_COUNT_KEY,
    OTP_KEY,
)

# 테스트 DB (SQLite in-memory)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, fake_redis):
    async def override_db():
        yield db_session

    async def override_redis():
        yield fake_redis

    from app.routers.auth import get_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


VALID_PHONE = "01012345678"


class TestTC01_SMSSend:
    """TC01: SMS 정상 발송."""

    async def test_send_sms_success(self, client, fake_redis):
        response = await client.post(
            "/api/v1/auth/sms/send",
            json={"phone": VALID_PHONE},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cooldown_seconds"] == 60
        # Redis에 OTP 저장 확인
        otp = await fake_redis.get(OTP_KEY.format(phone=VALID_PHONE))
        assert otp is not None
        assert len(otp) == 6
        assert otp.isdigit()


class TestTC02_Cooldown:
    """TC02: 쿨다운 중 재발송."""

    async def test_send_sms_cooldown(self, client, fake_redis):
        # 첫 번째 발송
        await client.post("/api/v1/auth/sms/send", json={"phone": VALID_PHONE})
        # 쿨다운 중 재발송
        response = await client.post(
            "/api/v1/auth/sms/send",
            json={"phone": VALID_PHONE},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "DNNG-AUTH-002"


class TestTC03_VerifyOTP:
    """TC03: OTP 정상 인증."""

    async def test_verify_otp_success(self, client, fake_redis):
        # SMS 발송
        await client.post("/api/v1/auth/sms/send", json={"phone": VALID_PHONE})
        # Redis에서 OTP 조회
        otp = await fake_redis.get(OTP_KEY.format(phone=VALID_PHONE))

        response = await client.post(
            "/api/v1/auth/sms/verify",
            json={"phone": VALID_PHONE, "code": otp},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["is_new_user"] is True


class TestTC04_WrongOTP:
    """TC04: 잘못된 OTP."""

    async def test_wrong_otp(self, client, fake_redis):
        await client.post("/api/v1/auth/sms/send", json={"phone": VALID_PHONE})

        response = await client.post(
            "/api/v1/auth/sms/verify",
            json={"phone": VALID_PHONE, "code": "000000"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "DNNG-AUTH-004"


class TestTC05_ExpiredOTP:
    """TC05: 만료 OTP (OTP 없이 검증 시도)."""

    async def test_expired_otp(self, client, fake_redis):
        # OTP 없이 바로 검증 시도 (만료 상황 시뮬레이션)
        phone = "01099998888"
        response = await client.post(
            "/api/v1/auth/sms/verify",
            json={"phone": phone, "code": "123456"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "DNNG-AUTH-005"


class TestTC06_BlockAfterFiveFailures:
    """TC06: 5회 실패 → 차단."""

    async def test_block_after_five_failures(self, client, fake_redis):
        phone = "01077776666"
        # SMS 발송
        await client.post("/api/v1/auth/sms/send", json={"phone": phone})

        # 5회 틀린 코드 시도
        for _ in range(4):
            resp = await client.post(
                "/api/v1/auth/sms/verify",
                json={"phone": phone, "code": "000000"},
            )
            assert resp.status_code == 400
            assert resp.json()["detail"]["error"]["code"] == "DNNG-AUTH-004"

        # 5번째 실패 → 차단
        resp = await client.post(
            "/api/v1/auth/sms/verify",
            json={"phone": phone, "code": "000000"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "DNNG-AUTH-003"

        # 차단 후 SMS 발송도 거부
        send_resp = await client.post(
            "/api/v1/auth/sms/send",
            json={"phone": phone},
        )
        assert send_resp.status_code == 400
        assert send_resp.json()["detail"]["error"]["code"] == "DNNG-AUTH-003"


class TestTC07_RefreshToken:
    """TC07: refresh_token으로 access_token 갱신."""

    async def test_refresh_token(self, client, fake_redis):
        phone = "01055554444"
        # 인증
        await client.post("/api/v1/auth/sms/send", json={"phone": phone})
        otp = await fake_redis.get(OTP_KEY.format(phone=phone))
        verify_resp = await client.post(
            "/api/v1/auth/sms/verify",
            json={"phone": phone, "code": otp},
        )
        refresh_token = verify_resp.json()["data"]["refresh_token"]

        # 갱신
        response = await client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
