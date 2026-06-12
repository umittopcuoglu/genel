"""
Mobile Check-in modelleri: OCR pasaport tarama, EGM bildirimi, yüz tanıma, NFC oda anahtarı.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Boolean, Text, Float, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OCRDocumentScan(BaseModel):
    """OCR ile taranan kimlik/pasaport belgesi."""
    __tablename__ = "ocr_document_scans"

    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    scan_type: Mapped[str] = mapped_column(String(20), nullable=False)  # passport, national_id, drivers_license
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    issuing_country: Mapped[str] = mapped_column(String(50), nullable=True)
    nationality: Mapped[str] = mapped_column(String(50), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    document_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mrz_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scan_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_ocr_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<OCRDocumentScan {self.scan_type}: {self.document_number}>"


class EGMSubmission(BaseModel):
    """EGM (Emniyet Genel Müdürlüğü) bildirimi."""
    __tablename__ = "egm_submissions"

    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    property_id: Mapped[str] = mapped_column(String(36), nullable=True)
    submission_type: Mapped[str] = mapped_column(
        String(20), default="checkin", nullable=False
    )  # checkin, checkout, correction
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, submitted, approved, rejected, error
    xml_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    response_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_request: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<EGMSubmission {self.submission_type}: {self.status}>"


class CheckinSession(BaseModel):
    """Mobil check-in oturumu."""
    __tablename__ = "checkin_sessions"

    reservation_id: Mapped[str] = mapped_column(ForeignKey("reservations.id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    session_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="started", nullable=False
    )  # started, ocr_completed, face_completed, egm_submitted, key_issued, completed, expired, cancelled
    device_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CheckinSession {self.id} ({self.status})>"


class FacialRecognitionScan(BaseModel):
    """Yüz tanıma taraması."""
    __tablename__ = "facial_recognition_scans"

    session_id: Mapped[str] = mapped_column(ForeignKey("checkin_sessions.id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    scan_type: Mapped[str] = mapped_column(String(20), default="selfie", nullable=False)  # selfie, live_photo
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # OCR fotoğrafı ile eşleşme
    is_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # yüz vektörü (base64)
    raw_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<FacialRecognitionScan {self.scan_type}: {self.confidence_score}>"


class NFCRoomKey(BaseModel):
    """NFC oda anahtarı (mobil telefon üzerinden)."""
    __tablename__ = "nfc_room_keys"

    stay_id: Mapped[str] = mapped_column(ForeignKey("stays.id"), nullable=False)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, inactive, expired, revoked
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<NFCRoomKey Room {self.room_id} ({self.status})>"
