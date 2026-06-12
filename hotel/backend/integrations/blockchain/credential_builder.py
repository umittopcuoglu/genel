"""
W3C Verifiable Credential builder.
"""
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class CredentialBuilder:
    """W3C formatında VC oluşturucu."""

    def __init__(self, config: dict):
        self.issuer_did = config.get("issuer_did", "did:polygon:hotelops")
        logger.info(f"CredentialBuilder initialized: issuer={self.issuer_did}")

    async def build_passport_credential(self, subject_did: str, passport_data: dict) -> dict:
        """Pasaport bilgileri için VC oluştur."""
        return self._build_vc(
            subject_did=subject_did,
            credential_type="PassportCredential",
            credential_data={
                "documentNumber": passport_data.get("document_number"),
                "firstName": passport_data.get("first_name"),
                "lastName": passport_data.get("last_name"),
                "nationality": passport_data.get("nationality"),
                "dateOfBirth": passport_data.get("date_of_birth"),
                "issuingCountry": passport_data.get("issuing_country"),
                "expiryDate": passport_data.get("document_expiry"),
            },
            expiration_days=365,
        )

    async def build_loyalty_credential(self, subject_did: str, loyalty_data: dict) -> dict:
        """Sadakat kartı VC'si oluştur."""
        return self._build_vc(
            subject_did=subject_did,
            credential_type="LoyaltyMembership",
            credential_data={
                "memberId": loyalty_data.get("member_id"),
                "tier": loyalty_data.get("tier", "Silver"),
                "points": loyalty_data.get("points", 0),
            },
            expiration_days=365 * 2,
        )

    async def build_age_verification(self, subject_did: str, over_18: bool) -> dict:
        """Yaş doğrulama VC'si (selective disclosure)."""
        return self._build_vc(
            subject_did=subject_did,
            credential_type="AgeVerification",
            credential_data={"over18": over_18, "verifiedBy": "HotelOps"},
            expiration_days=30,
        )

    def _build_vc(self, subject_did: str, credential_type: str, credential_data: dict, expiration_days: int = 365) -> dict:
        """W3C formatında VC oluştur."""
        issuance_date = datetime.now()
        expiration_date = issuance_date + timedelta(days=expiration_days)

        vc = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1",
            ],
            "id": f"urn:uuid:{hashlib.sha256(f'{subject_did}:{credential_type}:{issuance_date.isoformat()}'.encode()).hexdigest()[:36]}",
            "type": ["VerifiableCredential", credential_type],
            "issuer": self.issuer_did,
            "issuanceDate": issuance_date.isoformat(),
            "expirationDate": expiration_date.isoformat(),
            "credentialSubject": {
                "id": subject_did,
                **credential_data,
            },
        }

        # Proof ekle
        vc["proof"] = {
            "type": "Ed25519Signature2020",
            "created": issuance_date.isoformat(),
            "verificationMethod": f"{self.issuer_did}#key-1",
            "proofPurpose": "assertionMethod",
            "jws": f"mock_signature_{hashlib.sha256(json.dumps(vc, sort_keys=True).encode()).hexdigest()[:32]}",
        }

        return vc
