"""Kontrat testleri ortak fixture'ları.

Bu klasör Claude'un bağımsız denetim alanıdır — DeepSeek buraya dosya yazamaz.
Testler çalışan bir backend'e karşı koşar (BACKEND_URL env değişkeni).
Backend ayakta değilse testler SKIP edilir (CI'da docker compose ile ayağa kalkar).
"""
import os

import pytest

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def backend_alive() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(f"{BACKEND_URL}/api/v1/health", timeout=3)
        return True
    except Exception:
        return False


requires_backend = pytest.mark.skipif(
    not backend_alive(),
    reason=f"Backend ayakta değil ({BACKEND_URL}) — docker compose up gerekli",
)


@pytest.fixture(scope="session")
def base_url() -> str:
    return BACKEND_URL
