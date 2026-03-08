"""정산 라우터 — M08 PAYMENT.

엔드포인트:
  PATCH /api/v1/jobs/{job_id}/payment         — 협의 금액 기록
  POST  /api/v1/jobs/{job_id}/payment/confirm — 정산 확인

TODO: Lv2 — 토스페이먼츠/카카오페이 PG 연동 (실제 결제 처리)
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job, JobStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentResponse, PaymentUpdate

router = APIRouter()


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


@router.patch(
    "/jobs/{job_id}/payment",
    status_code=status.HTTP_200_OK,
    summary="협의 금액 기록",
)
async def record_payment(
    job_id: uuid.UUID,
    payment_data: PaymentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """채팅에서 협의된 금액을 기록합니다.

    TODO: Lv2 — 실제 PG 결제 처리로 전환
    """
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DNNG-MATCH-001", "message": "작업을 찾을 수 없습니다."}},
        )
    if job.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "DNNG-PAY-001", "message": "권한이 없습니다."}},
        )

    pay_result = await db.execute(select(Payment).where(Payment.job_id == job_id))
    payment = pay_result.scalar_one_or_none()

    if payment is None:
        # 매칭된 작업자 ID 조회
        from app.models.job import JobApplication, ApplicationStatus
        app_result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job_id,
                JobApplication.status == ApplicationStatus.SELECTED,
            )
        )
        application = app_result.scalar_one_or_none()
        worker_id = application.applicant_id if application else current_user.id

        payment = Payment(
            id=uuid.uuid4(),
            job_id=job_id,
            requester_id=current_user.id,
            worker_id=worker_id,
            agreed_amount=payment_data.agreed_amount,
            notes=payment_data.notes,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(payment)
    else:
        payment.agreed_amount = payment_data.agreed_amount
        payment.notes = payment_data.notes
        payment.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return success_response(PaymentResponse.model_validate(payment).model_dump())


@router.post(
    "/jobs/{job_id}/payment/confirm",
    status_code=status.HTTP_200_OK,
    summary="정산 확인 (의뢰자)",
)
async def confirm_payment(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """의뢰자가 정산을 확인합니다.

    TODO: Lv2 — PG 결제 완료 콜백 처리로 전환
    """
    pay_result = await db.execute(select(Payment).where(Payment.job_id == job_id))
    payment = pay_result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "DNNG-PAY-002", "message": "정산 기록을 찾을 수 없습니다."}},
        )
    if payment.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": {"code": "DNNG-PAY-001", "message": "권한이 없습니다."}},
        )
    if payment.status == PaymentStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": {"code": "DNNG-PAY-003", "message": "이미 확인된 정산입니다."}},
        )

    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.now(timezone.utc)
    payment.updated_at = datetime.now(timezone.utc)

    return success_response(PaymentResponse.model_validate(payment).model_dump())
