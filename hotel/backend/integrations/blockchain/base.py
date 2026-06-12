"""
Blockchain entegrasyon base adapter.
"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class TransactionResult(BaseModel):
    """Blockchain işlem sonucu."""
    tx_hash: str
    block_number: int
    status: str  # pending, confirmed, failed
    gas_used: Optional[int] = None


class BlockchainAdapter(ABC):
    """Blockchain entegrasyonu için base adapter."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def create_did(self, public_key: str, metadata: Optional[dict] = None) -> TransactionResult:
        """DID oluşturma işlemini zincire yaz."""
        pass

    @abstractmethod
    async def issue_credential(self, vc_hash: str, did: str) -> TransactionResult:
        """VC hash'ini zincire yaz."""
        pass

    @abstractmethod
    async def revoke_credential(self, vc_hash: str) -> TransactionResult:
        """VC'yi iptal et."""
        pass

    @abstractmethod
    async def verify_on_chain(self, tx_hash: str) -> dict:
        """İşlemi zincir üzerinde doğrula."""
        pass
