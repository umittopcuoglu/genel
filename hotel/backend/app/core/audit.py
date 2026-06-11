"""
Audit Middleware: Tüm POST/PUT/PATCH/DELETE isteklerini audit_log tablosuna kaydeder.
Ayrıca context üzerinden current_user bilgisini model layer'a iletmek için kullanılır.
"""
import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import AsyncSessionLocal
from app.models.audit import AuditLog
from app.core.auth import get_current_user  # doğrudan çağıramayız, dependency var
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Context variable for current user (model events için)
from contextvars import ContextVar
current_user_id_var: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


class AuditMiddleware(BaseHTTPMiddleware):
    """Yazma işlemlerini yakalayıp audit_log'a ekler."""

    async def dispatch(self, request: Request, call_next):
        # Sadece yazma metodlarını işle
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)

        # Request body'yi oku (tekrar kullanılabilir hale getir)
        body_bytes = await request.body()
        # Orijinal request'in body'sini restore et
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        # İstek bilgilerini al
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        # user_id'yi belirlemeye çalış (token'dan)
        user_id = None
        try:
            # Token'ı header'dan al
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                from app.core.auth import verify_token
                payload = await verify_token(token, token_type="access")
                user_id = payload.get("sub")
        except Exception:
            pass

        # Audit log kaydı için kullanıcı ID'sini context'e set et
        token = current_user_id_var.set(user_id)

        # Yanıtı al
        response = await call_next(request)

        # Sadece başarılı yanıtlarda (2xx) logla
        if 200 <= response.status_code < 300:
            # Request body'yi decode et (JSON ise)
            body_str = body_bytes.decode("utf-8", errors="ignore")
            try:
                body_json = json.loads(body_str)
                # Hassas verileri maskeleme (parola vb.)
                if "password" in body_json:
                    body_json["password"] = "***REDACTED***"
                body_for_log = json.dumps(body_json, ensure_ascii=False)
            except:
                body_for_log = body_str[:1000]  # Çok uzunsa kes

            # Audit log'u asenkron olarak kaydet (background task olabilir ama basitçe burada)
            try:
                async with AsyncSessionLocal() as db_session:
                    audit_entry = AuditLog(
                        user_id=user_id,
                        action=method,
                        resource=path,
                        old_value=None,  # Middleware için eski değer zor, basit bırakıyoruz
                        new_value=body_for_log,
                        ip_address=client_ip,
                        user_agent=request.headers.get("user-agent", "")[:255]
                    )
                    db_session.add(audit_entry)
                    await db_session.commit()
            except Exception as e:
                logger.error(f"Audit log kaydedilemedi: {e}")

        # Context'i temizle
        current_user_id_var.reset(token)

        return response


# Yardımcı fonksiyon: Model layer'da current user id'yi almak için
def get_current_user_id_from_context() -> Optional[str]:
    """Context'teki mevcut kullanıcı ID'sini döndürür. Model olaylarında kullanılır."""
    return current_user_id_var.get()
