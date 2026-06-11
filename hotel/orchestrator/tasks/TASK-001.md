---
id: TASK-001
modül: Altyapı / Auth + RBAC + Audit
durum: open
öncelik: critical
tur: 1
---

## Kapsam
HotelOps backend'inin temel iskeleti: FastAPI uygulama yapısı, PostgreSQL bağlantısı,
JWT auth (access 15dk + refresh 7gün), 9 rollü RBAC, audit log altyapısı,
health endpoint'i ve docker-compose ile yerel ayağa kalkma.

## Üretilecek Dosyalar
- backend/app/main.py                  (FastAPI app + global exception handler)
- backend/app/core/config.py           (pydantic-settings; .env'den okur)
- backend/app/core/db.py               (async SQLAlchemy session)
- backend/app/core/auth.py             (JWT üretme/doğrulama, get_current_user)
- backend/app/core/rbac.py             (rol dekoratörü/dependency: require_roles)
- backend/app/core/audit.py            (audit middleware: tüm yazma işlemleri)
- backend/app/models/base.py           (UUID id, created_at, updated_at, created_by, updated_by, deleted_at)
- backend/app/models/user.py           (users + roles)
- backend/app/models/audit.py          (audit_log tablosu — append-only)
- backend/app/schemas/auth.py          (LoginRequest, TokenResponse, vb.)
- backend/app/routers/auth.py          (POST /api/v1/auth/login, /refresh, /logout)
- backend/app/routers/health.py        (GET /api/v1/health)
- backend/migrations/                  (alembic init + ilk migration)
- backend/tests/conftest.py            (async test client + test DB fixture)
- backend/tests/test_auth.py           (login happy/error, refresh, RBAC 403)
- backend/requirements.txt
- backend/docker-compose.yml           (postgres:15 + redis:7 + api)
- backend/.env.example
- backend/seed.py                      (superadmin + 1 manager + 1 frontdesk kullanıcı)
- backend/README.md                    (kurulum: docker compose up → seed → test)

## Endpoint'ler
```
POST /api/v1/auth/login      → { access_token, refresh_token, user: {id, role} }
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/health          → 200 { "status": "ok" }  (auth gerektirmez)
```

## Kabul Kriterleri
- [ ] `docker compose up` + `python seed.py` ile sistem ayağa kalkar
- [ ] Login → access token ile korunan endpoint'e erişim çalışır
- [ ] Yanlış şifre → 401 + `{ "error": { "code": "INVALID_CREDENTIALS", "message": "..." } }`
- [ ] Token'sız korunan endpoint → 401 + hata zarfı
- [ ] Yetkisiz rol → 403 + hata zarfı
- [ ] Tüm POST çağrıları audit_log tablosuna yazılır (kullanıcı, IP, payload, timestamp)
- [ ] `/openapi.json` yayında, Türkçe açıklamalı
- [ ] pytest tamamı yeşil

## Test Beklentileri
- test_auth.py: login happy, login yanlış şifre, refresh, expired token, RBAC 403
- Her test bağımsız (fixture ile temiz DB)

## Bağlam
- RBAC roller: superadmin, manager, frontdesk, housekeeping, accounting, maintenance, fb, hr, guest
- Bu altyapı sonraki tüm modüllerin temelidir; base model sınıfı tüm tablolarca miras alınacak
- Hata zarfı ve liste zarfı 02_DEEPSEEK_TALIMATLARI.md §0 ve §15'te tanımlı
