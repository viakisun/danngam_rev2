"""후기 서비스 — M07 REVIEW."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


async def create_review(
    db: AsyncSession,
    reviewer_id: uuid.UUID,
    review_data: ReviewCreate,
) -> Review:
    """후기 작성.

    Args:
        db: DB 세션
        reviewer_id: 작성자 ID
        review_data: 후기 데이터

    Returns:
        생성된 후기

    Raises:
        ValueError: Job이 COMPLETED 상태가 아님 / 이미 후기 작성 / 참여자 아님
    """
    # Job 상태 확인
    job_result = await db.execute(select(Job).where(Job.id == review_data.job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise ValueError("DNNG-REVIEW-001:작업을 찾을 수 없습니다.")
    if job.status != JobStatus.COMPLETED:
        raise ValueError("DNNG-REVIEW-002:완료된 작업에만 후기를 작성할 수 있습니다.")

    # 중복 후기 확인
    dup = await db.execute(
        select(Review).where(
            and_(
                Review.job_id == review_data.job_id,
                Review.reviewer_id == reviewer_id,
                Review.reviewee_id == review_data.reviewee_id,
            )
        )
    )
    if dup.scalar_one_or_none():
        raise ValueError("DNNG-REVIEW-003:이미 후기를 작성했습니다.")

    review = Review(
        id=uuid.uuid4(),
        reviewer_id=reviewer_id,
        **review_data.model_dump(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(review)
    await db.flush()

    # reviewee의 평균 평점 재계산
    await recalculate_avg_rating(db, review_data.reviewee_id)

    return review


async def recalculate_avg_rating(db: AsyncSession, user_id: uuid.UUID) -> None:
    """사용자 평균 평점 재계산 후 User.avg_rating 업데이트."""
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.reviewee_id == user_id
        )
    )
    avg_rating, count = result.one()
    avg = round(float(avg_rating), 2) if avg_rating else 0.0

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.avg_rating = avg
        await db.flush()


async def get_user_reviews(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> tuple[list[Review], float, int]:
    """사용자 후기 목록 + 통계 조회."""
    result = await db.execute(
        select(Review).where(Review.reviewee_id == user_id).order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    stats = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.reviewee_id == user_id
        )
    )
    avg_rating, total = stats.one()

    return reviews, round(float(avg_rating or 0), 2), total or 0
