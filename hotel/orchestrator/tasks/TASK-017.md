---
id: TASK-017
modül: 9 (Security & Access Control)
kapsam: erişim kontrol + kartlar + kilitleri + güvenlik olayları + KVKK rızası + veri erişim/silme talepleri + SecureAI
durum: kuyrukta (TASK-001, TASK-007 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-001 (auth, audit), TASK-007 (BaseAgent, registry, PII mask)
---

# TASK-017 — Modül 9: Güvenlik & Erişim Kontrol + SecureAI

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §9. SecureAI tahminleri — bu görevde sadece çekirdek akış.
> Uyum: KVKK (Türk Kişisel Verileri Koruma Kanunu) / GDPR

## 1. Veri Modeli

### `access_logs`
- id (UUID, PK) [BaseModel]
- door_or_zone (VARCHAR 100) — "Room 301" | "Front Lobby" | "Staff Area"
- access_type (VARCHAR 15) — door / zone / gate
- card_number (VARCHAR 50 nullable, PII masked in logs)
- user_id (UUID FK → users.id, nullable personel)
- guest_id (UUID FK → guests.id, nullable misafir)
- entry_time (TIMESTAMP)
- exit_time (TIMESTAMP nullable)
- result (VARCHAR 15) — success / denied / expired / invalid_code / tamper_alarm
- notes (TEXT nullable)
- Index: user_id, guest_id, door_or_zone, entry_time

### `door_locks`
- id (UUID, PK) [BaseModel]
- room_id (UUID FK → rooms.id, nullable)
- location_description (VARCHAR 100) — "Room 301 Door" | "Staff Area Gate"
- lock_type (VARCHAR 30) — electronic / mechanical / rfid
- online_status (VARCHAR 15, default="unknown") — online / offline / error
- last_heartbeat (TIMESTAMP nullable)
- status (VARCHAR 15, default="active") — active / inactive / decommissioned
- notes (TEXT nullable)
- Index: room_id, online_status

### `key_cards`
- id (UUID, PK) [BaseModel]
- card_number (VARCHAR 50, unique, PII masked in UI)
- card_holder_type (VARCHAR 15) — guest / staff
- card_holder_id (UUID FK → guests.id | users.id)
- valid_from_date (DATE)
- valid_to_date (DATE) — check-in → check-out interval otomatik (guest), staff tarafından set
- status (VARCHAR 15, default="active") — active / expired / revoked / lost
- created_at (TIMESTAMP) — BaseModel'den inherit
- revoked_at (TIMESTAMP nullable)
- notes (TEXT nullable)
- Index: card_number, card_holder_type, status

### `incidents`
- id (UUID, PK) [BaseModel]
- incident_type (VARCHAR 30) — unauthorized_access / card_lost / door_forced / repeated_failed_attempts / other
- location (VARCHAR 100)
- severity (INT) — 1 critical … 5 low
- description (TEXT)
- reported_by (UUID FK → users.id)
- assigned_to (UUID FK → users.id nullable, security manager)
- status (VARCHAR 15, default="open") — open / investigating / resolved / closed
- resolved_at (TIMESTAMP nullable)
- notes (TEXT nullable)
- Index: status, severity, incident_type

### `kvkk_consents` (KVKK Rızası Kaydı)
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id)
- consent_type (VARCHAR 50) — data_processing | marketing | thirdparty
- purpose (TEXT) — "Konaklama hizmetinin sağlanması" | "Pazarlama iletişimi"
- granted (BOOLEAN) — rıza verildi mi?
- granted_at (TIMESTAMP nullable)
- revoked_at (TIMESTAMP nullable)
- consent_method (VARCHAR 30) — checkbox | signature | explicit
- notes (TEXT nullable)
- Index: guest_id, consent_type, granted

### `data_access_requests` (KVKK / GDPR: Erişim ve Silme Talepleri)
- id (UUID, PK) [BaseModel]
- request_type (VARCHAR 20) — access | deletion | portability
- subject_id (UUID FK → guests.id) — talep eden misafir
- requested_at (TIMESTAMP)
- status (VARCHAR 15, default="pending") — pending / approved / completed / rejected / cancelled
- approved_by (UUID FK → users.id nullable, superadmin/manager)
- completed_at (TIMESTAMP nullable)
- delivery_method (VARCHAR 30) — email | secure_download | none
- notes (TEXT nullable)
- Index: subject_id, status, request_type

