"""CRM servisi: Guest 360, segmentasyon, kampanya, iletişim geçmişi."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.crm import Campaign, CommunicationLog, GuestNote, Segment
from app.models.feedback import Feedback
from app.models.finance import Folio
from app.models.front_office import Guest, Reservation
from app.models.loyalty_account import LoyaltyAccount


class CRMService:
    # ── Guest 360 ──

    @staticmethod
    async def guest_360(db: AsyncSession, guest_id: UUID) -> dict:
        guest = await db.get(Guest, guest_id)
        if guest is None:
            raise ValueError("Misafir bulunamadı")

        # Konaklama istatistikleri
        stays_res = await db.execute(
            select(func.count(Reservation.id), func.max(Reservation.check_out))
            .where(Reservation.guest_id == guest_id, Reservation.deleted_at.is_(None))
        )
        total_stays, last_stay = stays_res.first() or (0, None)

        # Gelir (kapanmış folio'lardan)
        rev_res = await db.execute(
            select(func.coalesce(func.sum(Folio.total), 0))
            .where(Folio.guest_id == guest_id, Folio.deleted_at.is_(None))
        )
        total_revenue = float(rev_res.scalar() or 0)

        # Loyalty
        loy_res = await db.execute(select(LoyaltyAccount).where(LoyaltyAccount.guest_id == guest_id))
        loy = loy_res.scalars().first()

        # Şikayet ve geri bildirim
        comp_res = await db.execute(
            select(func.count(Complaint.id))
            .where(Complaint.guest_id == guest_id, Complaint.status != "resolved")
        )
        open_complaints = comp_res.scalar() or 0

        fb_res = await db.execute(
            select(func.avg(Feedback.rating)).where(Feedback.guest_id == guest_id)
        )
        avg_fb = fb_res.scalar()

        # Notlar / iletişim sayısı
        notes_res = await db.execute(
            select(func.count(GuestNote.id))
            .where(GuestNote.guest_id == guest_id, GuestNote.deleted_at.is_(None))
        )
        comm_res = await db.execute(
            select(func.count(CommunicationLog.id))
            .where(CommunicationLog.guest_id == guest_id, CommunicationLog.deleted_at.is_(None))
        )

        nightly = total_revenue / total_stays if total_stays else 0.0

        return {
            "guest_id": guest.id,
            "full_name": f"{guest.first_name} {guest.last_name}",
            "email": guest.email,
            "phone": guest.phone,
            "is_vip": bool(guest.is_vip),
            "total_stays": int(total_stays),
            "total_revenue": float(total_revenue),
            "avg_nightly_rate": float(round(nightly, 2)),
            "loyalty_tier": loy.tier if loy else None,
            "loyalty_points": int(loy.available_points) if loy else 0,
            "last_stay_date": last_stay,
            "open_complaints": int(open_complaints),
            "avg_feedback_score": float(avg_fb) if avg_fb is not None else None,
            "notes_count": int(notes_res.scalar() or 0),
            "communications_count": int(comm_res.scalar() or 0),
        }

    # ── Segment ──

    @staticmethod
    async def evaluate_segment(db: AsyncSession, criteria: dict) -> list[Guest]:
        """Kriterlere uyan misafirleri döndürür.

        Desteklenen kriterler:
          - min_stays: int
          - min_lifetime_revenue: float
          - tiers: list[str]
          - is_vip: bool
        """
        # Loyalty + stay agregasyonu olan misafirleri bul
        stmt = select(
            Guest,
            func.coalesce(func.count(Reservation.id), 0).label("stay_count"),
            func.coalesce(func.sum(Folio.total), 0).label("revenue"),
            LoyaltyAccount.tier.label("tier"),
        ).select_from(Guest).outerjoin(
            Reservation, and_(Reservation.guest_id == Guest.id, Reservation.deleted_at.is_(None))
        ).outerjoin(
            Folio, and_(Folio.guest_id == Guest.id, Folio.deleted_at.is_(None))
        ).outerjoin(
            LoyaltyAccount, LoyaltyAccount.guest_id == Guest.id
        ).where(Guest.deleted_at.is_(None)).group_by(Guest.id, LoyaltyAccount.tier)

        if "is_vip" in criteria:
            stmt = stmt.where(Guest.is_vip.is_(bool(criteria["is_vip"])))

        rows = (await db.execute(stmt)).all()
        result: list[Guest] = []
        for guest, stay_count, revenue, tier in rows:
            if "min_stays" in criteria and int(stay_count) < int(criteria["min_stays"]):
                continue
            if "min_lifetime_revenue" in criteria and float(revenue) < float(criteria["min_lifetime_revenue"]):
                continue
            if "tiers" in criteria and (tier or "bronze") not in criteria["tiers"]:
                continue
            result.append(guest)
        return result

    # ── Campaign ──

    @staticmethod
    async def send_campaign(db: AsyncSession, campaign: Campaign) -> Campaign:
        """Kampanyayı segment'teki tüm misafirlere "gönder" (CommunicationLog kayıtları açar).

        Gerçek dış servise (SES, Twilio, Meta) buradan delege edilebilir; şu an
        gönderim mock — her hedef için bir log + sent_count artar.
        """
        if campaign.status not in ("draft", "scheduled"):
            raise ValueError("Sadece taslak veya zamanlanmış kampanya gönderilebilir.")

        criteria: dict = {}
        if campaign.segment_id:
            seg = await db.get(Segment, campaign.segment_id)
            if seg and seg.is_active:
                criteria = seg.criteria or {}

        targets = await CRMService.evaluate_segment(db, criteria)
        campaign.status = "sending"
        await db.flush()

        sent = delivered = failed = 0
        for guest in targets:
            ok = bool(guest.email if campaign.channel == "email" else guest.phone)
            log = CommunicationLog(
                guest_id=guest.id,
                campaign_id=campaign.id,
                channel=campaign.channel,
                direction="outbound",
                subject=campaign.subject,
                body=campaign.body,
                status="delivered" if ok else "failed",
                external_ref=f"CMP-{campaign.id.hex[:8]}-{guest.id.hex[:6]}",
            )
            db.add(log)
            sent += 1
            if ok:
                delivered += 1
            else:
                failed += 1

        campaign.sent_count = sent
        campaign.delivered_count = delivered
        campaign.failed_count = failed
        campaign.status = "sent"
        campaign.sent_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(campaign)
        return campaign
