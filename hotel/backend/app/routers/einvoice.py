"""GİB e-Fatura router'ı."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.einvoice import EInvoice
from app.models.user import User
from app.services.einvoice_service import EInvoiceService

router = APIRouter(prefix="/api/v1/einvoice", tags=["e-Fatura"])

ACCOUNTING_ROLES = ["superadmin", "manager", "accounting"]


class CreateInvoiceRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    customer_email: EmailStr
    customer_tax_id: Optional[str] = Field(default=None, max_length=20)
    subtotal: Decimal = Field(gt=0)
    source_folio_id: Optional[UUID] = None


class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    invoice_date: str
    customer_name: str
    customer_tax_id: Optional[str]
    customer_email: str
    subtotal: Decimal
    kdv_amount: Decimal
    total_amount: Decimal
    e_invoice_uuid: Optional[str]
    einvoice_status: str
    xml_url: Optional[str]
    gib_response_code: Optional[str]
    gib_error_message: Optional[str]
    source_folio_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    req: CreateInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    try:
        inv = await EInvoiceService.create_invoice(
            db,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            subtotal=req.subtotal,
            customer_tax_id=req.customer_tax_id,
            source_folio_id=req.source_folio_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return InvoiceResponse.model_validate(inv)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    try:
        inv = await EInvoiceService.send_to_gib(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return InvoiceResponse.model_validate(inv)


@router.get("/{invoice_id}/status", response_model=InvoiceResponse)
async def query_status(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    try:
        inv = await EInvoiceService.query_status(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return InvoiceResponse.model_validate(inv)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    try:
        inv = await EInvoiceService.cancel(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return InvoiceResponse.model_validate(inv)


@router.get("/{invoice_id}/xml")
async def get_xml(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    inv = await db.get(EInvoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
    return {"invoice_number": inv.invoice_number, "xml": inv.xml_content}


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ACCOUNTING_ROLES)),
):
    res = await db.execute(
        select(EInvoice).where(EInvoice.deleted_at.is_(None)).order_by(EInvoice.created_at.desc())
    )
    return [InvoiceResponse.model_validate(r) for r in res.scalars().all()]
