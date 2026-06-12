"""
Blockchain Identity servisi: DID yönetimi, VC issue/verify, ispat, consent.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from random import randint, choice
import secrets
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.blockchain_identity import (
    BlockchainIdentity, VerifiableCredential, IdentityVerificationProof,
    BlockchainSyncEvent, GuestConsentLog,
)
from app.schemas.blockchain_identity import (
    BlockchainIdentityCreate,
    VerifiableCredentialIssue,
    IdentityVerificationRequest,
    GuestConsentCreate,
)


class BlockchainService:
    """Blockchain tabanlı SSI (Self-Sovereign Identity) iş mantığı."""

    # ── DID (Decentralized Identifier) ──

    @staticmethod
    async def create_did(db: AsyncSession, data: BlockchainIdentityCreate, current_user: dict) -> BlockchainIdentity:
        """Misafir için DID oluştur (mock)."""
        # Mock DID üretimi
        public_key = hashlib.sha256(f"{data.guest_id}-{secrets.token_hex(16)}".encode()).hexdigest()
        did = f"did:polygon:0x{public_key[:40]}"

        tx_hash = hashlib.sha256(f"CREATE_DID_{did}_{datetime.now().isoformat()}".encode()).hexdigest()

        identity = BlockchainIdentity(
            guest_id=data.guest_id,
            did=did,
            method=data.method,
            public_key=public_key,
            status="active",
            chain_tx_hash=f"0x{tx_hash}",
            extra_metadata=data.extra_metadata,
            created_by=current_user.get("user_id"),
        )
        db.add(identity)

        # Sync event
        sync = BlockchainSyncEvent(
            event_type="did_created",
            entity_type="identity",
            entity_id=identity.id,
            chain_tx_hash=f"0x{tx_hash}",
            chain_id="polygon-mumbai",
            block_number=randint(40000000, 50000000),
            status="confirmed",
            confirmed_at=datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(sync)
        await db.commit()
        await db.refresh(identity)
        return identity

    @staticmethod
    async def get_identity(db: AsyncSession, identity_id: UUID) -> Optional[BlockchainIdentity]:
        stmt = select(BlockchainIdentity).where(BlockchainIdentity.id == identity_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_identity_by_guest(db: AsyncSession, guest_id: UUID) -> Optional[BlockchainIdentity]:
        stmt = select(BlockchainIdentity).where(BlockchainIdentity.guest_id == guest_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_identity_by_did(db: AsyncSession, did: str) -> Optional[BlockchainIdentity]:
        stmt = select(BlockchainIdentity).where(BlockchainIdentity.did == did)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_identity(db: AsyncSession, identity_id: UUID, current_user: dict) -> Optional[BlockchainIdentity]:
        identity = await BlockchainService.get_identity(db, identity_id)
        if not identity:
            return None
        identity.is_verified = True
        identity.verified_at = datetime.now()
        identity.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(identity)
        return identity

    @staticmethod
    async def list_identities(db: AsyncSession) -> list[BlockchainIdentity]:
        stmt = select(BlockchainIdentity).order_by(BlockchainIdentity.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── VC (Verifiable Credential) ──

    @staticmethod
    async def issue_credential(db: AsyncSession, data: VerifiableCredentialIssue, current_user: dict) -> VerifiableCredential:
        """Doğrulanabilir kimlik bilgisi oluştur (mock)."""
        identity = await BlockchainService.get_identity(db, data.identity_id)
        if not identity:
            raise ValueError("Kimlik bulunamadı")

        # W3C VC formatı
        vc_data = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", data.credential_type],
            "issuer": f"did:polygon:hotelops",
            "issuanceDate": datetime.now().isoformat(),
            "credentialSubject": {
                "id": identity.did,
                **data.credential_data,
            },
        }

        proof_value = hashlib.sha256(f"{vc_data}{secrets.token_hex(8)}".encode()).hexdigest()
        tx_hash = hashlib.sha256(f"ISSUE_VC_{data.identity_id}_{datetime.now().isoformat()}".encode()).hexdigest()

        vc = VerifiableCredential(
            identity_id=data.identity_id,
            credential_type=data.credential_type,
            credential_data=vc_data,
            issuer_did="did:polygon:hotelops",
            subject_did=identity.did,
            issuance_date=datetime.now(),
            expiration_date=data.expiration_date,
            proof_type="Ed25519Signature2020",
            proof_value=proof_value,
            chain_tx_hash=f"0x{tx_hash}",
            status="active",
            created_by=current_user.get("user_id"),
        )
        db.add(vc)

        # Sync event
        sync = BlockchainSyncEvent(
            event_type="vc_issued",
            entity_type="credential",
            entity_id=vc.id,
            chain_tx_hash=vc.chain_tx_hash,
            chain_id="polygon-mumbai",
            block_number=randint(40000000, 50000000),
            status="confirmed",
            confirmed_at=datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(sync)
        await db.commit()
        await db.refresh(vc)
        return vc

    @staticmethod
    async def revoke_credential(db: AsyncSession, credential_id: UUID, current_user: dict) -> Optional[VerifiableCredential]:
        stmt = select(VerifiableCredential).where(VerifiableCredential.id == credential_id)
        result = await db.execute(stmt)
        vc = result.scalar_one_or_none()
        if not vc:
            return None
        vc.is_revoked = True
        vc.status = "revoked"
        vc.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(vc)
        return vc

    @staticmethod
    async def list_credentials(db: AsyncSession, identity_id: Optional[UUID] = None) -> list[VerifiableCredential]:
        stmt = select(VerifiableCredential)
        if identity_id:
            stmt = stmt.where(VerifiableCredential.identity_id == identity_id)
        stmt = stmt.order_by(VerifiableCredential.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Verification Proof ──

    @staticmethod
    async def create_verification_proof(db: AsyncSession, data: IdentityVerificationRequest, current_user: dict) -> IdentityVerificationProof:
        """Kimlik doğrulama ispatı oluştur (mock)."""
        proof = IdentityVerificationProof(
            identity_id=data.identity_id,
            verifier_id=data.verifier_id,
            verification_type=data.verification_type,
            disclosed_fields=data.disclosed_fields,
            proof_data={
                "challenge": secrets.token_hex(16),
                "signature": hashlib.sha256(f"{data.identity_id}{datetime.now()}".encode()).hexdigest(),
                "verified_at": datetime.now().isoformat(),
            },
            status="verified",
            verified_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            created_by=current_user.get("user_id"),
        )
        db.add(proof)

        sync = BlockchainSyncEvent(
            event_type="identity_verified",
            entity_type="proof",
            entity_id=proof.id,
            chain_tx_hash=f"0x{hashlib.sha256(f'VERIFY_{proof.id}'.encode()).hexdigest()}",
            chain_id="polygon-mumbai",
            block_number=randint(40000000, 50000000),
            status="confirmed",
            confirmed_at=datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(sync)
        await db.commit()
        await db.refresh(proof)
        return proof

    @staticmethod
    async def list_verification_proofs(db: AsyncSession, identity_id: Optional[UUID] = None) -> list[IdentityVerificationProof]:
        stmt = select(IdentityVerificationProof)
        if identity_id:
            stmt = stmt.where(IdentityVerificationProof.identity_id == identity_id)
        stmt = stmt.order_by(IdentityVerificationProof.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Sync Events ──

    @staticmethod
    async def list_sync_events(db: AsyncSession, limit: int = 50) -> list[BlockchainSyncEvent]:
        stmt = select(BlockchainSyncEvent).order_by(BlockchainSyncEvent.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Guest Consent ──

    @staticmethod
    async def log_consent(db: AsyncSession, data: GuestConsentCreate, current_user: dict) -> GuestConsentLog:
        consent = GuestConsentLog(
            guest_id=data.guest_id,
            consent_type=data.consent_type,
            is_granted=data.is_granted,
            granted_at=datetime.now() if data.is_granted else None,
            revoked_at=datetime.now() if not data.is_granted else None,
            ip_address=data.ip_address,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(consent)
        await db.commit()
        await db.refresh(consent)
        return consent

    @staticmethod
    async def list_consents(db: AsyncSession, guest_id: Optional[UUID] = None) -> list[GuestConsentLog]:
        stmt = select(GuestConsentLog)
        if guest_id:
            stmt = stmt.where(GuestConsentLog.guest_id == guest_id)
        stmt = stmt.order_by(GuestConsentLog.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
