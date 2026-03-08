"""농작업 매칭 서비스 — M03 MATCHING."""

import base64
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import ApplicationStatus, Job, JobApplication, JobStatus
from app.schemas.job import ApplicationCreate, JobCreate
from app.utils.geo import DEFAULT_RADIUS_KM, MAX_RADIUS_KM, haversine


async def create_job(
    db: AsyncSession,
    requester_id: uuid.UUID,
    job_data: JobCreate,
) -> Job:
    """작업 등록."""
    job = Job(
        id=uuid.uuid4(),
        requester_id=requester_id,
        **job_data.model_dump(),
        status=JobStatus.OPEN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.flush()
    return job


async def list_jobs_by_gps(
    db: AsyncSession,
    center_lat: float,
    center_lng: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    cursor: str | None = None,
    limit: int = 20,
    category: str | None = None,
) -> tuple[list[tuple[Job, float]], str | None]:
    """GPS 반경 내 작업 목록 조회 (cursor-based).

    긴급(is_urgent=True) 작업이 목록 최상단에 위치.

    Returns:
        (job, distance_km) 튜플 목록과 next_cursor
    """
    radius_km = min(radius_km, MAX_RADIUS_KM)

    # 대략적인 위도/경도 범위로 DB 필터링 (성능 최적화)
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * abs(max(0.001, abs(center_lat))))

    stmt = select(Job).where(
        and_(
            Job.status == JobStatus.OPEN,
            Job.location_lat.between(center_lat - lat_delta, center_lat + lat_delta),
            Job.location_lng.between(center_lng - lng_delta, center_lng + lng_delta),
        )
    )

    if category:
        stmt = stmt.where(Job.category == category)

    # cursor 적용
    if cursor:
        try:
            cursor_ts = _decode_cursor(cursor)
            stmt = stmt.where(Job.created_at < cursor_ts)
        except Exception:
            pass

    # 정렬: 긴급 우선, 최신순
    stmt = stmt.order_by(Job.is_urgent.desc(), Job.created_at.desc())
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Haversine 정밀 필터링
    filtered: list[tuple[Job, float]] = []
    for job in jobs:
        dist = haversine(center_lat, center_lng, job.location_lat, job.location_lng)
        if dist <= radius_km:
            filtered.append((job, round(dist, 2)))

    # cursor 생성
    next_cursor = None
    if len(filtered) > limit:
        filtered = filtered[:limit]
        last_job = filtered[-1][0]
        next_cursor = _encode_cursor(last_job.created_at)

    return filtered, next_cursor


def _encode_cursor(dt: datetime) -> str:
    return base64.b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.b64decode(cursor.encode()).decode())


async def apply_to_job(
    db: AsyncSession,
    job_id: uuid.UUID,
    applicant_id: uuid.UUID,
    application_data: ApplicationCreate,
) -> JobApplication:
    """작업 지원.

    Raises:
        ValueError: 중복 지원, 본인 작업, 마감된 작업
    """
    # 작업 조회
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError("DNNG-MATCH-001:작업을 찾을 수 없습니다.")

    # 본인 작업 지원 방지
    if job.requester_id == applicant_id:
        raise ValueError("DNNG-MATCH-003:본인이 등록한 작업에는 지원할 수 없습니다.")

    # 상태 확인
    if job.status != JobStatus.OPEN:
        raise ValueError("DNNG-MATCH-004:모집이 마감된 작업입니다.")

    # 중복 지원 확인
    dup = await db.execute(
        select(JobApplication).where(
            and_(
                JobApplication.job_id == job_id,
                JobApplication.applicant_id == applicant_id,
            )
        )
    )
    if dup.scalar_one_or_none():
        raise ValueError("DNNG-MATCH-002:이미 지원한 작업입니다.")

    application = JobApplication(
        id=uuid.uuid4(),
        job_id=job_id,
        applicant_id=applicant_id,
        message=application_data.message,
        status=ApplicationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )
    db.add(application)
    await db.flush()
    return application


async def select_applicant(
    db: AsyncSession,
    job_id: uuid.UUID,
    requester_id: uuid.UUID,
    applicant_id: uuid.UUID,
) -> Job:
    """지원자 선택 → 매칭 완료.

    Raises:
        ValueError: 권한 없음, 이미 매칭됨, 지원자 없음
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError("DNNG-MATCH-001:작업을 찾을 수 없습니다.")

    if job.requester_id != requester_id:
        raise ValueError("DNNG-MATCH-005:작업 등록자만 지원자를 선택할 수 있습니다.")

    if job.status != JobStatus.OPEN:
        raise ValueError("DNNG-MATCH-006:이미 매칭된 작업입니다.")

    # 지원 상태 업데이트
    app_result = await db.execute(
        select(JobApplication).where(
            and_(
                JobApplication.job_id == job_id,
                JobApplication.applicant_id == applicant_id,
            )
        )
    )
    application = app_result.scalar_one_or_none()
    if application is None:
        raise ValueError("DNNG-MATCH-001:해당 지원자를 찾을 수 없습니다.")

    application.status = ApplicationStatus.SELECTED
    job.status = JobStatus.MATCHED
    job.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return job


async def update_job_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    new_status: JobStatus,
) -> Job:
    """작업 상태 변경.

    허용 전이: MATCHED→IN_PROGRESS, IN_PROGRESS→COMPLETED, OPEN→CANCELLED
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise ValueError("DNNG-MATCH-001:작업을 찾을 수 없습니다.")

    if job.requester_id != user_id:
        raise ValueError("DNNG-MATCH-005:권한이 없습니다.")

    # 상태 전이 유효성
    valid_transitions = {
        JobStatus.MATCHED: [JobStatus.IN_PROGRESS],
        JobStatus.IN_PROGRESS: [JobStatus.COMPLETED],
        JobStatus.OPEN: [JobStatus.CANCELLED],
    }
    allowed = valid_transitions.get(job.status, [])
    if new_status not in allowed:
        raise ValueError(f"DNNG-MATCH-006:'{job.status}' → '{new_status}' 전이는 허용되지 않습니다.")

    job.status = new_status
    job.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return job
