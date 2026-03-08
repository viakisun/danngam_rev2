"""농작업 라우터 — M03 MATCHING.

엔드포인트:
  POST  /api/v1/jobs                          — 작업 등록
  GET   /api/v1/jobs                          — 작업 목록 (GPS 필터)
  GET   /api/v1/jobs/{job_id}                 — 작업 상세
  POST  /api/v1/jobs/{job_id}/apply           — 작업 지원
  POST  /api/v1/jobs/{job_id}/select/{app_id} — 지원자 선택
  PATCH /api/v1/jobs/{job_id}/status          — 상태 변경
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.schemas.job import (
    ApplicationCreate,
    ApplicationResponse,
    JobCreate,
    JobListResponse,
    JobResponse,
    StatusUpdateRequest,
)
from app.services.matching_service import (
    apply_to_job,
    create_job,
    list_jobs_by_gps,
    select_applicant,
    update_job_status,
)
from app.utils.geo import DEFAULT_RADIUS_KM, MAX_RADIUS_KM

router = APIRouter(prefix="/jobs")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def _parse_error(exc: ValueError) -> tuple[str, str]:
    """ValueError 메시지에서 에러코드와 메시지를 분리."""
    parts = str(exc).split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "DNNG-MATCH-000", str(exc)


@router.post("", status_code=status.HTTP_201_CREATED, summary="작업 등록")
async def create_job_endpoint(
    job_data: JobCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """농작업을 등록합니다. 의뢰자(requester) 역할 필요."""
    if current_user.current_role != UserRole.REQUESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "DNNG-MATCH-005", "message": "의뢰자 역할이 필요합니다."}},
        )
    job = await create_job(db, current_user.id, job_data)
    return success_response(JobResponse.model_validate(job).model_dump())


@router.get("", status_code=status.HTTP_200_OK, summary="작업 목록 조회 (GPS 반경)")
async def list_jobs_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lat: float = Query(..., description="기준 위도"),
    lng: float = Query(..., description="기준 경도"),
    radius_km: float = Query(DEFAULT_RADIUS_KM, ge=0.1, le=MAX_RADIUS_KM),
    category: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """GPS 반경 내 OPEN 상태 작업 목록을 조회합니다. 긴급 작업이 최상단."""
    job_tuples, next_cursor = await list_jobs_by_gps(
        db, lat, lng, radius_km, cursor, limit, category
    )

    items = []
    for job, dist in job_tuples:
        job_resp = JobResponse.model_validate(job)
        job_resp.distance_km = dist
        items.append(job_resp)

    return success_response(
        JobListResponse(
            items=items,
            next_cursor=next_cursor,
            total=len(items),
        ).model_dump()
    )


@router.get("/{job_id}", status_code=status.HTTP_200_OK, summary="작업 상세 조회")
async def get_job_endpoint(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DNNG-MATCH-001", "message": "작업을 찾을 수 없습니다."}},
        )
    return success_response(JobResponse.model_validate(job).model_dump())


@router.post("/{job_id}/apply", status_code=status.HTTP_201_CREATED, summary="작업 지원")
async def apply_job_endpoint(
    job_id: uuid.UUID,
    application_data: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """작업에 지원합니다. 작업자(worker) 역할 필요."""
    if current_user.current_role != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "DNNG-MATCH-005", "message": "작업자 역할이 필요합니다."}},
        )
    try:
        application = await apply_to_job(db, job_id, current_user.id, application_data)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response(ApplicationResponse.model_validate(application).model_dump())


@router.post(
    "/{job_id}/select/{applicant_id}",
    status_code=status.HTTP_200_OK,
    summary="지원자 선택 → 매칭 완료",
)
async def select_applicant_endpoint(
    job_id: uuid.UUID,
    applicant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        job = await select_applicant(db, job_id, current_user.id, applicant_id)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response({"status": job.status.value, "job_id": str(job.id)})


@router.patch("/{job_id}/status", status_code=status.HTTP_200_OK, summary="작업 상태 변경")
async def update_job_status_endpoint(
    job_id: uuid.UUID,
    status_data: StatusUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        job = await update_job_status(db, job_id, current_user.id, status_data.status)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response({"status": job.status.value})
