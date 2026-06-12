---
id: TASK-023
modül: Faz 4 - Multi-Property Management
kapsam: zincir oteller + merkezi muhasebe + oto-transfer + konsoldiye rapor
durum: kuyrukta (Faz 3 tamamlanınca)
tur: —
bağımlılık: TASK-001 (users + RBAC), TASK-004 (folio + payment), TASK-009 (dashboard)
---

# TASK-023 — Faz 4: Çok-Mülk Yönetimi — Otel Zinciri Konsolidasyonu

> Sahibi her otel için ayrı ortam/database'i yönetemesin. Merkezi "konsol" → tüm mülkler için KPI + finansal kontrol + personel yönetimi.

## 1. Veri Modeli

### `properties` (otel/mülk tanımı)
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100) — "Ankara Otel", "İzmir Resort"
- code (VARCHAR 10, unique) — AN01, IZ01
- chain_id (UUID FK → chains.id)
- address, city, country (VARCHAR 255, 100, 50)
- phone, email (VARCHAR 20, 100)
- stars (INT, default=4) — 3/4/5 yıldız
- rooms_count (INT)
- manager_user_id (UUID FK → users.id, mülk müdürü)
- currency (VARCHAR 3, default="TRY")
- timezone (VARCHAR 30, default="Europe/Istanbul")
- database_url (VARCHAR 255 encrypted nullable) — Mülk-specific DB (multi-tenant DB ya da shared)
- api_key (VARCHAR 100, unique, encrypted) — Mülk → Merkez API iletişim
- status (VARCHAR 15, default="active") — active / inactive / archived
- created_at (auto)
- Index: chain_id, status, code

### `chains` (otel zinciri sahipleri)
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100) — "Touresco Hotels Group"
- owner_user_id (UUID FK → users.id)
- owner_email (VARCHAR 100)
- billing_email (VARCHAR 100)
- max_properties (INT, default=10) — lisans limiti
- subscription_plan (VARCHAR 30, default="enterprise") — startup / growth / enterprise
- annual_cost (DECIMAL 12,2)
- billing_start_date (DATE)
- billing_next_date (DATE)
- status (VARCHAR 15, default="active") — active / suspended / cancelled
- Index: owner_user_id, status

### `property_sync_logs`
- id (UUID, PK) [BaseModel]
- property_id (UUID FK → properties.id)
- sync_type (VARCHAR 30) — reservation / folio / payment / occupancy
- sync_direction (VARCHAR 10) — pull / push / bidirectional
- records_synced (INT, default=0)
- status (VARCHAR 15, default="pending") — pending / success / partial / failed
- error_details (VARCHAR 500 nullable)
- started_at, completed_at (DATETIME)
- Index: property_id, status, created_at

### `consolidated_reports` (merkezi rapor önbelleği)
- id (UUID, PK) [BaseModel]
- chain_id (UUID FK → chains.id)
- report_type (VARCHAR 30) — kpi_summary / financial / occupancy / revenue
- report_date (DATE) — rapor hangi tarih için
- data (JSON) — {property_kpis: {...}, consolidated_numbers: {...}}
- generated_at (DATETIME)
- generated_by (UUID FK → users.id)
- status (VARCHAR 15, default="ready") — pending / ready / error
- Index: chain_id, report_type, report_date

### `property_users` (her mülkün kullanıcıları)
- id (UUID, PK) [BaseModel]
- property_id (UUID FK → properties.id)
- user_id (UUID FK → users.id)
- role_at_property (VARCHAR 30) — manager / frontdesk / housekeeping / accounting / superadmin
- access_level (VARCHAR 15, default="full") — full / read_only / department
- start_date (DATE)
- end_date (DATE nullable)
- status (VARCHAR 15, default="active") — active / inactive
- Index: property_id, user_id, status

## 2. Endpoint'ler (Merkezi Konsol — /api/v1/console/)

### `POST /api/v1/console/chains`
- Auth: superadmin (sistem)
- Body: { name, owner_user_id, subscription_plan, max_properties }
- 201 döner zincir kaydı + default API key

### `GET /api/v1/console/chains/{chain_id}/dashboard`
- Auth: chain owner, superadmin
- 200 döner { kpi_summary: {total_occupancy, total_revenue, total_guests}, properties: [{name, occupancy, revenue, adr}], alerts: [] }
- Cache: 1 saat (consolidated_reports)

### `POST /api/v1/console/properties`
- Auth: chain owner, superadmin
- Body: { name, code, chain_id, address, manager_user_id, rooms_count, database_url?, currency?, timezone? }
- 201 döner mülk kaydı + API key (property-to-central auth)

### `PATCH /api/v1/console/properties/{property_id}/sync`
- Auth: superadmin, chain owner
- Body: { sync_type: "reservation", direction: "pull" / "push" / "bidirectional", filters?: {start_date, end_date} }
- İşlem: Property API'sini çağır (API key'le auth) → verilen gün range'ini pull/push → property_sync_logs kaydı
- 202 döner { job_id, status: "pending" }

### `GET /api/v1/console/properties/{property_id}/sync-status`
- Auth: chain owner, superadmin
- 200 döner { last_sync_at, sync_count, last_error?, next_scheduled_sync }

