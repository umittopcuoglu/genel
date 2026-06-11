from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.ledger_entry import LedgerEntry
from app.models.chart_of_accounts import ChartOfAccount
from app.models.einvoice import EInvoice


class AccountingService:
    @staticmethod
    async def post_folio_closure(folio_id: UUID, total_amount: Decimal, db: AsyncSession) -> dict:
        """Folio kapanışında yevmiye kaydı oluştur."""

        revenue_account = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.account_code == "610")
        )
        revenue_acc = revenue_account.scalars().first()

        payment_account = await db.execute(
            select(ChartOfAccount).where(ChartOfAccount.account_code == "110")
        )
        payment_acc = payment_account.scalars().first()

        if not revenue_acc or not payment_acc:
            raise ValueError("Required chart of accounts not found")

        entry_number = f"2026-06-{int(datetime.utcnow().timestamp()) % 100000}"

        entry = LedgerEntry(
            journal_name="Satış",
            entry_date=datetime.utcnow().date().isoformat(),
            entry_number=entry_number,
            description=f"Folio #{folio_id} kapanışı",
            debit_account_id=payment_acc.id,
            debit_amount=total_amount,
            credit_account_id=revenue_acc.id,
            credit_amount=total_amount,
            source_type="folio",
            source_id=str(folio_id),
            status="draft",
            created_by=UUID(int=0),
        )

        db.add(entry)
        await db.commit()

        return {
            "entry_id": entry.id,
            "entry_number": entry_number,
            "amount": float(total_amount),
            "status": "draft",
        }

    @staticmethod
    async def post_ledger_entry(entry_id: UUID, db: AsyncSession) -> dict:
        """Yevmiye kaydını deftera naklet."""
        result = await db.execute(
            select(LedgerEntry).where(LedgerEntry.id == entry_id)
        )
        entry = result.scalars().first()

        if not entry:
            raise ValueError("Ledger entry not found")

        if entry.status != "draft":
            raise ValueError("Entry already posted")

        if entry.debit_amount != entry.credit_amount:
            raise ValueError("Debit and credit amounts must match")

        entry.status = "posted"
        entry.posted_at = datetime.utcnow().isoformat()
        await db.commit()

        return {"entry_id": entry.id, "status": "posted"}

    @staticmethod
    async def generate_einvoice(
        folio_id: UUID, customer_name: str, customer_email: str, total_amount: Decimal, db: AsyncSession
    ) -> dict:
        """e-Fatura oluştur."""
        invoice_number = f"2026{int(datetime.utcnow().timestamp()) % 100000:05d}"

        kdv = total_amount * Decimal("0.18")
        subtotal = total_amount / Decimal("1.18")

        invoice = EInvoice(
            invoice_number=invoice_number,
            invoice_date=datetime.utcnow().date().isoformat(),
            customer_name=customer_name,
            customer_email=customer_email,
            subtotal=subtotal,
            kdv_amount=kdv,
            total_amount=total_amount,
            einvoice_status="generated",
            source_folio_id=folio_id,
            created_by=UUID(int=0),
        )

        db.add(invoice)
        await db.commit()

        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice_number,
            "status": "generated",
            "total": float(total_amount),
        }
