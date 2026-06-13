"""GİB e-Fatura entegrasyon servisi.

Aktif `gib_einvoice` entegrasyonundan parametreleri okur, provider'a
(Foriba/Logo/Uyumsoft/İzibiz) göre fatura XML'i üretir ve dış servise iletir.
Şu an MOCK — provider parametreleri verildikten sonra gerçek HTTP entegrasyonu
buraya delege edilir.
"""
import logging
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.param_crypto import decrypt_params
from app.models.einvoice import EInvoice
from app.models.integration_setting import IntegrationSetting

logger = logging.getLogger(__name__)


class EInvoiceService:
    """GİB e-Fatura yaşam döngüsü: oluştur → XML → gönder → durum sorgula → PDF."""

    KDV_RATE = Decimal("0.20")

    # ── Yardımcılar ──

    @staticmethod
    async def _resolve_integration(db: AsyncSession) -> tuple[IntegrationSetting, dict]:
        res = await db.execute(
            select(IntegrationSetting).where(
                IntegrationSetting.integration_type == "gib_einvoice",
                IntegrationSetting.enabled.is_(True),
                IntegrationSetting.deleted_at.is_(None),
            )
        )
        row = res.scalars().first()
        if row is None:
            raise ValueError("Aktif bir GİB e-Fatura entegrasyonu bulunamadı")
        params = decrypt_params(row.params_encrypted) or {}
        required = ("provider", "username", "password", "vkn", "endpoint_url", "environment")
        for k in required:
            if not params.get(k):
                raise ValueError(f"GİB parametresi eksik: {k}")
        return row, params

    @staticmethod
    def _validate_vkn_tckn(value: str) -> bool:
        """VKN (10 hane) veya TCKN (11 hane) sade doğrulama."""
        if not value or not value.isdigit():
            return False
        return len(value) in (10, 11)

    @staticmethod
    def _calculate_totals(subtotal: Decimal) -> tuple[Decimal, Decimal]:
        kdv = (subtotal * EInvoiceService.KDV_RATE).quantize(Decimal("0.01"))
        total = (subtotal + kdv).quantize(Decimal("0.01"))
        return kdv, total

    @staticmethod
    def _build_ubl_xml(inv: EInvoice, sender_vkn: str, environment: str) -> str:
        """UBL-TR 1.2 sözleşmesine uygun (basitleştirilmiş) e-Fatura XML'i.

        Gerçek üretimde XSD doğrulaması, dijital imza, profil (TICARI/TEMEL),
        senaryo bilgisi vb. eklenir; bu sürüm provider'ların kabul edebileceği
        çekirdek alanları içerir.
        """
        invoice_uuid = inv.e_invoice_uuid or str(uuid4())
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <UBLVersionID>2.1</UBLVersionID>
  <CustomizationID>TR1.2</CustomizationID>
  <ProfileID>TEMELFATURA</ProfileID>
  <ID>{escape(inv.invoice_number)}</ID>
  <UUID>{invoice_uuid}</UUID>
  <IssueDate>{escape(inv.invoice_date)}</IssueDate>
  <InvoiceTypeCode>SATIS</InvoiceTypeCode>
  <DocumentCurrencyCode>TRY</DocumentCurrencyCode>
  <Environment>{escape(environment)}</Environment>
  <AccountingSupplierParty>
    <Party>
      <PartyIdentification><ID schemeID="VKN">{escape(sender_vkn)}</ID></PartyIdentification>
    </Party>
  </AccountingSupplierParty>
  <AccountingCustomerParty>
    <Party>
      <PartyIdentification><ID schemeID="TCKN">{escape(inv.customer_tax_id or '')}</ID></PartyIdentification>
      <PartyName><Name>{escape(inv.customer_name)}</Name></PartyName>
      <Contact><ElectronicMail>{escape(inv.customer_email)}</ElectronicMail></Contact>
    </Party>
  </AccountingCustomerParty>
  <LegalMonetaryTotal>
    <LineExtensionAmount currencyID="TRY">{inv.subtotal}</LineExtensionAmount>
    <TaxExclusiveAmount currencyID="TRY">{inv.subtotal}</TaxExclusiveAmount>
    <TaxInclusiveAmount currencyID="TRY">{inv.total_amount}</TaxInclusiveAmount>
    <PayableAmount currencyID="TRY">{inv.total_amount}</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""

    # ── Akış ──

    @classmethod
    async def create_invoice(
        cls,
        db: AsyncSession,
        customer_name: str,
        customer_email: str,
        subtotal: Decimal,
        customer_tax_id: Optional[str] = None,
        source_folio_id: Optional[UUID] = None,
    ) -> EInvoice:
        if subtotal <= 0:
            raise ValueError("Tutar pozitif olmalı")
        if customer_tax_id and not cls._validate_vkn_tckn(customer_tax_id):
            raise ValueError("VKN/TCKN formatı geçersiz (10 veya 11 hane)")

        integration, params = await cls._resolve_integration(db)
        kdv, total = cls._calculate_totals(subtotal)
        now = datetime.now(timezone.utc)
        invoice_number = f"GIB{now.year}-{secrets.token_hex(4).upper()}"

        inv = EInvoice(
            invoice_number=invoice_number,
            invoice_date=now.date().isoformat(),
            customer_name=customer_name,
            customer_tax_id=customer_tax_id,
            customer_email=customer_email,
            subtotal=subtotal,
            kdv_amount=kdv,
            total_amount=total,
            e_invoice_uuid=str(uuid4()),
            einvoice_status="draft",
            source_folio_id=source_folio_id,
        )
        inv.xml_content = cls._build_ubl_xml(inv, params["vkn"], params["environment"])
        db.add(inv)
        await db.commit()
        await db.refresh(inv)
        return inv

    @classmethod
    async def send_to_gib(cls, db: AsyncSession, invoice_id: UUID) -> EInvoice:
        """Faturayı entegratöre gönder (mock: provider parametrelerini doğrular, durumu günceller)."""
        inv = await db.get(EInvoice, invoice_id)
        if inv is None:
            raise ValueError("Fatura bulunamadı")
        if inv.einvoice_status not in ("draft", "failed"):
            raise ValueError(f"Bu durumdaki fatura yeniden gönderilemez: {inv.einvoice_status}")

        integration, params = await cls._resolve_integration(db)
        provider = params["provider"]

        # MOCK: provider'a göre simülasyon — özel test e-postası ile başarısızlık simüle edilebilir
        if inv.customer_email and "rejected" in inv.customer_email.lower():
            inv.einvoice_status = "failed"
            inv.gib_response_code = "9999"
            inv.gib_error_message = f"{provider}: alıcı kayıtlı kullanıcı değil"
        else:
            inv.einvoice_status = "sent"
            inv.gib_response_code = "0000"
            inv.gib_error_message = None
            inv.xml_url = f"https://gib.example.com/{provider}/{inv.e_invoice_uuid}.xml"
        await db.commit()
        await db.refresh(inv)
        return inv

    @classmethod
    async def query_status(cls, db: AsyncSession, invoice_id: UUID) -> EInvoice:
        """GİB tarafındaki güncel durumu sorgular (mock: gönderildiyse delivered'a geçirir)."""
        inv = await db.get(EInvoice, invoice_id)
        if inv is None:
            raise ValueError("Fatura bulunamadı")
        await cls._resolve_integration(db)
        if inv.einvoice_status == "sent":
            inv.einvoice_status = "delivered"
            await db.commit()
            await db.refresh(inv)
        return inv

    @classmethod
    async def cancel(cls, db: AsyncSession, invoice_id: UUID) -> EInvoice:
        inv = await db.get(EInvoice, invoice_id)
        if inv is None:
            raise ValueError("Fatura bulunamadı")
        if inv.einvoice_status in ("cancelled", "delivered"):
            raise ValueError(f"Bu durumdaki fatura iptal edilemez: {inv.einvoice_status}")
        inv.einvoice_status = "cancelled"
        await db.commit()
        await db.refresh(inv)
        return inv
