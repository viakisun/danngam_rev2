"""M02 USER 테스트 (TC01~TC05)."""

import uuid
from datetime import datetime, timezone

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.user import User, UserRole
from app.utils.jwt import create_access_token

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
async def test_user(db_session: AsyncSession) -> User:
    """테스트용 사용자 생성."""
    user = User(
        id=uuid.uuid4(),
        phone="01011112222",
        name="테스트유저",
        current_role=UserRole.REQUESTER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, test_user: User):
    """인증된 테스트 클라이언트."""

    async def override_db():
        yield db_session

    async def override_current_user():
        return test_user

    from app.routers.auth import get_redis

    async def override_redis():
        yield fakeredis.aioredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


class TestTC01_GetProfile:
    """TC01: 내 프로필 조회."""

    async def test_get_profile(self, client, test_user):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["phone"] == test_user.phone
        assert data["data"]["name"] == "테스트유저"
        assert data["data"]["current_role"] == "requester"


class TestTC02_UpdateName:
    """TC02: 이름 수정."""

    async def test_update_name(self, client):
        response = await client.put(
            "/api/v1/users/me",
            json={"name": "홍길동"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "홍길동"


class TestTC03_EmptyName:
    """TC03: 이름 빈값 (유효성 검사)."""

    async def test_empty_name_rejected(self, client):
        response = await client.put(
            "/api/v1/users/me",
            json={"name": ""},
        )
        assert response.status_code == 422


class TestTC04_RoleSwitch:
    """TC04: requester → worker 전환."""

    async def test_role_switch_to_worker(self, client, test_user):
        # test_user는 requester로 시작
        test_user.current_role = UserRole.REQUESTER
        response = await client.post(
            "/api/v1/users/me/role-switch",
            json={"role": "worker"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["current_role"] == "worker"


class TestTC05_SameRoleSwitch:
    """TC05: 동일 역할로 전환 시 에러."""

    async def test_same_role_rejected(self, client, test_user):
        # 현재 역할과 동일한 역할로 전환 시도
        current_role = test_user.current_role.value
        response = await client.post(
            "/api/v1/users/me/role-switch",
            json={"role": current_role},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "DNNG-USER-002"
