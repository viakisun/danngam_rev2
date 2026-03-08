"""M07 REVIEW 테스트."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.job import Job, JobCategory, JobStatus, PayType
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate
from app.services.review_service import create_review, get_user_reviews

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


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
        phone="01077771111",
        current_role=UserRole.REQUESTER,
        is_active=True,
        avg_rating=0.0,
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
        phone="01088882222",
        current_role=UserRole.WORKER,
        is_active=True,
        avg_rating=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def completed_job(db: AsyncSession, requester: User) -> Job:
    job = Job(
        id=uuid.uuid4(),
        requester_id=requester.id,
        title="벼베기 완료 작업",
        category=JobCategory.RICE_HARVESTING,
        location_lat=36.19,
        location_lng=127.09,
        location_address="충남 논산시",
        area_pyeong=3000,
        pay_type=PayType.PER_PYEONG,
        status=JobStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    return job


class TestCreateReview:
    """후기 작성 테스트."""

    async def test_create_review_success(self, db, requester, worker, completed_job):
        review = await create_review(
            db,
            requester.id,
            ReviewCreate(
                job_id=completed_job.id,
                reviewee_id=worker.id,
                rating=5,
                comment="정말 빠르게 해주셨어요",
            ),
        )
        assert review.id is not None
        assert review.rating == 5
        assert review.comment == "정말 빠르게 해주셨어요"
        assert review.reviewer_id == requester.id
        assert review.reviewee_id == worker.id

    async def test_rating_out_of_range(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ReviewCreate(
                job_id=uuid.uuid4(),
                reviewee_id=uuid.uuid4(),
                rating=6,  # 최대 5
            )

    async def test_review_requires_completed_job(self, db, requester, worker):
        from app.models.job import JobStatus
        open_job = Job(
            id=uuid.uuid4(),
            requester_id=requester.id,
            title="열린 작업",
            category=JobCategory.RICE_HARVESTING,
            location_lat=36.19,
            location_lng=127.09,
            location_address="충남 논산시",
            area_pyeong=1000,
            pay_type=PayType.TOTAL,
            status=JobStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(open_job)
        await db.flush()

        with pytest.raises(ValueError, match="DNNG-REVIEW-002"):
            await create_review(
                db,
                requester.id,
                ReviewCreate(
                    job_id=open_job.id,
                    reviewee_id=worker.id,
                    rating=3,
                ),
            )

    async def test_duplicate_review_rejected(self, db, requester, worker, completed_job):
        try:
            await create_review(
                db,
                requester.id,
                ReviewCreate(job_id=completed_job.id, reviewee_id=worker.id, rating=4),
            )
        except ValueError:
            pass  # 이미 이전 테스트에서 작성했을 수 있음

        with pytest.raises(ValueError, match="DNNG-REVIEW-003"):
            await create_review(
                db,
                requester.id,
                ReviewCreate(job_id=completed_job.id, reviewee_id=worker.id, rating=3),
            )


class TestGetUserReviews:
    """사용자 후기 목록 조회 테스트."""

    async def test_get_reviews_empty(self, db):
        new_user = User(
            id=uuid.uuid4(),
            phone="01099993333",
            current_role=UserRole.WORKER,
            is_active=True,
            avg_rating=0.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_user)
        await db.flush()

        reviews, avg, total = await get_user_reviews(db, new_user.id)
        assert reviews == []
        assert avg == 0.0
        assert total == 0
