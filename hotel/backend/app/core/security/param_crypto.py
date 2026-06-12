"""
Entegrasyon parametreleri için simetrik şifreleme (Fernet/AES-128-CBC+HMAC).
Anahtar JWT_SECRET_KEY'den SHA-256 ile türetilir — ayrı anahtar yönetimi
istenirse INTEGRATION_CRYPT_KEY env değişkeni ile geçersiz kılınabilir.
"""
import base64
import hashlib
import json
import os

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    raw = os.environ.get("INTEGRATION_CRYPT_KEY") or settings.JWT_SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return Fernet(key)


def encrypt_params(params: dict) -> str:
    """Parametre sözlüğünü şifreli metne çevirir."""
    return _fernet().encrypt(json.dumps(params, ensure_ascii=False).encode()).decode()


def decrypt_params(token: str) -> dict:
    """Şifreli metni parametre sözlüğüne çevirir; bozuk/boşsa {} döner."""
    if not token:
        return {}
    try:
        return json.loads(_fernet().decrypt(token.encode()).decode())
    except (InvalidToken, ValueError):
        return {}


# Yanıtlarda maskelenecek hassas alan adları (alt dize eşleşmesi)
SENSITIVE_KEYS = ("password", "secret", "token", "api_key", "apikey", "key", "credential")


def mask_params(params: dict) -> dict:
    """Hassas değerleri son 4 karakter görünür kalacak şekilde maskeler."""
    masked = {}
    for k, v in params.items():
        if isinstance(v, str) and v and any(s in k.lower() for s in SENSITIVE_KEYS):
            masked[k] = ("•" * 8 + v[-4:]) if len(v) > 4 else "•" * 8
        else:
            masked[k] = v
    return masked
