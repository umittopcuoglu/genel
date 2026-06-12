"""
Polygon blockchain adapter (mock) — instant confirm + SHA256 tx hash.
"""
import logging
import hashlib
from typing import Optional
from random import randint
from datetime import datetime

from integrations.blockchain.base import BlockchainAdapter, TransactionResult

logger = logging.getLogger(__name__)


class PolygonAdapter(BlockchainAdapter):
    """Polygon (MATIC) blockchain mock adapter."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.rpc_url = config.get("rpc_url", "https://polygon-mumbai.g.alchemy.com/v2/mock")
        self.contract_address = config.get("contract_address", "0xMOCK_IDENTITY_CONTRACT")
        logger.info(f"PolygonAdapter initialized: {self.rpc_url[:40]}...")

    async def create_did(self, public_key: str, metadata: Optional[dict] = None) -> TransactionResult:
        """DID oluşturma (mock — SHA256 tx hash)."""
        tx_data = f"CREATE_DID:{public_key}:{datetime.now().isoformat()}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()

        logger.info(f"[Polygon] DID created: 0x{tx_hash[:20]}...")

        return TransactionResult(
            tx_hash=f"0x{tx_hash}",
            block_number=randint(45000000, 50000000),
            status="confirmed",
            gas_used=randint(50000, 150000),
        )

    async def issue_credential(self, vc_hash: str, did: str) -> TransactionResult:
        """VC issue (mock)."""
        tx_data = f"ISSUE_VC:{vc_hash}:{did}:{datetime.now().isoformat()}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()

        logger.info(f"[Polygon] VC issued: 0x{tx_hash[:20]}...")

        return TransactionResult(
            tx_hash=f"0x{tx_hash}",
            block_number=randint(45000000, 50000000),
            status="confirmed",
            gas_used=randint(30000, 100000),
        )

    async def revoke_credential(self, vc_hash: str) -> TransactionResult:
        """VC revoke (mock)."""
        tx_data = f"REVOKE_VC:{vc_hash}:{datetime.now().isoformat()}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()

        logger.info(f"[Polygon] VC revoked: 0x{tx_hash[:20]}...")

        return TransactionResult(
            tx_hash=f"0x{tx_hash}",
            block_number=randint(45000000, 50000000),
            status="confirmed",
            gas_used=randint(20000, 80000),
        )

    async def verify_on_chain(self, tx_hash: str) -> dict:
        """İşlem doğrulama (mock)."""
        logger.info(f"[Polygon] Verifying transaction: {tx_hash[:20]}...")
        return {
            "tx_hash": tx_hash,
            "block_number": randint(45000000, 50000000),
            "status": "confirmed",
            "confirmations": randint(10, 100),
            "timestamp": datetime.now().isoformat(),
        }
