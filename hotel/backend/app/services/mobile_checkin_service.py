"""
Mobile Check-in servisi: OCR, yüz tanıma, EGM, NFC oda anahtarı.
"""
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID
from random import uniform, randint, choice
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.mobile_checkin import (
    OCRDocumentScan, EGMSubmission, CheckinSession,
    FacialRecognitionScan, NFCRoomKey,
)
from app.schemas.mobile_checkin import (
    OCRDocumentScanCreate,
    CheckinSessionStart,
    NFCRoomKeyIssue,
)


class MobileCheckinService:
    """Mobil check-in iş mantığı."""

    # ── Checkin Session ──

    @staticmethod
    async def start_session(db: AsyncSession, data: CheckinSessionStart, current_user: dict) -> CheckinSession:
        """Check-in oturumu başlat."""
        token = secrets.token_urlsafe(48)
        session = CheckinSession(
            reservation_id=data.reservation_id,
            guest_id=data.guest_id,
            session_token=token,
            status="started",
            device_info=data.device_info,
            ip_address=data.ip_address or "0.0.0.0",
            started_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            created_by=current_user.get("user_id"),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: UUID) -> Optional[CheckinSession]:
        stmt = select(CheckinSession).where(CheckinSession.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_by_token(db: AsyncSession, token: str) -> Optional[CheckinSession]:
        stmt = select(CheckinSession).where(CheckinSession.session_token == token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session_status(db: AsyncSession, session_id: UUID, status: str, current_user: dict) -> Optional[CheckinSession]:
        session = await MobileCheckinService.get_session(db, session_id)
        if not session:
            return None
        session.status = status
        if status == "completed":
            session.completed_at = datetime.now()
        session.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def list_sessions(db: AsyncSession, status: Optional[str] = None) -> list[CheckinSession]:
        stmt = select(CheckinSession)
        if status:
            stmt = stmt.where(CheckinSession.status == status)
        stmt = stmt.order_by(CheckinSession.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── OCR ──

    @staticmethod
    async def scan_document(db: AsyncSession, data: OCRDocumentScanCreate, current_user: dict) -> OCRDocumentScan:
        """OCR belge taraması kaydet (mock)."""
        doc = OCRDocumentScan(
            guest_id=data.guest_id,
            scan_type=data.scan_type,
            document_number=data.document_number,
            issuing_country=data.issuing_country,
            nationality=data.nationality,
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            document_expiry=data.document_expiry,
            scan_confidence=uniform(85, 99),
            raw_ocr_result={
                "mrz_parsed": True,
                "fields_extracted": 12,
                "confidence_details": {"document_number": 0.98, "name": 0.95, "dob": 0.92},
            },
            created_by=current_user.get("user_id"),
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def list_document_scans(db: AsyncSession, guest_id: Optional[UUID] = None) -> list[OCRDocumentScan]:
        stmt = select(OCRDocumentScan)
        if guest_id:
            stmt = stmt.where(OCRDocumentScan.guest_id == guest_id)
        stmt = stmt.order_by(OCRDocumentScan.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Facial Recognition ──

    @staticmethod
    async def scan_face(db: AsyncSession, session_id: UUID, guest_id: UUID, current_user: dict) -> FacialRecognitionScan:
        """Yüz taraması yap (mock)."""
        confidence = round(uniform(85, 99), 2)
        match_score = round(uniform(80, 99), 2)

        scan = FacialRecognitionScan(
            session_id=session_id,
            guest_id=guest_id,
            scan_type="selfie",
            confidence_score=confidence,
            match_score=match_score,
            is_match=match_score >= 75,
            raw_result={
                "face_detected": True,
                "liveness_detected": True,
                "quality_score": round(uniform(0.8, 0.99), 2),
            },
            scanned_at=datetime.now(),
        )
        db.add(scan)

        # Session durumunu güncelle
        await MobileCheckinService.update_session_status(db, session_id, "face_completed", current_user)

        await db.commit()
        await db.refresh(scan)
        return scan

    @staticmethod
    async def list_face_scans(db: AsyncSession, session_id: UUID) -> list[FacialRecognitionScan]:
        stmt = select(FacialRecognitionScan).where(FacialRecognitionScan.session_id == session_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── EGM ──

    @staticmethod
    async def submit_egm(db: AsyncSession, stay_id: UUID, guest_id: UUID, current_user: dict) -> EGMSubmission:
        """EGM bildirimi gönder (mock)."""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<EGM_Bildirim>
    <IslemTuru>GIRIS</IslemTuru>
    <TesisKodu>MOCK001</TesisKodu>
    <Musteri>
        <Ad>{current_user.get('user_id', 'MOCK')}</Ad>
        <Soyad>TEST</Soyad>
        <KimlikNo>MOCK{randint(10000, 99999)}</KimlikNo>
    </Musteri>
</EGM_Bildirim>"""

        submission = EGMSubmission(
            stay_id=stay_id,
            guest_id=guest_id,
            submission_type="checkin",
            status="submitted",
            xml_payload=xml,
            response_code="00",
            response_message="Başarılı",
            reference_number=f"EGM-{randint(100000, 999999)}",
            submitted_at=datetime.now(),
            raw_request={"endpoint": "https://egm.gov.tr/kayit", "method": "POST"},
            raw_response={"status": "success", "reference": f"EGM-{randint(100000, 999999)}"},
            created_by=current_user.get("user_id"),
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def list_egm_submissions(db: AsyncSession, stay_id: Optional[UUID] = None) -> list[EGMSubmission]:
        stmt = select(EGMSubmission)
        if stay_id:
            stmt = stmt.where(EGMSubmission.stay_id == stay_id)
        stmt = stmt.order_by(EGMSubmission.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── NFC Room Key ──

    @staticmethod
    async def issue_nfc_key(db: AsyncSession, data: NFCRoomKeyIssue, current_user: dict) -> NFCRoomKey:
        """NFC oda anahtarı oluştur (mock)."""
        token = secrets.token_hex(32)
        nfc_key = NFCRoomKey(
            stay_id=data.stay_id,
            room_id=data.room_id,
            guest_id=data.guest_id,
            token=token,
            status="active",
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            device_id=data.device_id,
            created_by=current_user.get("user_id"),
        )
        db.add(nfc_key)
        await db.commit()
        await db.refresh(nfc_key)
        return nfc_key

    @staticmethod
    async def get_nfc_key(db: AsyncSession, key_id: UUID) -> Optional[NFCRoomKey]:
        stmt = select(NFCRoomKey).where(NFCRoomKey.id == key_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_nfc_key(db: AsyncSession, key_id: UUID, current_user: dict) -> Optional[NFCRoomKey]:
        key = await MobileCheckinService.get_nfc_key(db, key_id)
        if not key:
            return None
        key.status = "revoked"
        key.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(key)
        return key

    @staticmethod
    async def list_nfc_keys(db: AsyncSession, stay_id: Optional[UUID] = None) -> list[NFCRoomKey]:
        stmt = select(NFCRoomKey)
        if stay_id:
            stmt = stmt.where(NFCRoomKey.stay_id == stay_id)
        result = await db.execute(stmt)
        return result.scalars().all()
