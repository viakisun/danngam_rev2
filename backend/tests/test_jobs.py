"""M03 MATCHING 테스트 (TC01~TC08)."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.job import Job, JobApplication, JobCategory, JobStatus, PayType, ApplicationStatus
from app.models.user import User, UserRole
from app.schemas.job import ApplicationCreate, JobCreate
from app.services.matching_service import (
    apply_to_job,
    create_job,
    list_jobs_by_gps,
    select_applicant,
    update_job_status,
)
from app.utils.geo import haversine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# 충남 논산 좌표 (테스트 기준점)
CENTER_LAT = 36.19
CENTER_LNG = 127.09


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def requester(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01011110001",
        current_role=UserRole.REQUESTER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def worker(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        phone="01022220002",
        current_role=UserRole.WORKER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


def make_job_data(lat: float = CENTER_LAT, lng: float = CENTER_LNG, is_urgent: bool = False) -> JobCreate:
    return JobCreate(
        title="벼베기 작업 구합니다",
        category=JobCategory.RICE_HARVESTING,
        location_lat=lat,
        location_lng=lng,
        location_address="충남 논산시 테스트동",
        area_pyeong=3000,
        pay_type=PayType.PER_PYEONG,
        pay_amount=5000,
        is_urgent=is_urgent,
    )


class TestTC01_CreateJob:
    """TC01: 작업 등록."""

    async def test_create_job(self, db, requester):
        job = await create_job(db, requester.id, make_job_data())
        assert job.id is not None
        assert job.title == "벼베기 작업 구합니다"
        assert job.category == JobCategory.RICE_HARVESTING
        assert job.status == JobStatus.OPEN
        assert job.requester_id == requester.id


class TestTC02_GPSFilter:
    """TC02: GPS 반경 내 목록 조회."""

    async def test_jobs_within_radius(self, db, requester):
        # 반경 내 작업 (3km)
        job_near = await create_job(
            db, requester.id,
            make_job_data(lat=CENTER_LAT + 0.025, lng=CENTER_LNG)  # ~2.8km
        )
        results, _ = await list_jobs_by_gps(db, CENTER_LAT, CENTER_LNG, radius_km=5.0)
        job_ids = [j.id for j, _ in results]
        assert job_near.id in job_ids


class TestTC03_OutsideRadius:
    """TC03: 반경 외 작업 미포함."""

    async def test_jobs_outside_radius_excluded(self, db, requester):
        # 반경 외 작업 (50km 이상)
        job_far = await create_job(
            db, requester.id,
            make_job_data(lat=CENTER_LAT + 0.5, lng=CENTER_LNG + 0.5)  # ~60km
        )
        results, _ = await list_jobs_by_gps(db, CENTER_LAT, CENTER_LNG, radius_km=5.0)
        job_ids = [j.id for j, _ in results]
        assert job_far.id not in job_ids


class TestTC04_UrgentFirst:
    """TC04: 긴급 작업 최상단 정렬."""

    async def test_urgent_jobs_first(self, db, requester):
        normal = await create_job(db, requester.id, make_job_data(is_urgent=False))
        urgent = await create_job(db, requester.id, make_job_data(is_urgent=True))

        results, _ = await list_jobs_by_gps(db, CENTER_LAT, CENTER_LNG, radius_km=5.0)
        job_ids = [j.id for j, _ in results]

        if urgent.id in job_ids and normal.id in job_ids:
            assert job_ids.index(urgent.id) < job_ids.index(normal.id)


class TestTC05_Apply:
    """TC05: 작업 지원."""

    async def test_apply_to_job(self, db, requester, worker):
        job = await create_job(db, requester.id, make_job_data())
        app = await apply_to_job(db, job.id, worker.id, ApplicationCreate(message="경력 5년"))
        assert app.id is not None
        assert app.job_id == job.id
        assert app.applicant_id == worker.id
        assert app.status == ApplicationStatus.PENDING


class TestTC06_DuplicateApply:
    """TC06: 중복 지원."""

    async def test_duplicate_apply_rejected(self, db, requester, worker):
        job = await create_job(db, requester.id, make_job_data())
        await apply_to_job(db, job.id, worker.id, ApplicationCreate())

        with pytest.raises(ValueError, match="DNNG-MATCH-002"):
            await apply_to_job(db, job.id, worker.id, ApplicationCreate())


class TestTC07_SelectApplicant:
    """TC07: 지원자 선택 → 매칭 완료."""

    async def test_select_applicant(self, db, requester, worker):
        job = await create_job(db, requester.id, make_job_data())
        await apply_to_job(db, job.id, worker.id, ApplicationCreate())
        updated_job = await select_applicant(db, job.id, requester.id, worker.id)
        assert updated_job.status == JobStatus.MATCHED


class TestTC08_StatusTransition:
    """TC08: 상태 전이 (MATCHED → IN_PROGRESS → COMPLETED)."""

    async def test_full_status_transition(self, db, requester, worker):
        job = await create_job(db, requester.id, make_job_data())
        await apply_to_job(db, job.id, worker.id, ApplicationCreate())
        await select_applicant(db, job.id, requester.id, worker.id)

        in_progress = await update_job_status(db, job.id, requester.id, JobStatus.IN_PROGRESS)
        assert in_progress.status == JobStatus.IN_PROGRESS

        completed = await update_job_status(db, job.id, requester.id, JobStatus.COMPLETED)
        assert completed.status == JobStatus.COMPLETED


class TestHaversine:
    """Haversine 거리 계산 단위 테스트."""

    def test_same_point_distance_zero(self):
        dist = haversine(36.19, 127.09, 36.19, 127.09)
        assert dist == pytest.approx(0.0, abs=0.001)

    def test_known_distance(self):
        # 서울(37.5665, 126.9780) → 부산(35.1796, 129.0756) ≈ 325km
        dist = haversine(37.5665, 126.9780, 35.1796, 129.0756)
        assert 320 < dist < 340
