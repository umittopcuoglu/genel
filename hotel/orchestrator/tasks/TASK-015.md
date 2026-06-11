---
id: TASK-015
modül: 6 (Maintenance & Technical Services)
kapsam: iş emri yönetimi + varlık envanteri + önleyici bakım + bakım geçmişi + TechCare AI
durum: kuyrukta (TASK-005, TASK-007 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-002 (rooms, room_types), TASK-005 (housekeeping), TASK-007 (BaseAgent, registry, PII mask)
---

# TASK-015 — Modül 6: Bakım & Teknik Servis + TechCare AI

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §6. TechCare AI tahminleri — bu görevde sadece çekirdek akış.

## 1. Veri Modeli

### `work_orders`
- id (UUID, PK) [BaseModel]
- room_id (UUID FK → rooms.id nullable, null=ortak alan)
- location_description (VARCHAR 100) — "Room 301" | "Front Lobby" | "Kitchen"
- category (VARCHAR 30) — plumbing / electrical / hvac / appliance / structural / other
- description (TEXT) — arıza açıklaması
- assigned_to (UUID FK → users.id, maintenance rolü, nullable)
- priority (INT, default=3) — 1 acil (guest impact) … 5 düşük (cosmetic)
- status (VARCHAR 15, default="open") — open / assigned / in_progress / resolved / closed
- sla_minutes (INT nullable) — tahmini süre
- started_at, resolved_at, closed_at (TIMESTAMP nullable)
- parts_used (JSON array) — [{ name, cost }]
- labor_hours (DECIMAL 5,2 nullable)
- notes (TEXT nullable)
- Index: room_id, status, assigned_to, priority

### `assets`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100) — "AC Unit Room 301", "Dishwasher Kitchen"
- category (VARCHAR 30) — hvac / plumbing / appliance / structural
- room_id (UUID FK → rooms.id nullable, asset konumu)
- location_description (VARCHAR 100)
- purchase_date (DATE nullable)
- warranty_end_date (DATE nullable)
- last_maintenance_date (DATE nullable)
- next_maintenance_due (DATE nullable)
- status (VARCHAR 15, default="active") — active / inactive / decommissioned
- notes (TEXT nullable)
- Index: category, room_id, status

### `preventive_maintenance`
- id (UUID, PK) [BaseModel]
- asset_id (UUID FK → assets.id)
- task_description (VARCHAR 200)
- frequency_days (INT) — 30, 90, 180, 365
- last_completed_date (DATE nullable)
- next_due_date (DATE) — auto-set on creation
- assigned_to (UUID FK → users.id nullable, maintenance)
- status (VARCHAR 15, default="pending") — pending / completed / overdue / skipped
- Index: asset_id, next_due_date, status

### `maintenance_logs`
- id (UUID, PK) [BaseModel]
- work_order_id (UUID FK → work_orders.id)
- performed_by (UUID FK → users.id, maintenance)
- action_taken (TEXT)
- parts_replaced (VARCHAR 200 nullable)
- duration_minutes (INT)
- notes (TEXT nullable)
- Index: work_order_id, performed_by

## 2. Endpoint'ler

### `POST /api/v1/maintenance/work-orders`
- Auth: superadmin, manager, maintenance, housekeeping (talep aç), frontdesk
- Body: { room_id?, location_description, category, description, priority?, assigned_to? }
- 201 döner work_order (status=open)
- room_id varsa ve assigned_to boş ise housekeeping bilgilendirilir (WS)

### `GET /api/v1/maintenance/work-orders`
- Auth: superadmin, manager, maintenance
- Query: ?status=&priority=&room_id=&assigned_to=&from_date=&to_date=
- 200 döner { data: [{...}], meta: { total, by_status: {...} } }

### `GET /api/v1/maintenance/work-orders/{id}`
- Auth: superadmin, manager, maintenance
- 200 döner { id, description, status, logs: [{...}], sla_minutes, priority, ... }

### `PATCH /api/v1/maintenance/work-orders/{id}/assign`
- Auth: superadmin, manager
- Body: { assigned_to }
- status geçişi: open→assigned
- assigned_to'ya bildirim gönderilir

### `PATCH /api/v1/maintenance/work-orders/{id}/status`
- Auth: superadmin, manager, maintenance
- Body: { status }
- Geçişler: open→assigned→in_progress→resolved→closed; atlama/geri 422
- in_progress'te started_at otomatik, resolved'da resolved_at otomatik, closed'da closed_at otomatik
- resolved'dan önce maintenance_log entry yazılmalı

### `POST /api/v1/maintenance/work-orders/{id}/log`
- Auth: superadmin, manager, maintenance
- Body: { action_taken, parts_replaced?, duration_minutes, notes? }
- maintenance_log yazılır; work_order.parts_used updatede

### `PATCH /api/v1/maintenance/work-orders/{id}/room-status`
- Auth: superadmin, manager, maintenance
- Body: { room_status } — "OOO" (out of order) | "clean"
- room.status güncelleme; OOO'ya set edilince housekeeping bilgisi (TASK-005 inspection gerekli)

### `GET /api/v1/maintenance/assets`
- Auth: superadmin, manager, maintenance
- Query: ?category=&room_id=&status=
- 200 döner { data: [{...}], meta: {...} }

### `POST /api/v1/maintenance/assets`
- Auth: superadmin, manager, maintenance
- Body: { name, category, room_id?, location_description, purchase_date, warranty_end_date, notes? }
- 201 döner asset

### `GET /api/v1/maintenance/preventive-maintenance`
- Auth: superadmin, manager, maintenance
- Query: ?status=pending&overdue=true
- 200 döner { data: [{...}], meta: { overdue_count, pending_count } }

### `POST /api/v1/maintenance/preventive-maintenance/auto-generate`
- Auth: superadmin, manager
- Body: { as_of_date } — "2026-06-11"
- next_due_date <= as_of_date olan tüm preventive_maintenance satırları fetch; status=pending olanlar listele
- Taşıdığı asset'in last_maintenance_date + frequency_days < today ise overdue mark
- 200 döner { data: { pending: N, overdue: M }, meta: {...} }

### `PATCH /api/v1/maintenance/preventive-maintenance/{id}/complete`
- Auth: superadmin, manager, maintenance
- Body: { completed_date? } — default=today
- status=completed, last_completed_date=completed_date, next_due_date=completed_date + frequency_days
- work_order otomatik create (category=preventive, opsiyonel log)

## 3. İş Mantığı

- **İş emri oluştur**: open → (opsiyonel) OOO oda işaretleme → assigned (maintenance'ye) → in_progress → log entries → resolved (parts_used, labor_hours) → closed
- **SLA süresi**: category bazlı default (electrical=30min, plumbing=60min, hvac=120min); assigned'da start saati kaydedilir
- **Oda durumu**: OOO set edilince housekeeping "inspection" görev auto-create (TASK-005); clean'e dön → inspection complete gerekir
- **Varlık envanteri**: purchase_date varsa warranty otomatik hesap; last_maintenance_date + frequency güncelle
- **Önleyici bakım**: next_due_date <= today ise overdue; auto-generate çağrısında sorgular, completetion'da schedule reset
- **Tekrarlayan arızalar**: same asset, category aynı, son 30 gün içinde 3+ WO → TechCare risk flag

## 4. TechCare AI Ajanı

### Model: `app/core/agents/techcare_ai.py`
- Miras: BaseAgent
- agent_name: "techcare_ai"
- model_provider: "deepseek" (fallback: "openai", "claude")

### `POST /api/v1/ai/techcare/triage`
- Auth: superadmin, manager, maintenance, housekeeping
- Body: { description, location? }
- LLM prompt (PII masked): "Arıza açıklaması → kategori + öncelik tahmini + SLA süresi"
- Mock: description="Odada AC soğutmuyor" → output: { category: "hvac", priority: 1, sla_minutes: 60, rationale: "Guest comfort impact" }
- LLM (gerçek): DeepSeek API
- 200 döner { data: { suggested_category, priority, sla_minutes, confidence, rationale }, meta: {...} }

### `GET /api/v1/ai/techcare/predict`
- Auth: superadmin, manager, maintenance
- Query: ?asset_id=UUID
- LLM prompt: "Varlık geçmişi (log ve maintenance) → arıza riski + tahmini yaşam süresi"
- Mock: output: { failure_risk: 0.72, predicted_lifespan_months: 18, recommended_action: "schedule replacement" }
- 200 döner { data: { failure_risk, predicted_lifespan_months, recommendation }, meta: {...} }

## 5. Testler (minimum 16)
- WO create → status=open
- WO assign → assigned, maintenance WS bildirim
- WO status chain: open→assigned→in_progress→resolved→closed (valid), invalid transition 422
- WO log → parts_used update
- room OOO → housekeeping inspection görev (TASK-005 entegrasyonu)
- asset CRUD
- preventive-maintenance create + auto-generate
- PM complete → next_due_date reset
- techcare triage mock/LLM happy path
- techcare predict mock/LLM happy path
- RBAC: housekeeping WO create ✓, asset create 403
- SLA süresi category'ye göre
- tekrarlayan arıza flag (3+ aynı asset, 30 gün)
- techcare LLM error handling

## 6. Teslim dosyaları
```
### FILE: backend/app/models/maintenance.py
### FILE: backend/app/routers/maintenance.py
### FILE: backend/app/core/agents/techcare_ai.py
### FILE: backend/app/services/maintenance_service.py
### FILE: backend/tests/test_modules/test_maintenance.py
### FILE: backend/migrations/versions/005_add_maintenance_tables.py
```

## 7. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- WO durum makinesi eksiksiz test edilmiş; invalid transition 422
- TechCare ajanı BaseAgent'ı miras alır, registry'ye kaydolı, mock modu test için
- Housekeeping entegrasyonu (OOO → inspection) TASK-005 ile koordine
- OpenAPI Türkçe; error kodları `INVALID_TRANSITION`
