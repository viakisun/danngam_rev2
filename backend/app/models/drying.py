"""건조시설 및 예약 모델 — M04 DRYING (핵심 차별화 기능)."""

import uuid
from datetime import date, datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReservationStatus(str, PyEnum):
    """건조 예약 상태."""

    PENDING = "PENDING"  # 승인 대기
    APPROVED = "APPROVED"  # 승인 완료
    IN_DRYING = "IN_DRYING"  # 건조 중
    COMPLETED = "COMPLETED"  # 건조 완료
    CANCELLED = "CANCELLED"  # 취소


class DryingFacility(Base):
    """건조시설 모델."""

    __tablename__ = "drying_facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location_address: Mapped[str] = mapped_column(String(200), nullable=False)
    location_lat: Mapped[float] = mapped_column(Float, nullable=False)
    location_lng: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_crops: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reservations: Mapped[list["DryingReservation"]] = relationship(
        back_populates="facility", lazy="select"
    )


class DryingReservation(Base):
    """건조 예약 모델.

    핵심 차별화: 수율(yield_pct) 자동 계산 + 품질 기록.
    """

    __tablename__ = "drying_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drying_facilities.id"), nullable=False, index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    crop_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_kg: Mapped[float] = mapped_column(Float, nullable=False)
    output_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        default=ReservationStatus.PENDING,
        nullable=False,
    )
    # 수율 (자동 계산: output_kg / input_kg * 100)
    yield_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 품질 지표
    moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    color_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quality_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    facility: Mapped["DryingFacility"] = relationship(back_populates="reservations")
