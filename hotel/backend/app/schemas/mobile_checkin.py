from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from uuid import UUID


# ── OCRDocumentScan ──

class OCRDocumentScanResponse(BaseModel):
    id: UUID
    guest_id: UUID
    scan_type: str
    document_number: str
    issuing_country: Optional[str] = None
    nationality: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    document_expiry: Optional[date] = None
    mrz_text: Optional[str] = None
    scan_confidence: float
    image_path: Optional[str] = None
    raw_ocr_result: Optional[dict] = None
    is_verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OCRDocumentScanCreate(BaseModel):
    guest_id: UUID
    scan_type: str = "passport"
    document_number: str = Field(..., max_length=50)
    issuing_country: Optional[str] = None
    nationality: Optional[str] = None
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    document_expiry: Optional[date] = None
    scan_confidence: float = 0.0
    notes: Optional[str] = None


# ── EGMSubmission ──

class EGMSubmissionResponse(BaseModel):
    id: UUID
    stay_id: UUID
    guest_id: UUID
    property_id: Optional[str] = None
    submission_type: str
    status: str
    xml_payload: Optional[str] = None
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    reference_number: Optional[str] = None
    submitted_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ── CheckinSession ──

class CheckinSessionResponse(BaseModel):
    id: UUID
    reservation_id: UUID
    guest_id: UUID
    session_token: str
    status: str
    device_info: Optional[dict] = None
    ip_address: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CheckinSessionStart(BaseModel):
    reservation_id: UUID
    guest_id: UUID
    device_info: Optional[dict] = None
    ip_address: Optional[str] = None


# ── FacialRecognitionScan ──

class FacialRecognitionScanResponse(BaseModel):
    id: UUID
    session_id: UUID
    guest_id: UUID
    scan_type: str
    confidence_score: float
    match_score: Optional[float] = None
    is_match: bool
    image_path: Optional[str] = None
    scanned_at: datetime

    class Config:
        from_attributes = True


# ── NFCRoomKey ──

class NFCRoomKeyResponse(BaseModel):
    id: UUID
    stay_id: UUID
    room_id: UUID
    guest_id: UUID
    token: str
    status: str
    issued_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    use_count: int
    device_id: Optional[str] = None

    class Config:
        from_attributes = True


class NFCRoomKeyIssue(BaseModel):
    stay_id: UUID
    room_id: UUID
    guest_id: UUID
    device_id: Optional[str] = None
