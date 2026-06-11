"""Temel API sözleşme testleri — 02_DEEPSEEK_TALIMATLARI.md §0 ve §15'e göre.

Claude tarafından yazılmıştır; DeepSeek'in teslimatı bu testlerden geçmek zorundadır.
"""
import json
import urllib.error
import urllib.request

import pytest

from conftest import requires_backend


def get(base_url: str, path: str, token: str | None = None):
    req = urllib.request.Request(f"{base_url}{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


@requires_backend
class TestGenelSozlesme:
    """§0 Genel kurallar: hata zarfı, auth zorunluluğu, OpenAPI."""

    def test_health_endpoint_var(self, base_url):
        status, _ = get(base_url, "/api/v1/health")
        assert status == 200

    def test_openapi_spec_yayinda(self, base_url):
        status, spec = get(base_url, "/openapi.json")
        assert status == 200
        assert spec.get("openapi", "").startswith("3.")

    def test_korunan_endpoint_tokensiz_401(self, base_url):
        status, body = get(base_url, "/api/v1/rooms")
        assert status == 401
        # §0.7 hata zarfı: { "error": { "code", "message" } }
        assert "error" in body, f"Hata zarfı yok: {body}"
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_olmayan_kaynak_404_zarfli(self, base_url):
        status, body = get(base_url, "/api/v1/olmayan-kaynak-xyz")
        assert status == 404
        assert "error" in body


@requires_backend
class TestListeZarfi:
    """§15: tüm liste endpoint'leri { data: [...], meta: {...} } döner."""

    @pytest.mark.parametrize("path", [
        "/api/v1/rooms",
        "/api/v1/arrivals?date=2026-06-11",
        "/api/v1/departures?date=2026-06-11",
    ])
    def test_liste_zarfi(self, base_url, path, auth_token=None):
        # Token'lı senaryo TASK-001 (auth) teslim edilince genişletilecek;
        # şimdilik zarf kontrolü 401 olmayan durumlar için yapılır.
        status, body = get(base_url, path)
        if status == 200:
            assert "data" in body and "meta" in body
            assert {"page", "per_page", "total"} <= set(body["meta"].keys())
