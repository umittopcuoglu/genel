"""Payment Gateway servisi.

Aktif `payment_gateway` entegrasyonunu okur ve provider'a göre charge/refund yürütür.
Şu an iyzico/stripe/paytr için MOCK istemci içerir; gerçek anahtar geldiğinde
HTTP çağrıları gerçek endpoint'lere yönlendirilir (parametreler hazır).
"""
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.param_crypto import decrypt_params
from app.models.integration_setting import IntegrationSetting
from app.models.payment_transaction import (
    PaymentTransaction,
    PaymentTxnKind,
    PaymentTxnStatus,
)
from app.schemas.payment import CardDetails, ChargeRequest, RefundRequest

logger = logging.getLogger(__name__)


def _luhn_check(number: str) -> bool:
    """Standart Luhn algoritması — geçersiz kart numaralarını reddet."""
    s, alt = 0, False
    for d in reversed(number):
        n = int(d)
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        s += n
        alt = not alt
    return s % 10 == 0


def _detect_brand(number: str) -> str:
    if number.startswith("4"):
        return "VISA"
    if number[:2] in {"51", "52", "53", "54", "55"} or number[:4] in {"2221", "2720"}:
        return "MASTERCARD"
    if number[:2] in {"34", "37"}:
        return "AMEX"
    if number[:2] == "65" or number.startswith("9792"):
        return "TROY"
    return "UNKNOWN"