### `GET /api/v1/console/chains/{chain_id}/financial-report`
- Auth: chain owner, superadmin, accounting
- Query: ?from_date=2026-06-01&to_date=2026-06-30
- 200 döner consolidated report (consolidated_reports cache'den)
  - { total_revenue, total_folio_balance, total_payments, property_breakdown: [{name, revenue, balance}], commission_calculations: [] }

### `GET /api/v1/console/chains/{chain_id}/occupancy-trend`
- Auth: chain owner, superadmin
- Query: ?days=30
- 200 döner { trend: [{date, occupancy_pct, avg_adr, revenue}], chain_avg: 65.5, best_performer: "AN01", worst: "IZ01" }

### `POST /api/v1/console/properties/{property_id}/transfer-folio`
- Auth: superadmin, accounting
- Body: { folio_ids: [...], transfer_to_property_id, reason: "konsolidasyon" }
- İşlem: master folio → transferred_from_property kayıt (audit)
- 200 döner { transferred_count, batch_id }

### `GET /api/v1/console/property-users/{property_id}`
- Auth: chain owner, manager, superadmin
- 200 döner { users: [{user_id, email, role_at_property, access_level, status}] }

### `POST /api/v1/console/property-users`
- Auth: manager (property), chain owner, superadmin
- Body: { property_id, user_id, role_at_property, access_level }
- 201 döner property_users kaydı + grant (user mülke erişim)

## 3. İş Mantığı

1. **Zincir kurma:**
   - Owner user (superadmin level) zincir oluşturur
   - API key auto-generate (64-char random, encrypted storage)
   - Subscription plan ↔ max_properties limiti (startup=3, growth=10, enterprise=unlimited)

2. **Mülk ekleme:**
   - Chain owner mülk kaydını oluşturur
   - database_url nullable: shared DB (tenant_id) ya da ayrı DB URI
   - Shared DB senaryosu: tüm tablolara `property_id` FK + global index

3. **Senkronizasyon:**
   - Her mülk kendi API'ye sahip: `https://{property}.hotelops.local/api/v1/`
   - Central → Property: API key + property_id ile POST /api/v1/internal/sync
   - Property → Central: (ileride webhook; şimdilik pull-only)
   - property_sync_logs durum makinesi: pending → (processing) → success / partial / failed

4. **Konsolidasyonlu raporlar:**
   - Scheduled job (nightly 2AM UTC): tüm mülklerin KPI'sını pull → consolidated_reports kaydı
   - Cache: 1 saat (dashboard'da tazelik)
   - KPI: occupancy, ADR, RevPAR, total_revenue, folio_balance, payment_method breakdown

5. **Finansal otomatik transfer:**
   - Mülk düzeyinde: master group folio (grup = konsol ana hesap)
   - Monthly settlement: her mülkün net revenue → master folio'ya transfer (reason="monthly_settlement_CHAİN_ID")
   - Commission otomatik hesapla: (mülk revenue × chain commission rate)

6. **Personel yönetimi:**
   - Central user = tüm mülklere erişim (superadmin)
   - Property user = tek mülke + role (property_users mapping)
   - Access token'da property_id inject et (JWT claim)

7. **Multi-tenant isolation:**
   - Shared DB: tüm sorguya `where property_id = <current>` filter ekle
   - Ayrı DB: connection pool'ı dinamik seç (property.database_url)
   - Test: fake properties (property_id=123, 456...) mock data ile

## 4. Minimum Test Sayısı

- [ ] 5 unit test (`test_multi_property.py`):
  - Chain creation + subscription limit check
  - Property add (max_properties control)
  - API key generation + rotation
  - Sync log state machine
  - Commission calculation

- [ ] 4 integration test (`test_chain_sync_e2e.py`):
  - Pull reservations from 2 properties → consolidate
  - Pull folios + aggregate revenue
  - Transfer folio cross-property (audit)
  - Permission check (property_users isolation)

- [ ] 2 performance test:
  - 10 property sync parallel, 1000 rez each, < 30s total
  - Dashboard KPI calculation (all properties) < 5s

## 5. Acceptance Criteria

- [ ] Chain + property CRUD endpoints
- [ ] Property API key generation + rotation
- [ ] Sync job (pull reservation/folio/payment) with status tracking
- [ ] Consolidated reporting (KPI + financial) dengan caching
- [ ] Cross-property folio transfer dengan audit trail
- [ ] Permission isolation (property_users per property)
- [ ] Subscription plan ↔ max_properties limiti
- [ ] Tüm endpoint'ler RBAC + hata zarfı
- [ ] Multi-tenant test (fake properties isolation)
- [ ] OpenAPI Türkçe
- [ ] pytest backend/tests yeşil

---

## 6. Teslim Dosyaları

### FILE: hotel/backend/app/models/chain.py
```python
# Chain + property + sync models
```

### FILE: hotel/backend/app/routers/console.py
```python
# Console API endpoints (chain dashboard + sync + reporting)
```

### FILE: hotel/backend/app/services/chain_service.py
```python
# Chain + property logic + sync orchestration
```

### FILE: hotel/backend/app/services/consolidation_service.py
```python
# Report generation + KPI aggregation
```

### FILE: hotel/backend/integrations/chain/property_connector.py
```python
# Property → Central API client
```

### FILE: hotel/backend/migrations/versions/0NN_add_multi_property.py
```python
# Migration: chains, properties, property_sync_logs, consolidated_reports, property_users
```

### FILE: hotel/backend/tests/test_modules/test_multi_property.py
```python
# Unit + integration + performance tests
```
