"""
Blockchain router: DID, VC, Verification Proof, Sync Event, Consent endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.blockchain_identity import (
    BlockchainIdentityCreate,
    BlockchainIdentityResponse,
    VerifiableCredentialIssue,
    VerifiableCredentialResponse,
    IdentityVerificationRequest,
    IdentityVerificationProofResponse,
    BlockchainSyncEventResponse,
    GuestConsentCreate,
    GuestConsentLogResponse,
)
from app.services.blockchain_service import BlockchainService

router = APIRouter(prefix="/api/v1/blockchain", tags=["Blockchain Identity"])


# ── DID Endpoints ──

@router.post("/identities", response_model=BlockchainIdentityResponse, status_code=status.HTTP_201_CREATED)
async def create_did(
    data: BlockchainIdentityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Misafir için DID oluştur."""
    return await BlockchainService.create_did(db, data, {"user_id": str(current_user.id)})


@router.get("/identities", response_model=List[BlockchainIdentityResponse])
async def list_identities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Tüm DID'leri listele."""
    return await BlockchainService.list_identities(db)


@router.get("/identities/{identity_id}", response_model=BlockchainIdentityResponse)
async def get_identity(
    identity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """DID detayını getir."""
    identity = await BlockchainService.get_identity(db, identity_id)
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kimlik bulunamadı")
    return identity


@router.get("/identities/guest/{guest_id}", response_model=BlockchainIdentityResponse)
async def get_identity_by_guest(
    guest_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Misafir ID'sine göre DID getir."""
    identity = await BlockchainService.get_identity_by_guest(db, guest_id)
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu misafir için kimlik bulunamadı")
    return identity


@router.post("/identities/{identity_id}/verify", response_model=BlockchainIdentityResponse)
async def verify_identity(
    identity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """DID doğrula."""
    identity = await BlockchainService.verify_identity(db, identity_id, {"user_id": str(current_user.id)})
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kimlik bulunamadı")
    return identity


# ── VC Endpoints ──

@router.post("/credentials", response_model=VerifiableCredentialResponse, status_code=status.HTTP_201_CREATED)
async def issue_credential(
    data: VerifiableCredentialIssue,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Doğrulanabilir kimlik bilgisi (VC) oluştur."""
    try:
        return await BlockchainService.issue_credential(db, data, {"user_id": str(current_user.id)})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/credentials", response_model=List[VerifiableCredentialResponse])
async def list_credentials(
    identity_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """VC'leri listele."""
    return await BlockchainService.list_credentials(db, identity_id=identity_id)


@router.post("/credentials/{credential_id}/revoke", response_model=VerifiableCredentialResponse)
async def revoke_credential(
    credential_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """VC'yi iptal et."""
    vc = await BlockchainService.revoke_credential(db, credential_id, {"user_id": str(current_user.id)})
    if not vc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VC bulunamadı")
    return vc


# ── Verification Proof Endpoints ──

@router.post("/verifications", response_model=IdentityVerificationProofResponse, status_code=status.HTTP_201_CREATED)
async def create_verification(
    data: IdentityVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Kimlik doğrulama ispatı oluştur."""
    return await BlockchainService.create_verification_proof(db, data, {"user_id": str(current_user.id)})


@router.get("/verifications", response_model=List[IdentityVerificationProofResponse])
async def list_verifications(
    identity_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Doğrulama ispatlarını listele."""
    return await BlockchainService.list_verification_proofs(db, identity_id=identity_id)


# ── Sync Events Endpoints ──

@router.get("/sync-events", response_model=List[BlockchainSyncEventResponse])
async def list_sync_events(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Blockchain senkronizasyon olaylarını listele."""
    return await BlockchainService.list_sync_events(db, limit=limit)


# ── Consent Endpoints ──

@router.post("/consent", response_model=GuestConsentLogResponse, status_code=status.HTTP_201_CREATED)
async def log_consent(
    data: GuestConsentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Misafir izin/rıza kaydı oluştur."""
    return await BlockchainService.log_consent(db, data, {"user_id": str(current_user.id)})


@router.get("/consent", response_model=List[GuestConsentLogResponse])
async def list_consents(
    guest_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """İzin kayıtlarını listele."""
    return await BlockchainService.list_consents(db, guest_id=guest_id)
