"""
DID (Decentralized Identifier) üretim servisi — Ed25519 key pair (mock).
"""
import logging
import hashlib
import secrets
from typing import Optional

logger = logging.getLogger(__name__)


class DIDService:
    """
    DID üretim ve yönetim servisi (mock).
    Gerçekte Ed25519 veya secp256k1 key pair kullanılır.
    """

    def __init__(self, config: dict):
        self.method = config.get("method", "polygon")
        self.network = config.get("network", "polygon-mumbai")
        logger.info(f"DIDService initialized: {self.method} @ {self.network}")

    async def generate_key_pair(self) -> dict:
        """Ed25519 key pair üret (mock — SHA256 simülasyonu)."""
        private_seed = secrets.token_bytes(32)
        public_key = hashlib.sha256(private_seed).hexdigest()
        private_key = private_seed.hex()

        logger.info("[DID] Key pair generated (mock Ed25519)")
        return {
            "public_key": public_key,
            "private_key": private_key,
            "algorithm": "Ed25519",
            "key_type": "Ed25519VerificationKey2020",
        }

    async def create_did(self, public_key: str) -> str:
        """DID string oluştur."""
        did = f"did:{self.method}:{public_key[:40]}"
        logger.info(f"[DID] DID created: {did}")
        return did

    async def resolve_did(self, did: str) -> Optional[dict]:
        """DID çözümle (mock — DID Document döndür)."""
        if not did.startswith("did:"):
            return None
        return {
            "did": did,
            "method": self.method,
            "network": self.network,
            "public_key": did.split(":")[-1],
            "authentication": [{"type": "Ed25519SignatureAuthentication2020", "publicKey": did.split(":")[-1]}],
            "service": [{"id": f"{did}#hotelops", "type": "HotelOpsService", "endpoint": "https://api.hotelops.com"}],
        }
