---
id: TASK-019
modül: GDS Entegrasyonu (Dağıtım Sistemi)
kapsam: GDS bağlantısı yönetimi + ARI (Availability/Rate/Inventory) push + Rez pull/webhook + GDS sync
durum: kuyrukta (TASK-003, TASK-008 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-003 (rooms, room_types, availability, reservations), TASK-008 (channel manager adapter deseni)
---

# TASK-019 — GDS Entegrasyonu (Amadeus / Sabre / Travelport)

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md — GDS adapter, TASK-008 Channel Manager adapter deseni tekrar kullanılır.

## 1. Veri Modeli

### `gds_connections`
- id (UUID, PK) [BaseModel]
- provider_name (VARCHAR 50) — "amadeus" | "sabre" | "travelport" | "other"
- api_key (VARCHAR 200, encrypted)
- api_secret (VARCHAR 200, encrypted)
- gds_property_id (VARCHAR 100) — GDS tarafındaki otel tanımlayıcısı
- status (VARCHAR 15, default="active") — active / inactive / error / test
- last_sync_datetime (TIMESTAMP nullable)
- last_error_message (TEXT nullable)
- sync_frequency_hours (INT, default=6) — ne sıklıkla sync edilecek
- notes (TEXT nullable)
- Index: provider_name, status

### `gds_mappings`
- id (UUID, PK) [BaseModel]
- gds_connection_id (UUID FK → gds_connections.id)
- room_type_id (UUID FK → room_types.id)
- gds_room_code (VARCHAR 50) — GDS tarafındaki oda tipi kodu
- gds_rate_code (VARCHAR 50) — GDS tarafındaki fiyat kodu (sezonalite, channel-specific)
- mapping_status (VARCHAR 15, default="active") — active / inactive
- notes (TEXT nullable)
- Index: gds_connection_id, room_type_id

### `gds_sync_logs`
- id (UUID, PK) [BaseModel]
- gds_connection_id (UUID FK → gds_connections.id)
- sync_type (VARCHAR 20) — ari_push | rez_pull | webhook_received
- sync_datetime (TIMESTAMP)
- status (VARCHAR 15) — success | partial | failed
- record_count (INT) — kaç rez / ARI item işlendi
- error_message (TEXT nullable)
- details (JSON nullable)
- Index: gds_connection_id, sync_type, sync_datetime

## 2. Endpoint'ler

### `POST /api/v1/gds/connections`
- Auth: superadmin, manager
- Body: { provider_name, api_key, api_secret, gds_property_id, sync_frequency_hours?, notes? }
- api_key, api_secret encrypted → .env credential validation (mock-first, test'te hardcoded)
- 201 döner gds_connection (status=test, ilk sync trigger opsiyonel)

### `GET /api/v1/gds/connections`
- Auth: superadmin, manager
- 200 döner { data: [{...api_key masked...}], meta: {...} }

### `PATCH /api/v1/gds/connections/{id}/status`
- Auth: superadmin, manager
- Body: { status }
- test → active geçişinde ilk sync trigger
- 200 döner gds_connection

### `POST /api/v1/gds/mappings`
- Auth: superadmin, manager
- Body: { gds_connection_id, room_type_id, gds_room_code, gds_rate_code }
- 201 döner gds_mapping

### `GET /api/v1/gds/mappings`
- Auth: superadmin, manager
- Query: ?gds_connection_id=&room_type_id=
- 200 döner { data: [{...}], meta: {...} }

### `POST /api/v1/gds/sync-ari`
- Auth: superadmin, manager
- Body: { gds_connection_id }
- Trigger: TASK-003 availability + TASK-004 rates → GDS push
- ARI (Availability/Rate/Inventory):
  - room_type per → gds_mappings.gds_room_code
  - qty_available → today + 365 days
  - rate → room_type.daily_rates (channel + date) of GDS mapped rates
- Adapter (TASK-008 pattern): integrations/gds/{provider}.py activate
- gds_sync_logs entry: sync_type="ari_push", record_count = room_types pushed, status
- 200 döner { data: { pushed: N, errors: M }, meta: {...} }

### `POST /api/v1/gds/webhook`
- Auth: GDS (webhook signature doğrulama)
- Body: { event, data: {...} } — event="reservation_created" | "reservation_cancelled" | ...
- Signature doğrula: gds_connections'ten api_secret
- Adapter activate (provider_name'e göre)
- Rez data normalize → local reservation create/update/cancel (source=gds, gds_connection_id kaydedilir)
- Overbooking kontrolü: TASK-008 ile aynı (qty_available kontrolü)
- gds_sync_logs: sync_type="webhook_received"
- 200 döner { success: true }

### `GET /api/v1/gds/sync-logs`
- Auth: superadmin, manager
- Query: ?gds_connection_id=&sync_type=&from_datetime=&to_datetime=&status=
- 200 döner { data: [{...}], meta: { success_count, failure_count } }

### `POST /api/v1/gds/pull-reservations`
- Auth: superadmin, manager
- Body: { gds_connection_id, from_date, to_date }
- Adapter: rez pull request (tarih aralığı)
- Rez data normalize → local insert/update (source=gds)
- gds_sync_logs: sync_type="rez_pull"
- 200 döner { data: { imported: N, updated: M, skipped: K }, meta: {...} }

## 3. İş Mantığı

- **ARI Push**: Trigger manual (`/sync-ari`) veya scheduled (sync_frequency_hours); availability → GDS rate inventory; channel-specific rates push
- **Rez Pull**: Trigger manual veya scheduled; GDS'den rez data fetch → local DB normalize (source=gds, overbooking check)
- **Webhook**: GDS'den incoming rez event → signature verify → normalize → local create/update/cancel
- **Overbooking**: GDS rez pull/webhook'ta qty_available check (TASK-008 pattern); insufficient ise overbooking flag veya deny (policy per provider)
- **Mapping**: room_type + rate code → GDS code; sezonalite + channel-specific (TASK-008 rate_code variation)
- **Sync log**: Her push/pull/webhook'ta record; error tracking + manual retry imkan
- **Encryption**: api_key, api_secret .env-backed; production'da encrypted column (test'te plain)

## 4. Dış Sistem Integrasyon (Mock-First)

### Adapter Deseni (TASK-008'den inherit)
```
integrations/gds/base.py: BaseGDSAdapter (abstract)
  - push_ari(availability, rates) → async
  - pull_reservations(from_date, to_date) → async
  - verify_webhook_signature(data, signature) → bool
  
integrations/gds/amadeus.py: AmadeusAdapter (mock-first)
integrations/gds/sabre.py: SabreAdapter (mock-first)
integrations/gds/travelport.py: TravelportAdapter (mock-first)
```
- Mock mod: in-memory queue, hardcoded response
- Test: mock adapter; gerçek anahtar .env-backed (test .env.test'te dummy key)
- Error handling: API timeout → status="partial", error_message logged

## 5. Testler (minimum 12)
- gds_connection create + status test → active
- gds_mapping create
- sync-ari push → gds_sync_logs success
- rez-pull webhook → normalize → local reservation create
- webhook signature validation success / failure
- overbooking: pull/webhook'ta qty_available < requested → flag | deny
- sync-ari scheduled trigger (job-like behavior; mock clock)
- API timeout → partial status, error_message
- gds_sync_logs query by status/type
- adapter mock mode: in-memory queue
- RBAC: manager GDS connection manage ✓, frontdesk read-only ✓
- rate mapping: channel + date sezonalite multi-variant

## 6. Teslim dosyaları
```
### FILE: backend/app/models/gds.py
### FILE: backend/app/routers/gds.py
### FILE: backend/app/services/gds_service.py
### FILE: backend/integrations/gds/base.py
### FILE: backend/integrations/gds/amadeus.py
### FILE: backend/integrations/gds/sabre.py
### FILE: backend/integrations/gds/travelport.py
### FILE: backend/tests/test_modules/test_gds.py
### FILE: backend/migrations/versions/005_add_gds_tables.py
```

## 7. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- ARI push + Rez pull/webhook end-to-end test edilmiş
- Overbooking entegrasyonu (TASK-008 pattern) test edilmiş
- Adapter mock-first; production key → .env
- Signature doğrulama test edilmiş
- OpenAPI Türkçe; error kodları `OVERBOOKING`, `INVALID_SIGNATURE`, adapter-spesifik hatalar
