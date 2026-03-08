"""후기 관련 Pydantic 스키마 — M07 REVIEW."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """후기 작성 요청."""

    job_id: uuid.UUID
    reviewee_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=200)


class ReviewResponse(BaseModel):
    """후기 응답."""

    id: uuid.UUID
    job_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewee_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserReviewStats(BaseModel):
    """사용자 후기 통계."""

    avg_rating: float
    total_reviews: int
    items: list[ReviewResponse]
