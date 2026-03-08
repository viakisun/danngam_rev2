"""정산 관련 Pydantic 스키마 — M08 PAYMENT."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentUpdate(BaseModel):
    """협의 금액 기록 요청."""

    agreed_amount: int = Field(..., ge=0)
    notes: str | None = None


class PaymentResponse(BaseModel):
    """정산 응답."""

    id: uuid.UUID
    job_id: uuid.UUID
    requester_id: uuid.UUID
    worker_id: uuid.UUID
    agreed_amount: int | None
    notes: str | None
    status: PaymentStatus
    confirmed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
