"""Job, JobApplication 모델 — M03 MATCHING."""

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


class JobCategory(str, PyEnum):
    """농작업 카테고리 (현장 용어 기준)."""

    RICE_HARVESTING = "rice_harvesting"  # 벼베기
    SWEET_POTATO_DIGGING = "sweet_potato_digging"  # 고구마 캐기
    GARLIC_PLANTING = "garlic_planting"  # 마늘 심기
    DRONE_SPRAYING = "drone_spraying"  # 드론 방제
    ROTARY_WORK = "rotary_work"  # 로터리 작업
    OTHER = "other"  # 기타


class JobStatus(str, PyEnum):
    """작업 상태."""

    OPEN = "OPEN"  # 모집 중
    MATCHED = "MATCHED"  # 매칭 완료
    IN_PROGRESS = "IN_PROGRESS"  # 작업 중
    COMPLETED = "COMPLETED"  # 완료
    CANCELLED = "CANCELLED"  # 취소


class PayType(str, PyEnum):
    """급여 유형."""

    PER_PYEONG = "per_pyeong"  # 평당
    TOTAL = "total"  # 총액
    NEGOTIABLE = "negotiable"  # 협의


class ApplicationStatus(str, PyEnum):
    """지원 상태."""

    PENDING = "pending"  # 대기
    SELECTED = "selected"  # 선택됨
    REJECTED = "rejected"  # 거절


class Job(Base):
    """농작업 모델."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[JobCategory] = mapped_column(
        Enum(JobCategory, name="job_category"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_lat: Mapped[float] = mapped_column(Float, nullable=False)
    location_lng: Mapped[float] = mapped_column(Float, nullable=False)
    location_address: Mapped[str] = mapped_column(String(200), nullable=False)
    area_pyeong: Mapped[int] = mapped_column(Integer, nullable=False)
    desired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pay_type: Mapped[PayType] = mapped_column(Enum(PayType, name="pay_type"), nullable=False)
    pay_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipment_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.OPEN,
        nullable=False,
        index=True,
    )
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

    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="job", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} category={self.category} status={self.status}>"


class JobApplication(Base):
    """작업 지원 모델."""

    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job: Mapped["Job"] = relationship(back_populates="applications")

    def __repr__(self) -> str:
        return f"<JobApplication id={self.id} job_id={self.job_id} status={self.status}>"
