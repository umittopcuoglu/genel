"""F&B servisi: Outlet, Menu, Check yaşam döngüsü, folio'ya transfer."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Folio, FolioItem, FolioItemType
from app.models.fnb import Check, CheckItem, CheckStatus, MenuItem, Outlet


class FnBService:
    @staticmethod
    async def _recalc(check: Check) -> None:
        subtotal = sum((it.line_total for it in check.items), Decimal("0"))
        kdv = sum(
            (it.line_total - (it.line_total / (1 + it.kdv_rate)) for it in check.items), Decimal("0")
        )
        check.subtotal = (subtotal - kdv).quantize(Decimal("0.01"))
        check.kdv_total = kdv.quantize(Decimal("0.01"))
        check.total = subtotal.quantize(Decimal("0.01"))

    @classmethod
    async def add_item(
        cls, db: AsyncSession, check_id: UUID, menu_item_id: UUID, qty: int = 1
    ) -> Check:
        check = await db.get(Check, check_id)
        if check is None:
            raise ValueError("Adisyon bulunamadı")
        if check.status != CheckStatus.OPEN.value:
            raise ValueError(f"Sadece açık adisyona ekleme yapılabilir (durum: {check.status})")
        mi = await db.get(MenuItem, menu_item_id)
        if mi is None or not mi.is_active:
            raise ValueError("Menü kalemi bulunamadı veya pasif")

        line_total = (mi.price * qty).quantize(Decimal("0.01"))
        item = CheckItem(
            check_id=check.id,
            menu_item_id=mi.id,
            name_snapshot=mi.name,
            qty=qty,
            unit_price=mi.price,
            kdv_rate=mi.kdv_rate,
            line_total=line_total,
        )
        db.add(item)
        await db.flush()

        # Yeniden yükle
        await db.refresh(check, attribute_names=["items"])
        await cls._recalc(check)
        await db.commit()
        await db.refresh(check)
        return check

    @classmethod
    async def post_to_folio(cls, db: AsyncSession, check_id: UUID, folio_id: UUID) -> Check:
        check = await db.get(Check, check_id)
        if check is None:
            raise ValueError("Adisyon bulunamadı")
        if check.status != CheckStatus.OPEN.value:
            raise ValueError("Sadece açık adisyon oda hesabına aktarılabilir")
        folio = await db.get(Folio, folio_id)
        if folio is None:
            raise ValueError("Folio bulunamadı")

        await db.refresh(check, attribute_names=["items"])
        for it in check.items:
            db.add(
                FolioItem(
                    folio_id=folio.id,
                    type=FolioItemType.FNB.value,
                    description=f"F&B: {it.name_snapshot} x{it.qty}",
                    qty=it.qty,
                    unit_price=it.unit_price,
                    tax_rate=(it.kdv_rate * 100),
                    total=it.line_total,
                )
            )
        folio.total = (folio.total or Decimal("0")) + check.total
        folio.balance = (folio.balance or Decimal("0")) + check.total
        check.folio_id = folio.id
        check.status = CheckStatus.POSTED_TO_FOLIO.value
        await db.commit()
        await db.refresh(check)
        return check

    @classmethod
    async def settle_cash(cls, db: AsyncSession, check_id: UUID) -> Check:
        check = await db.get(Check, check_id)
        if check is None:
            raise ValueError("Adisyon bulunamadı")
        if check.status != CheckStatus.OPEN.value:
            raise ValueError("Sadece açık adisyon ödeme alabilir")
        check.status = CheckStatus.PAID.value
        await db.commit()
        await db.refresh(check)
        return check

    @classmethod
    async def void(cls, db: AsyncSession, check_id: UUID) -> Check:
        check = await db.get(Check, check_id)
        if check is None:
            raise ValueError("Adisyon bulunamadı")
        if check.status != CheckStatus.OPEN.value:
            raise ValueError("Sadece açık adisyon iptal edilebilir")
        check.status = CheckStatus.VOIDED.value
        await db.commit()
        await db.refresh(check)
        return check
