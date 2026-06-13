"""Payment Gateway router'ı: charge / refund / 3DS callback / işlem listesi."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.payment import (
    ChargeRequest,
    ChargeResponse,
    PaymentTxnResponse,
    RefundRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

CASHIER_ROLES = ["superadmin", "manager", "frontdesk", "accounting"]


@router.post("/charge", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
async def charge(
    req: ChargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(CASHIER_ROLES)),
):
    try:
        txn, redirect_url = await PaymentService.charge(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ChargeResponse(
        txn=PaymentTxnResponse.model_validate(txn),
        redirect_url=redirect_url,
        success=txn.status == "succeeded",
    )


@router.post("/refund", response_model=PaymentTxnResponse, status_code=status.HTTP_201_CREATED)
async def refund(
    req: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(CASHIER_ROLES)),
):
    try:
        txn = await PaymentService.refund(db, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PaymentTxnResponse.model_validate(txn)


@router.get("/3ds/callback", response_model=PaymentTxnResponse)
async def threeds_callback(
    txn: UUID = Query(...),
    ok: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    """3DS bankacılık callback'i — webhook olarak public, idempotent."""
    try:
        result = await PaymentService.complete_3ds(db, txn, bool(ok))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PaymentTxnResponse.model_validate(result)


@router.get("", response_model=List[PaymentTxnResponse])
async def list_transactions(
    folio_id: Optional[UUID] = Query(None),
    reservation_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(CASHIER_ROLES)),
):
    rows = await PaymentService.list_transactions(db, folio_id=folio_id, reservation_id=reservation_id)
    return [PaymentTxnResponse.model_validate(r) for r in rows]
