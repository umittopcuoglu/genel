from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


# ── BlockchainIdentity ──

class BlockchainIdentityResponse(BaseModel):
    id: UUID
    guest_id: UUID
    did: str
    method: str
    public_key: str
    status: str
    chain_tx_hash: Optional[str] = None
    is_verified: bool
    verified_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class BlockchainIdentityCreate(BaseModel):
    guest_id: UUID
    method: str = "polygon"
    metadata: Optional[dict] = None


# ── VerifiableCredential ──

class VerifiableCredentialResponse(BaseModel):
    id: UUID
    identity_id: UUID
    credential_type: str
    credential_data: dict
    issuer_did: str
    subject_did: str
    issuance_date: datetime
    expiration_date: Optional[datetime] = None
    proof_type: str
    chain_tx_hash: Optional[str] = None
    status: str
    is_revoked: bool

    class Config:
        from_attributes = True


class VerifiableCredentialIssue(BaseModel):
    identity_id: UUID
    credential_type: str = Field(..., max_length=50)
    credential_data: dict
    expiration_date: Optional[datetime] = None


# ── IdentityVerificationProof ──

class IdentityVerificationProofResponse(BaseModel):
    id: UUID
    identity_id: UUID
    verifier_id: str
    verification_type: str
    disclosed_fields: dict
    status: str
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IdentityVerificationRequest(BaseModel):
    identity_id: UUID
    verification_type: str = Field(..., max_length=30)
    disclosed_fields: dict
    verifier_id: str


# ── BlockchainSyncEvent ──

class BlockchainSyncEventResponse(BaseModel):
    id: UUID
    event_type: str
    entity_type: str
    entity_id: str
    chain_tx_hash: str
    chain_id: str
    block_number: Optional[int] = None
    status: str
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── GuestConsentLog ──

class GuestConsentLogResponse(BaseModel):
    id: UUID
    guest_id: UUID
    consent_type: str
    is_granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    consent_version: str
    ip_address: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class GuestConsentCreate(BaseModel):
    guest_id: UUID
    consent_type: str = Field(..., max_length=30)
    is_granted: bool = True
    ip_address: Optional[str] = None
    notes: Optional[str] = None
