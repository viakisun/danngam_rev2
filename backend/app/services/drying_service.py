"""건조시설 서비스 — M04 DRYING (핵심 차별화)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drying import DryingFacility, DryingReservation, ReservationStatus
from app.schemas.drying import FacilityCreate, ReservationComplete, ReservationCreate


def calculate_yield(input_kg: float, output_kg: float) -> float:
    """수율 계산: output_kg / input_kg * 100.

    Args:
        input_kg: 투입량 (kg)
        output_kg: 산출량 (kg)

    Returns:
        수율 (%, 소수점 2자리)

    Raises:
        ValueError: output_kg가 input_kg보다 큰 경우
    """
    if output_kg > input_kg:
        raise ValueError("DNNG-DRY-003:산출량이 투입량보다 클 수 없습니다.")
    if input_kg <= 0:
        raise ValueError("투입량은 0보다 커야 합니다.")
    return round((output_kg / input_kg) * 100, 2)


async def register_facility(
    db: AsyncSession,
    operator_id: uuid.UUID,
    facility_data: FacilityCreate,
) -> DryingFacility:
    """건조시설 등록."""
    facility = DryingFacility(
        id=uuid.uuid4(),
        operator_id=operator_id,
        **facility_data.model_dump(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(facility)
    await db.flush()
    return facility


async def create_reservation(
    db: AsyncSession,
    requester_id: uuid.UUID,
    reservation_data: ReservationCreate,
) -> DryingReservation:
    """건조 예약 생성.

    Raises:
        ValueError: 시설 없음
    """
    result = await db.execute(
        select(DryingFacility).where(
            DryingFacility.id == reservation_data.facility_id,
            DryingFacility.is_active.is_(True),
        )
    )
    facility = result.scalar_one_or_none()
    if facility is None:
        raise ValueError("DNNG-DRY-001:건조시설을 찾을 수 없습니다.")

    reservation = DryingReservation(
        id=uuid.uuid4(),
        requester_id=requester_id,
        **reservation_data.model_dump(),
        status=ReservationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(reservation)
    await db.flush()
    return reservation


async def approve_reservation(
    db: AsyncSession,
    reservation_id: uuid.UUID,
    operator_id: uuid.UUID,
) -> DryingReservation:
    """예약 승인 (시설 운영자만 가능)."""
    result = await db.execute(
        select(DryingReservation).where(DryingReservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if reservation is None:
        raise ValueError("DNNG-DRY-001:예약을 찾을 수 없습니다.")

    # 운영자 확인
    fac_result = await db.execute(
        select(DryingFacility).where(
            DryingFacility.id == reservation.facility_id,
            DryingFacility.operator_id == operator_id,
        )
    )
    if fac_result.scalar_one_or_none() is None:
        raise ValueError("DNNG-DRY-001:권한이 없습니다.")

    if reservation.status != ReservationStatus.PENDING:
        raise ValueError("DNNG-DRY-002:승인 대기 상태의 예약만 승인할 수 있습니다.")

    reservation.status = ReservationStatus.APPROVED
    reservation.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return reservation


async def complete_reservation(
    db: AsyncSession,
    reservation_id: uuid.UUID,
    operator_id: uuid.UUID,
    complete_data: ReservationComplete,
) -> DryingReservation:
    """건조 완료 처리 + 수율 자동 계산.

    핵심 차별화: 수율(yield_pct) = output_kg / input_kg * 100

    Raises:
        ValueError: output_kg > input_kg (DNNG-DRY-003)
    """
    result = await db.execute(
        select(DryingReservation).where(DryingReservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if reservation is None:
        raise ValueError("DNNG-DRY-001:예약을 찾을 수 없습니다.")

    # 수율 계산 (output > input 방지)
    yield_pct = calculate_yield(reservation.input_kg, complete_data.output_kg)

    reservation.output_kg = complete_data.output_kg
    reservation.yield_pct = yield_pct
    reservation.moisture_pct = complete_data.moisture_pct
    reservation.color_grade = complete_data.color_grade
    reservation.quality_grade = complete_data.quality_grade
    reservation.notes = complete_data.notes
    reservation.status = ReservationStatus.COMPLETED
    reservation.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return reservation