class PaymentService:
    """Provider-aware ödeme yürütme katmanı."""

    @staticmethod
    async def _resolve_integration(
        db: AsyncSession, integration_id: Optional[UUID]
    ) -> tuple[IntegrationSetting, dict]:
        """Hedef entegrasyonu (ve şifresi çözülmüş parametreleri) getirir."""
        stmt = select(IntegrationSetting).where(
            IntegrationSetting.integration_type == "payment_gateway",
            IntegrationSetting.enabled.is_(True),
            IntegrationSetting.deleted_at.is_(None),
        )
        if integration_id is not None:
            stmt = stmt.where(IntegrationSetting.id == integration_id)
        res = await db.execute(stmt)
        row = res.scalars().first()
        if row is None:
            raise ValueError("Aktif bir ödeme entegrasyonu bulunamadı (admin parametreleri girip etkinleştirmeli).")
        params = decrypt_params(row.params_encrypted) or {}
        if not params.get("provider"):
            raise ValueError("Entegrasyon parametrelerinde 'provider' eksik.")
        return row, params

    @staticmethod
    async def _call_provider_charge(
        provider: str, params: dict, amount: Decimal, currency: str, card: CardDetails
    ) -> dict:
        """Provider'a charge çağrısı.

        MOCK: provider/params zaten doğrulandığı kabulüyle deterministik yanıt üretir.
        Gerçek istemciler (iyzico/stripe/paytr) ileride buraya eklenecek.
        Test kart numaraları:
          - 4111 1111 1111 1111 → başarı (VISA)
          - 4000 0000 0000 0002 → reddedildi
        """
        ref = f"{provider.upper()}-{secrets.token_hex(8)}"
        # Reddedilen test kartı
        if card.number == "4000000000000002":
            return {"success": False, "ref": ref, "error": "card_declined"}
        # CVC kontrolü
        if card.cvc == "000":
            return {"success": False, "ref": ref, "error": "invalid_cvc"}
        return {"success": True, "ref": ref}

    @staticmethod
    async def _call_provider_refund(
        provider: str, params: dict, txn: PaymentTransaction, amount: Decimal
    ) -> dict:
        ref = f"{provider.upper()}-REF-{secrets.token_hex(6)}"
        return {"success": True, "ref": ref}

    @classmethod
    async def charge(cls, db: AsyncSession, req: ChargeRequest) -> tuple[PaymentTransaction, Optional[str]]:
        """Kart üzerinden tahsilat. Returns (txn, redirect_url_for_3ds)."""
        if not _luhn_check(req.card.number):
            raise ValueError("Kart numarası geçersiz (Luhn doğrulaması).")

        integration, params = await cls._resolve_integration(db, req.integration_id)
        provider = params["provider"]
        brand = _detect_brand(req.card.number)

        txn = PaymentTransaction(
            folio_id=req.folio_id,
            reservation_id=req.reservation_id,
            integration_id=integration.id,
            provider=provider,
            kind=PaymentTxnKind.CHARGE.value,
            status=PaymentTxnStatus.PENDING.value,
            amount=req.amount,
            currency=req.currency,
            card_last4=req.card.number[-4:],
            card_brand=brand,
        )
        db.add(txn)
        await db.flush()

        # 3DS akışı (entegrasyonda zorunluysa veya istek 3DS isterse)
        force_3ds = bool(params.get("use_3d_secure")) or req.use_3d_secure
        if force_3ds:
            txn.status = PaymentTxnStatus.PENDING.value
            txn.provider_ref = f"{provider.upper()}-3DS-{secrets.token_hex(6)}"
            await db.commit()
            await db.refresh(txn)
            redirect_url = f"/api/v1/payments/3ds/callback?txn={txn.id}&ok=1"
            return txn, redirect_url

        result = await cls._call_provider_charge(provider, params, req.amount, req.currency, req.card)
        if result["success"]:
            txn.status = PaymentTxnStatus.SUCCEEDED.value
            txn.provider_ref = result["ref"]
        else:
            txn.status = PaymentTxnStatus.FAILED.value
            txn.provider_ref = result["ref"]
            txn.error_message = result.get("error")
        await db.commit()
        await db.refresh(txn)
        return txn, None

    @classmethod
    async def complete_3ds(cls, db: AsyncSession, txn_id: UUID, ok: bool) -> PaymentTransaction:
        """3DS callback — bankadan dönen sonucu işleme alır."""
        res = await db.execute(select(PaymentTransaction).where(PaymentTransaction.id == txn_id))
        txn = res.scalar_one_or_none()
        if txn is None:
            raise ValueError("İşlem bulunamadı.")
        if txn.status != PaymentTxnStatus.PENDING.value:
            return txn
        txn.status = PaymentTxnStatus.SUCCEEDED.value if ok else PaymentTxnStatus.FAILED.value
        if not ok:
            txn.error_message = "3ds_failed"
        await db.commit()
        await db.refresh(txn)
        return txn

    @classmethod
    async def refund(cls, db: AsyncSession, req: RefundRequest) -> PaymentTransaction:
        res = await db.execute(select(PaymentTransaction).where(PaymentTransaction.id == req.txn_id))
        original = res.scalar_one_or_none()
        if original is None:
            raise ValueError("Orijinal işlem bulunamadı.")
        if original.status != PaymentTxnStatus.SUCCEEDED.value:
            raise ValueError("Sadece başarılı işlemler iade edilebilir.")

        amount = req.amount or original.amount
        if amount > original.amount:
            raise ValueError("İade tutarı orijinal işlemden büyük olamaz.")

        integration, params = await cls._resolve_integration(db, original.integration_id)
        provider = params["provider"]
        result = await cls._call_provider_refund(provider, params, original, amount)

        refund_txn = PaymentTransaction(
            folio_id=original.folio_id,
            reservation_id=original.reservation_id,
            integration_id=integration.id,
            provider=provider,
            kind=PaymentTxnKind.REFUND.value,
            status=PaymentTxnStatus.SUCCEEDED.value if result["success"] else PaymentTxnStatus.FAILED.value,
            amount=amount,
            currency=original.currency,
            provider_ref=result["ref"],
            parent_txn_id=original.id,
            error_message=None if result["success"] else result.get("error"),
            card_last4=original.card_last4,
            card_brand=original.card_brand,
        )
        db.add(refund_txn)
        # Orijinal kayıt tamamen iade edildiyse durumunu güncelle
        if result["success"] and amount == original.amount:
            original.status = PaymentTxnStatus.REFUNDED.value
        await db.commit()
        await db.refresh(refund_txn)
        return refund_txn

    @classmethod
    async def list_transactions(
        cls, db: AsyncSession, folio_id: Optional[UUID] = None, reservation_id: Optional[UUID] = None
    ) -> list[PaymentTransaction]:
        stmt = select(PaymentTransaction).where(PaymentTransaction.deleted_at.is_(None))
        if folio_id:
            stmt = stmt.where(PaymentTransaction.folio_id == folio_id)
        if reservation_id:
            stmt = stmt.where(PaymentTransaction.reservation_id == reservation_id)
        stmt = stmt.order_by(PaymentTransaction.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
