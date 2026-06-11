#!/usr/bin/env python3
"""DeepSeek API istemcisi — HotelOps orkestratörü için.

Repo kökündeki .env dosyasından DEEPSEEK_API_KEY okur.
DeepSeek erişilemezse OPENROUTER_API_KEY ile OpenRouter'a düşer (fallback).
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "deepseek/deepseek-chat"  # OpenRouter üzerinden aynı model


def load_env() -> None:
    """Repo kökündeki .env dosyasını ortam değişkenlerine yükler (varsa)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _post(url: str, headers: dict, payload: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.2,
         max_retries: int = 3) -> str:
    """DeepSeek'e mesaj gönderir, yanıt metnini döner.

    Sıra: DeepSeek API → (başarısızsa) OpenRouter → (o da yoksa) RuntimeError.
    Çağıran taraf manuel moda düşebilir (run_task.py --manual).
    """
    load_env()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    providers = []
    if os.getenv("DEEPSEEK_API_KEY"):
        providers.append((
            DEEPSEEK_URL,
            {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
            DEEPSEEK_MODEL,
        ))
    if os.getenv("OPENROUTER_API_KEY"):
        providers.append((
            OPENROUTER_URL,
            {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            OPENROUTER_MODEL,
        ))
    if not providers:
        raise RuntimeError(
            ".env içinde DEEPSEEK_API_KEY veya OPENROUTER_API_KEY bulunamadı."
        )

    last_error: Exception | None = None
    for url, headers, model in providers:
        for attempt in range(max_retries):
            try:
                data = _post(url, headers, {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 8192,
                })
                return data["choices"][0]["message"]["content"]
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as exc:
                last_error = exc
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Tüm sağlayıcılar başarısız oldu: {last_error}")


if __name__ == "__main__":
    # Hızlı bağlantı testi: python orchestrator/deepseek_client.py
    try:
        reply = chat("Kısa cevap ver.", "Merhaba, çalışıyor musun? Tek kelime: evet/hayır")
        print(f"✅ Bağlantı OK — yanıt: {reply[:100]}")
    except RuntimeError as exc:
        print(f"❌ Bağlantı yok: {exc}")
        print("→ Manuel mod kullanın: python orchestrator/run_task.py TASK-001 --manual")
