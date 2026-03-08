"""건조시설 관련 Pydantic 스키마 — M04 DRYING."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.drying import ReservationStatus


class FacilityCreate(BaseModel):
    """건조시설 등록 요청."""

    name: str = Field(..., min_length=1, max_length=100)
    location_address: str = Field(..., max_length=200)
    location_lat: float = Field(..., ge=-90.0, le=90.0)
    location_lng: float = Field(..., ge=-180.0, le=180.0)
    capacity_kg: float = Field(..., gt=0)
    price_per_kg: int = Field(..., ge=0)
    description: str | None = None
    available_crops: list[str] | None = None


class FacilityResponse(BaseModel):
    """건조시설 응답."""

    id: uuid.UUID
    operator_id: uuid.UUID
    name: str
    location_address: str
    location_lat: float
    location_lng: float
    capacity_kg: float
    price_per_kg: int
    description: str | None
    available_crops: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReservationCreate(BaseModel):
    """건조 예약 요청."""

    facility_id: uuid.UUID
    crop_type: str = Field(..., max_length=50)
    input_kg: float = Field(..., gt=0)
    scheduled_date: date
    notes: str | None = None


class ReservationComplete(BaseModel):
    """건조 완료 요청 (수율/품질 기록)."""

    output_kg: float = Field(..., gt=0)
    moisture_pct: float | None = Field(None, ge=0, le=100)
    color_grade: str | None = Field(None, max_length=10)
    quality_grade: str | None = Field(None, max_length=20)
    notes: str | None = None


class ReservationResponse(BaseModel):
    """건조 예약 응답."""

    id: uuid.UUID
    facility_id: uuid.UUID
    requester_id: uuid.UUID
    crop_type: str
    input_kg: float
    output_kg: float | None
    scheduled_date: date
    status: ReservationStatus
    yield_pct: float | None
    moisture_pct: float | None
    color_grade: str | None
    quality_grade: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
