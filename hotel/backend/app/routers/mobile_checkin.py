"""
Mobile Check-in router: Session, OCR, Yüz Tanıma, EGM, NFC anahtar endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.mobile_checkin import (
    CheckinSessionStart,
    CheckinSessionResponse,
    OCRDocumentScanCreate,
    OCRDocumentScanResponse,
    FacialRecognitionScanResponse,
    EGMSubmissionResponse,
    NFCRoomKeyIssue,
    NFCRoomKeyResponse,
)
from app.services.mobile_checkin_service import MobileCheckinService

router = APIRouter(prefix="/api/v1/mobile", tags=["Mobile Check-in"])


# ── Session Endpoints ──

@router.post("/checkin/start", response_model=CheckinSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_checkin(
    data: CheckinSessionStart,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Mobil check-in oturumu başlat."""
    return await MobileCheckinService.start_session(db, data, {"user_id": str(current_user.id)})


@router.get("/checkin/sessions", response_model=List[CheckinSessionResponse])
async def list_sessions(
    status_filter: str = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Check-in oturumlarını listele."""
    return await MobileCheckinService.list_sessions(db, status=status_filter)


@router.get("/checkin/sessions/{session_id}", response_model=CheckinSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Check-in oturumu detayını getir."""
    session = await MobileCheckinService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oturum bulunamadı")
    return session


@router.post("/checkin/sessions/{session_id}/complete", response_model=CheckinSessionResponse)
async def complete_checkin(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Check-in işlemini tamamla."""
    session = await MobileCheckinService.update_session_status(db, session_id, "completed", {"user_id": str(current_user.id)})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oturum bulunamadı")
    return session


# ── OCR Endpoints ──

@router.post("/ocr/scan", response_model=OCRDocumentScanResponse, status_code=status.HTTP_201_CREATED)
async def scan_document(
    data: OCRDocumentScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Belge tara (pasaport/kimlik)."""
    return await MobileCheckinService.scan_document(db, data, {"user_id": str(current_user.id)})


@router.get("/ocr/scans", response_model=List[OCRDocumentScanResponse])
async def list_document_scans(
    guest_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Taranan belgeleri listele."""
    return await MobileCheckinService.list_document_scans(db, guest_id=guest_id)


# ── Face Recognition Endpoints ──

@router.post("/checkin/sessions/{session_id}/face", response_model=FacialRecognitionScanResponse)
async def scan_face(
    session_id: UUID,
    guest_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Yüz taraması yap ve belge ile eşleştir."""
    return await MobileCheckinService.scan_face(db, session_id, guest_id, {"user_id": str(current_user.id)})


@router.get("/checkin/sessions/{session_id}/face-scans", response_model=List[FacialRecognitionScanResponse])
async def list_face_scans(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Yüz tarama kayıtlarını listele."""
    return await MobileCheckinService.list_face_scans(db, session_id)


# ── EGM Endpoints ──

@router.post("/egm/submit", response_model=EGMSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_egm(
    stay_id: UUID = Query(...),
    guest_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """EGM bildirimi gönder."""
    return await MobileCheckinService.submit_egm(db, stay_id, guest_id, {"user_id": str(current_user.id)})


@router.get("/egm/submissions", response_model=List[EGMSubmissionResponse])
async def list_egm_submissions(
    stay_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """EGM bildirimlerini listele."""
    return await MobileCheckinService.list_egm_submissions(db, stay_id=stay_id)


# ── NFC Room Key Endpoints ──

@router.post("/nfc/keys", response_model=NFCRoomKeyResponse, status_code=status.HTTP_201_CREATED)
async def issue_nfc_key(
    data: NFCRoomKeyIssue,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """NFC oda anahtarı oluştur."""
    return await MobileCheckinService.issue_nfc_key(db, data, {"user_id": str(current_user.id)})


@router.get("/nfc/keys", response_model=List[NFCRoomKeyResponse])
async def list_nfc_keys(
    stay_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """NFC anahtarlarını listele."""
    return await MobileCheckinService.list_nfc_keys(db, stay_id=stay_id)


@router.post("/nfc/keys/{key_id}/revoke", response_model=NFCRoomKeyResponse)
async def revoke_nfc_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """NFC oda anahtarını iptal et."""
    key = await MobileCheckinService.revoke_nfc_key(db, key_id, {"user_id": str(current_user.id)})
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anahtar bulunamadı")
    return key
