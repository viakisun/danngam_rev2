"""관리자 라우터 — M09 ADMIN.

엔드포인트:
  GET  /api/v1/admin/users             — 사용자 목록 (검색/필터)
  POST /api/v1/admin/users/{id}/deactivate — 계정 정지
  GET  /api/v1/admin/jobs              — 작업 목록
  GET  /api/v1/admin/stats             — 기본 통계

TODO: Lv2 — 차트 데이터, 복잡한 집계, 감사 로그
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job, JobStatus
from app.models.user import User

router = APIRouter(prefix="/admin")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """관리자 전용 dependency."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {"code": "DNNG-ADMIN-001", "message": "관리자 권한이 필요합니다."},
            },
        )
    return current_user


@router.get("/users", status_code=status.HTTP_200_OK, summary="사용자 목록")
async def list_users(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = Query(None, description="전화번호 또는 이름 검색"),
    is_active: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """사용자 목록을 조회합니다. 전화번호/이름으로 검색 가능."""
    stmt = select(User)

    if q:
        stmt = stmt.where(
            (User.phone.ilike(f"%{q}%")) | (User.name.ilike(f"%{q}%"))
        )
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    # 전체 수
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    users = result.scalars().all()

    items = [
        {
            "id": str(u.id),
            "phone": u.phone,
            "name": u.name,
            "current_role": u.current_role.value if u.current_role else None,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "avg_rating": u.avg_rating,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return success_response({"items": items, "total": total, "limit": limit, "offset": offset})


@router.post(
    "/users/{user_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="계정 정지",
)
async def deactivate_user(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """사용자 계정을 정지합니다."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {"code": "DNNG-ADMIN-002", "message": "사용자를 찾을 수 없습니다."},
            },
        )
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {"code": "DNNG-ADMIN-003", "message": "관리자 계정은 정지할 수 없습니다."},
            },
        )

    user.is_active = False
    await db.flush()
    return success_response({"id": str(user_id), "is_active": False})


@router.get("/jobs", status_code=status.HTTP_200_OK, summary="작업 목록")
async def list_jobs_admin(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    job_status: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """전체 작업 목록을 조회합니다."""
    stmt = select(Job)

    if job_status:
        try:
            status_enum = JobStatus(job_status)
            stmt = stmt.where(Job.status == status_enum)
        except ValueError:
            pass

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    stmt = stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    items = [
        {
            "id": str(j.id),
            "title": j.title,
            "category": j.category.value if j.category else None,
            "status": j.status.value if j.status else None,
            "location_address": j.location_address,
            "requester_id": str(j.requester_id),
            "is_urgent": j.is_urgent,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]
    return success_response({"items": items, "total": total, "limit": limit, "offset": offset})


@router.get("/stats", status_code=status.HTTP_200_OK, summary="기본 통계")
async def get_stats(
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """플랫폼 기본 통계를 반환합니다.

    TODO: Lv2 — 일별/월별 추이 차트, 지역별 분포, 매출 통계
    """
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (
        await db.execute(select(func.count(User.id)).where(User.is_active.is_(True)))
    ).scalar() or 0

    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    matched_jobs = (
        await db.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.MATCHED)
        )
    ).scalar() or 0
    completed_jobs = (
        await db.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.COMPLETED)
        )
    ).scalar() or 0

    completion_rate = round(completed_jobs / total_jobs * 100, 1) if total_jobs > 0 else 0.0

    return success_response(
        {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users,
            },
            "jobs": {
                "total": total_jobs,
                "matched": matched_jobs,
                "completed": completed_jobs,
                "completion_rate_pct": completion_rate,
            },
        }
    )
