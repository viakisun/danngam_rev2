"""후기 라우터 — M07 REVIEW.

엔드포인트:
  POST /api/v1/reviews                     — 후기 작성
  GET  /api/v1/reviews/users/{user_id}     — 사용자 후기 목록
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, UserReviewStats
from app.services.review_service import create_review, get_user_reviews

router = APIRouter(prefix="/reviews")


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


@router.post("", status_code=status.HTTP_201_CREATED, summary="후기 작성")
async def create_review_endpoint(
    review_data: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """작업 완료 후 상대방에 대한 별점+후기를 작성합니다."""
    try:
        review = await create_review(db, current_user.id, review_data)
    except ValueError as e:
        parts = str(e).split(":", 1)
        code, message = (parts[0], parts[1]) if len(parts) == 2 else ("DNNG-REVIEW-000", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": code, "message": message}},
        )
    return success_response(ReviewResponse.model_validate(review).model_dump())


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, summary="사용자 후기 목록")
async def get_user_reviews_endpoint(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """특정 사용자가 받은 후기 목록과 평균 평점을 조회합니다."""
    reviews, avg_rating, total = await get_user_reviews(db, user_id)
    return success_response(
        UserReviewStats(
            avg_rating=avg_rating,
            total_reviews=total,
            items=[ReviewResponse.model_validate(r) for r in reviews],
        ).model_dump()
    )
