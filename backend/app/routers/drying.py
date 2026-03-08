"""건조시설 라우터 — M04 DRYING.

엔드포인트:
  POST  /api/v1/drying/facilities                        — 시설 등록
  GET   /api/v1/drying/facilities                        — 시설 목록
  POST  /api/v1/drying/reservations                      — 예약 생성
  GET   /api/v1/drying/reservations/{id}                 — 예약 상세
  PATCH /api/v1/drying/reservations/{id}/approve         — 예약 승인
  PATCH /api/v1/drying/reservations/{id}/complete        — 건조 완료 (수율 계산)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.drying import DryingFacility, DryingReservation
from app.models.user import User
from app.schemas.drying import (
    FacilityCreate,
    FacilityResponse,
    ReservationComplete,
    ReservationCreate,
    ReservationResponse,
)
from app.services.drying_service import (
    approve_reservation,
    complete_reservation,
    create_reservation,
    register_facility,
)
from app.utils.geo import DEFAULT_RADIUS_KM, MAX_RADIUS_KM, haversine

router = APIRouter(prefix="/drying")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def _parse_error(exc: ValueError) -> tuple[str, str]:
    parts = str(exc).split(":", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("DNNG-DRY-000", str(exc))


@router.post("/facilities", status_code=status.HTTP_201_CREATED, summary="건조시설 등록")
async def register_facility_endpoint(
    facility_data: FacilityCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    facility = await register_facility(db, current_user.id, facility_data)
    return success_response(FacilityResponse.model_validate(facility).model_dump())


@router.get("/facilities", status_code=status.HTTP_200_OK, summary="건조시설 목록")
async def list_facilities_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lat: float = Query(None),
    lng: float = Query(None),
    radius_km: float = Query(DEFAULT_RADIUS_KM, ge=0.1, le=MAX_RADIUS_KM),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    stmt = select(DryingFacility).where(DryingFacility.is_active.is_(True))
    result = await db.execute(stmt)
    facilities = result.scalars().all()

    items = []
    for f in facilities:
        if lat is not None and lng is not None:
            dist = haversine(lat, lng, f.location_lat, f.location_lng)
            if dist > radius_km:
                continue
        items.append(FacilityResponse.model_validate(f).model_dump())

    return success_response({"items": items, "total": len(items)})


@router.post("/reservations", status_code=status.HTTP_201_CREATED, summary="건조 예약")
async def create_reservation_endpoint(
    reservation_data: ReservationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        reservation = await create_reservation(db, current_user.id, reservation_data)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response(ReservationResponse.model_validate(reservation).model_dump())


@router.get("/reservations/{reservation_id}", status_code=status.HTTP_200_OK, summary="예약 상세")
async def get_reservation_endpoint(
    reservation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(DryingReservation).where(DryingReservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DNNG-DRY-001", "message": "예약을 찾을 수 없습니다."}},
        )
    return success_response(ReservationResponse.model_validate(reservation).model_dump())


@router.patch(
    "/reservations/{reservation_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="예약 승인 (운영자)",
)
async def approve_reservation_endpoint(
    reservation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    try:
        reservation = await approve_reservation(db, reservation_id, current_user.id)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response(ReservationResponse.model_validate(reservation).model_dump())


@router.patch(
    "/reservations/{reservation_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="건조 완료 + 수율 자동 계산",
)
async def complete_reservation_endpoint(
    reservation_id: uuid.UUID,
    complete_data: ReservationComplete,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """건조를 완료하고 수율을 자동 계산합니다.

    수율(%) = 산출량(output_kg) / 투입량(input_kg) × 100
    """
    try:
        reservation = await complete_reservation(db, reservation_id, current_user.id, complete_data)
    except ValueError as e:
        code, message = _parse_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response(ReservationResponse.model_validate(reservation).model_dump())