## 2. Endpoint'ler

### `POST /api/v1/security/key-cards`
- Auth: superadmin, manager, frontdesk
- Body: { card_holder_type, card_holder_id, valid_from_date, valid_to_date }
- card_number otomatik generate (random alphanumeric)
- check-in'de guest → valid_to_date = checkout_date otomatik
- 201 döner key_card (card_number masked UI'da)

### `PATCH /api/v1/security/key-cards/{id}/revoke`
- Auth: superadmin, manager, frontdesk
- Body: {}
- status=revoked, revoked_at=now
- check-out'ta otomatik call edilir
- 200 döner key_card

### `GET /api/v1/security/access-logs`
- Auth: superadmin, manager
- Query: ?user_id=&guest_id=&door_or_zone=&from_datetime=&to_datetime=&result=
- 200 döner { data: [{...card_number masked...}], meta: { total } }

### `GET /api/v1/security/door-locks`
- Auth: superadmin, manager, maintenance
- 200 döner { data: [{ id, location, lock_type, online_status, last_heartbeat }], meta: { online_count, offline_count } }

### `POST /api/v1/security/incidents`
- Auth: superadmin, manager
- Body: { incident_type, location, severity, description, reported_by }
- 201 döner incident (status=open)
- severity >= 3 (critical/high) ise manager WS bildirim

### `GET /api/v1/security/incidents`
- Auth: superadmin, manager
- Query: ?status=&severity=&from_date=&to_date=
- 200 döner { data: [{...}], meta: { by_type: {...}, by_severity: {...} } }

### `PATCH /api/v1/security/incidents/{id}/status`
- Auth: superadmin, manager
- Body: { status }
- Geçişler: open→investigating→resolved→closed; cancelled her yerden
- resolved'da resolved_at=now otomatik
- 200 döner incident

### `POST /api/v1/security/door-control`
- Auth: superadmin, manager, maintenance (mock IoT kilit)
- Body: { door_lock_id, command } — "unlock" | "lock" | "force_lock"
- IoT adapter call (mock-first): kilit durum değiştir
- online_status=offline ise 503 `LOCK_OFFLINE`
- başarı durumunda access_log entry yaz
- 200 döner { success: true, new_status }

### `POST /api/v1/kvkk/consents`
- Auth: guest (kendi kaydı), superadmin, manager
- Body: { guest_id, consent_type, purpose, granted }
- Yalnızca guest kendi ID'sine yazabilir; admin her guest'e
- 201 döner kvkk_consent

### `GET /api/v1/kvkk/consents`
- Auth: guest (kendi), superadmin, manager
- Query: ?guest_id=&consent_type=
- guest parametresiz ise kendi consents; admin filter ile
- 200 döner { data: [{...}], meta: {...} }

### `POST /api/v1/kvkk/data-access-requests`
- Auth: guest (talep etme), superadmin, manager (onaylama)
- Body: { request_type: "access" | "deletion" | "portability", subject_id?, delivery_method? }
- guest → kendi subject_id otomatik; admin → subject_id set
- 201 döner data_access_request (status=pending)
- Notification: superadmin/manager'a bildir (manuel inceleme gerekli)

### `GET /api/v1/kvkk/data-access-requests`
- Auth: guest (kendi pending), superadmin, manager
- 200 döner { data: [{...}], meta: {...} }

### `PATCH /api/v1/kvkk/data-access-requests/{id}/approve`
- Auth: superadmin, manager
- Body: { delivery_method }
- status=approved, approved_by=current_user
- request_type=deletion ise async job başlat (veri anonimleştirme)
- request_type=access ise guest veri dump hazırla → email / secure download
- 200 döner request

## 3. İş Mantığı

- **Check-in/Out kartı**: check-in'de key_card create (valid_to_date = checkout_date), check-out'ta revoke otomatik
- **Erişim log**: door_lock/access event → access_logs yazı; card_number/user_id mask (PII)
- **Kart geçerliliği**: valid_to_date < today ise result=expired, access denied
- **Şüpheli aktivite**: same door, 5+ consecutive failed attempts (result=denied) → incident create, manager WS bildir
- **KVKK Rızası**: konaklamadan before/during/after rıza toplama; purpose + consent_method kaydedilir
- **Silme Talebi (Deletion)**: request_type=deletion → status=approved sonrası:
  - guest ilişkili tüm PII alanlarını anonimleştir (name → "Guest-UUID", email → masked)
  - stays, reservations, folios, chat logs guest_id bağlı tuple'lar soft-delete
  - audit: deletion_audit_log entry (kim, ne zaman, talep_id)
- **Kilit Offline**: door_locks.online_status=offline ise control 503 veya force unlock imkan
- **Audit**: tüm işlem (card revoke, incident create, consent change) → audit_logs (TASK-001)

## 4. Dış Sistem Integrasyon (Mock-First)

### IoT Kilit Adapter
```
integrations/security/base.py: BaseLockAdapter (abstract)
  - unlock(lock_id) → async
  - lock(lock_id) → async
  - force_lock(lock_id) → async
integrations/security/generic_lock.py: GenericLockAdapter (mock-first)
```
- Test: mock adapter (in-memory state)

## 5. SecureAI Ajanı

### Model: `app/core/agents/secure_ai.py`
- Miras: BaseAgent
- agent_name: "secure_ai"
- model_provider: "deepseek" (fallback: "openai", "claude")

### `POST /api/v1/ai/secureai/anomaly-scan`
- Auth: superadmin, manager
- Body: { days_back: 7 }
- LLM prompt (PII masked): "Erişim log → anormal pattern: repeated denied, off-hours access, new locations"
- Mock: output: { anomalies: [{ log_id, anomaly_type: "repeated_denied" | "off_hours", risk_score: 0.8 }, ...] }
- LLM (gerçek): DeepSeek API (son N gün access_logs fetch → prompt)
- 200 döner { data: { anomalies: [...], risk_summary }, meta: {...} }

### `GET /api/v1/ai/secureai/incident-summary`
- Auth: superadmin, manager
- Query: ?from_date=&to_date=
- LLM prompt: "Incident özetleme + trend analizi; en yüksek risk areas"
- Mock: output: { summary: "3 unauthorized attempts, 1 door forced", high_risk_areas: ["Room 301", "Staff Area"], recommendation: "review access logs" }
- 200 döner { data: { summary, high_risk_areas, recommendation }, meta: {...} }

## 6. Testler (minimum 16)
- key_card create → valid_to_date, status=active
- check-in → key_card auto create
- check-out → key_card revoke otomatik
- access_log create → PII masked
- expired card → result=expired, access denied
- repeated failed attempts → incident create, manager WS bildir
- kvkk_consent create + revoke
- data-access-request pending → approve (request_type=access)
- deletion request → pending → approve → guest PII anonimize (audit trail)
- door-control unlock/lock → IoT adapter mock
- door-control offline lock → 503
- incident create → severity=critical ise manager bildir
- secureai anomaly-scan mock/LLM happy path
- secureai incident-summary mock/LLM happy path
- RBAC: guest kendi consent/request yazabilir ✓, başka guest 403; token'sız 401
- deletion audit trail: tüm silinen PII user_id + timestamp kaydedilir

## 7. Teslim dosyaları
```
### FILE: backend/app/models/security.py
### FILE: backend/app/routers/security.py
### FILE: backend/app/core/agents/secure_ai.py
### FILE: backend/app/services/security_service.py
### FILE: backend/integrations/security/base.py
### FILE: backend/integrations/security/generic_lock.py
### FILE: backend/tests/test_modules/test_security.py
### FILE: backend/migrations/versions/005_add_security_tables.py
```

## 8. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- KVKK silme talebi end-to-end test edilmiş: request → approval → PII anonimize → audit log
- Key card lifecycle (check-in create → check-out revoke) otomasyonu test edilmiş
- SecureAI ajanı BaseAgent'ı miras alır, registry'ye kaydolı, mock modu test için
- IoT kilit adapter mock-first, interface test edilmiş
- OpenAPI Türkçe; error kodları `LOCK_OFFLINE`, KVKK-spesifik
- PII masking: access_logs, key_cards UI'da card_number gösterilmiyor (masked "****1234")
