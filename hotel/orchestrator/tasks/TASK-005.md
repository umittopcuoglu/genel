---
id: TASK-005
modül: 5 (Housekeeping)
kapsam: görev panosu + temizlik görevleri + kayıp eşya + minibar post
durum: kuyrukta (TASK-004 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-002 (rooms, stays), TASK-004 (folio post — minibar)
---

# TASK-005 — Modül 5: Housekeeping

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §5. CleanOps AI tahminleri ve mobil WebSocket Faz 2 — bu görevde sadece çekirdek akış.

## 1. Veri Modeli

### `housekeeping_tasks`
- id (UUID, PK) [BaseModel]
- room_id (FK → rooms.id)
- assigned_to (UUID FK → users.id, nullable)
- type (VARCHAR 15) — checkout / stayover / inspection / deep
- status (VARCHAR 15, default="pending") — pending / in_progress / done / verified
- priority (INT, default=3) — 1 acil … 5 düşük
- started_at, completed_at (TIMESTAMP nullable)
- notes (TEXT nullable)
- Index: room_id, assigned_to, status

### `lost_found`
- id (UUID, PK) [BaseModel]
- room_id (FK → rooms.id)
- found_by (UUID FK → users.id)
- item_description (TEXT)
- status (VARCHAR 15, default="stored") — stored / returned / disposed
- returned_to (VARCHAR 100 nullable), returned_at (TIMESTAMP nullable)
- Index: room_id, status

### `minibar_items`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100), price (DECIMAL 10,2), tax_rate (DECIMAL 5,2, default=18)

## 2. Endpoint'ler

### `GET /api/v1/housekeeping/board`
- Auth: superadmin, manager, housekeeping, frontdesk
- Dönen: oda durum panosu — { data: [ { room_no, floor, status, active_task: {...}|null, current_guest: bool } ], meta: { counts: {clean, dirty, inspected, out_of_order} } }

### `POST /api/v1/housekeeping/tasks`
- Auth: superadmin, manager, housekeeping
- Body: { room_id, type, assigned_to?, priority?, notes? }
- Aynı odada açık (pending/in_progress) aynı tip görev varsa 409 `TASK_EXISTS`

### `PATCH /api/v1/housekeeping/tasks/{id}/status`
- Auth: superadmin, manager, housekeeping
- Body: { status }
- Geçiş kuralları: pending→in_progress→done→verified; atlama/geri gitme 422 `INVALID_TRANSITION`
- in_progress'e geçişte started_at, done'da completed_at otomatik
- done olduğunda room.status → clean; verified'da → inspected

### `POST /api/v1/housekeeping/auto-generate`
- Auth: superadmin, manager
- Body: { date }
- O gün checkout olan odalara "checkout", in-house odalara "stayover" görevi üretir (dupe atlanır)
- 200: { data: { created: N, skipped: M }, meta: {} }

### `POST /api/v1/lost-found` + `PATCH /api/v1/lost-found/{id}/return`
- Auth: superadmin, manager, housekeeping, frontdesk
- return: { returned_to } → status=returned, returned_at otomatik

### `POST /api/v1/minibar/post`
- Auth: superadmin, manager, housekeeping, frontdesk
- Body: { room_id, items: [ {minibar_item_id, qty} ] }
- Odadaki aktif konaklamanın folio'suna type=fnb satırları post eder
- Aktif konaklama yoksa 409 `NO_ACTIVE_STAY`

## 3. Testler (minimum 14)
- board doğru sayımlar
- task create happy / dupe 409
- status geçişleri happy zinciri + geçersiz geçiş 422
- done → room clean, verified → inspected doğrulaması
- auto-generate: checkout+stayover üretimi, dupe skip
- lost-found create + return akışı
- minibar post → folio_items yazıldı, tutar doğru
- minibar aktif konaklama yok 409
- RBAC: fb rolü task oluşturamaz 403; token'sız 401

## 4. Teslim dosyaları
```
### FILE: backend/app/models/housekeeping.py
### FILE: backend/app/routers/housekeeping.py
### FILE: backend/app/routers/lost_found.py
### FILE: backend/app/routers/minibar.py
### FILE: backend/tests/test_modules/test_housekeeping.py
### FILE: backend/migrations/versions/005_add_housekeeping_tables.py
```

## 5. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- Durum makinesi geçiş kuralları eksiksiz test edilmiş
- OpenAPI Türkçe
