"""
Blockchain Misafir Kimliği (SSI) modelleri: DID, VC, ispat zinciri.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BlockchainIdentity(BaseModel):
    """Misafir'in blockchain üzerindeki merkeziyetsiz kimliği (DID)."""
    __tablename__ = "blockchain_identities"

    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    did: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)  # did:polygon:0x...
    method: Mapped[str] = mapped_column(String(20), default="polygon", nullable=False)  # polygon, ethr, key
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AES-256 encrypted
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, revoked, expired
    chain_tx_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # 'metadata' Declarative API'de rezerve; Python attr extra_metadata, DB kolonu "metadata"
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<BlockchainIdentity {self.did[:30]}...>" if len(self.did) > 30 else f"<BlockchainIdentity {self.did}>"


class VerifiableCredential(BaseModel):
    """W3C formatında doğrulanabilir kimlik bilgisi (VC)."""
    __tablename__ = "verifiable_credentials"

    identity_id: Mapped[str] = mapped_column(ForeignKey("blockchain_identities.id"), nullable=False)
    credential_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PassportCredential, NationalIDCredential, GuestMembership, LoyaltyCard
    credential_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    issuer_did: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_did: Mapped[str] = mapped_column(String(200), nullable=False)
    issuance_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    proof_type: Mapped[str] = mapped_column(String(30), default="Ed25519Signature2020", nullable=False)
    proof_value: Mapped[str] = mapped_column(Text, nullable=False)
    chain_tx_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, revoked, expired
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<VerifiableCredential {self.credential_type} for {self.subject_did[:20]}...>"


class IdentityVerificationProof(BaseModel):
    """Kimlik doğrulama ispat kaydı (selective disclosure)."""
    __tablename__ = "identity_verification_proofs"

    identity_id: Mapped[str] = mapped_column(ForeignKey("blockchain_identities.id"), nullable=False)
    verifier_id: Mapped[str] = mapped_column(String(36), nullable=False)
    verification_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # age_verification, identity_check, membership_verification
    disclosed_fields: Mapped[dict] = mapped_column(JSON, nullable=False)  # hangi alanlar paylaşıldı
    proof_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, verified, rejected, expired
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<IdentityVerificationProof {self.verification_type}: {self.status}>"


class BlockchainSyncEvent(BaseModel):
    """Zincir senkronizasyon olayı (on-chain transaction log)."""
    __tablename__ = "blockchain_sync_events"

    event_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # did_created, vc_issued, vc_revoked, identity_verified
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # identity, credential, proof
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chain_tx_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    chain_id: Mapped[str] = mapped_column(String(20), default="polygon-mumbai", nullable=False)
    block_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", nullable=False
    )  # pending, confirmed, failed
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<BlockchainSyncEvent {self.event_type}: {self.chain_tx_hash[:20]}...>"


class GuestConsentLog(BaseModel):
    """Misafir izin/rıza kaydı (KVKK/GDPR uyumlu)."""
    __tablename__ = "guest_consent_logs"

    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # data_sharing, identity_storage, marketing, blockchain_identity
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_version: Mapped[str] = mapped_column(String(10), default="1.0", nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<GuestConsentLog {self.consent_type}: {'granted' if self.is_granted else 'revoked'}>"
