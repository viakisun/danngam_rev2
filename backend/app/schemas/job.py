"""농작업 관련 Pydantic 스키마 — M03 MATCHING."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.job import ApplicationStatus, JobCategory, JobStatus, PayType


class JobCreate(BaseModel):
    """작업 등록 요청."""

    title: str = Field(..., min_length=2, max_length=100)
    category: JobCategory
    description: str | None = None
    location_lat: float = Field(..., ge=-90.0, le=90.0)
    location_lng: float = Field(..., ge=-180.0, le=180.0)
    location_address: str = Field(..., max_length=200)
    area_pyeong: int = Field(..., ge=1)
    desired_date: date | None = None
    pay_type: PayType
    pay_amount: int | None = Field(None, ge=0)
    equipment_tags: list[str] | None = None
    is_urgent: bool = False


class JobResponse(BaseModel):
    """작업 응답."""

    id: uuid.UUID
    requester_id: uuid.UUID
    title: str
    category: JobCategory
    description: str | None
    location_lat: float
    location_lng: float
    location_address: str
    area_pyeong: int
    desired_date: date | None
    pay_type: PayType
    pay_amount: int | None
    equipment_tags: list[str] | None
    is_urgent: bool
    status: JobStatus
    created_at: datetime
    distance_km: float | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """작업 목록 응답 (cursor-based)."""

    items: list[JobResponse]
    next_cursor: str | None
    total: int


class ApplicationCreate(BaseModel):
    """작업 지원 요청."""

    message: str | None = Field(None, max_length=500)


class ApplicationResponse(BaseModel):
    """작업 지원 응답."""

    id: uuid.UUID
    job_id: uuid.UUID
    applicant_id: uuid.UUID
    message: str | None
    status: ApplicationStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusUpdateRequest(BaseModel):
    """작업 상태 변경 요청."""

    status: JobStatus
