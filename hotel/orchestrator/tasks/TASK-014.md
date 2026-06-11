---
id: TASK-014
modül: 3 (Groups & Events / MICE)
kapsam: grup yönetimi + etkinlik + salon müsaitliği + rooming list import + grup folio + EventIQ AI
durum: kuyrukta (TASK-004, TASK-007 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-003 (rooms, room_types, availability), TASK-004 (folio post), TASK-007 (BaseAgent, registry, PII mask)
---

# TASK-014 — Modül 3: Groups & Events (MICE) + EventIQ AI

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §3. EventIQ AI tahminleri — bu görevde sadece çekirdek akış.

## 1. Veri Modeli

### `groups`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100)
- agency_id (UUID FK → users.id nullable, acenta temsilcisi)
- contract_number (VARCHAR 50 unique nullable)
- status (VARCHAR 15, default="inquiry") — inquiry / confirmed / cancelled / completed
- block_start_date, block_end_date (DATE)
- pax_count (INT) — beklenen misafir sayısı
- group_folio_id (UUID FK → folios.id, master account)
- discount_rate (DECIMAL 5,2, default=0) — grup indirim oranı (0-100)
- notes (TEXT nullable)
- Index: status, block_start_date, agency_id

### `room_blocks`
- id (UUID, PK) [BaseModel]
- group_id (UUID FK → groups.id)
- room_type_id (UUID FK → room_types.id)
- qty_required (INT) — talep edilen oda sayısı
- qty_confirmed (INT, default=0) — onaylanan oda sayısı
- pickup_date, release_date (DATE) — envanterden çekme/serbest bırakma tarihleri
- status (VARCHAR 15, default="pending") — pending / confirmed / released / cancelled
- Index: group_id, status

### `events`
- id (UUID, PK) [BaseModel]
- group_id (UUID FK → groups.id)
- title (VARCHAR 100)
- event_type (VARCHAR 30) — conference / meeting / wedding / gala / other
- venue_id (UUID FK → venues.id nullable, salon/mekan)
- capacity_required (INT)
- setup_type (VARCHAR 30) — classroom / theater / banquet / boardroom / cocktail
- start_datetime, end_datetime (TIMESTAMP)
- catering_required (BOOLEAN, default=false)
- notes (TEXT nullable)
- Index: group_id, venue_id

### `event_resources`
- id (UUID, PK) [BaseModel]
- event_id (UUID FK → events.id)
- resource_type (VARCHAR 30) — equipment / catering / staff
- description (VARCHAR 200)
- qty_required (INT)
- unit_cost (DECIMAL 10,2)
- status (VARCHAR 15, default="requested") — requested / confirmed / completed / cancelled
- Index: event_id

### `group_rooming_list`
- id (UUID, PK) [BaseModel]
- group_id (UUID FK → groups.id)
- guest_name (VARCHAR 100)
- guest_email (VARCHAR 100 nullable)
- guest_phone (VARCHAR 20 nullable)
- room_type_requested (VARCHAR 30)
- checkin_date, checkout_date (DATE)
- reservation_id (UUID FK → reservations.id nullable, otomatik rez bağlanır)
- status (VARCHAR 15, default="pending") — pending / matched / checked_in / checked_out
- Index: group_id, reservation_id

### `venues`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100)
- capacity_min, capacity_max (INT)
- setup_types (JSON array VARCHAR 30) — ["classroom", "theater", ...]
- status (VARCHAR 15, default="active") — active / inactive
- Index: status

## 2. Endpoint'ler

### `POST /api/v1/groups`
- Auth: superadmin, manager, frontdesk
- Body: { name, agency_id?, contract_number?, block_start_date, block_end_date, pax_count, discount_rate?, notes? }
- 201 döner grup kaydı (group_folio otomatik oluşturulur: master account)

### `GET /api/v1/groups/{id}`
- Auth: superadmin, manager, frontdesk
- 200 döner { id, name, status, room_blocks: [{...}], events: [{...}], rooming_list_count, ... }

### `PATCH /api/v1/groups/{id}/status`
- Auth: superadmin, manager
- Body: { status }
- Geçişler: inquiry→confirmed→completed; cancelled her yerden
- confirmed'e geçişte room_blocks' qty_confirmed kontrolü (talep > confirmed ise 422 `INSUFFICIENT_INVENTORY`)

### `POST /api/v1/groups/{id}/room-blocks`
- Auth: superadmin, manager
- Body: { room_type_id, qty_required, pickup_date, release_date }
- TASK-003 availability'sinden qty boş oda kontrol; yetersizse 409 `NO_AVAILABILITY`
- Başarılıysa status=confirmed, envanter reserved mark edilir (TASK-003 ile senkronize)

### `PATCH /api/v1/groups/{id}/room-blocks/{block_id}/release`
- Auth: superadmin, manager
- Blok serbest bırakılır: status=released, oda sayısı envantera geri döner
- İlişkili reservations (reservation.group_id filter) pending ise cancel edilir

### `GET /api/v1/groups/{id}/rooming-list`
- Auth: superadmin, manager, frontdesk
- 200 döner { data: [{ guest_name, room_type, checkin/checkout, status, reservation_id }], meta: { total, matched, pending } }

### `POST /api/v1/groups/{id}/rooming-list/import`
- Auth: superadmin, manager
- Body: { items: [{ guest_name, guest_email?, guest_phone?, room_type_requested, checkin_date, checkout_date }] }
- Her satır için: checkin/checkout → grup block aralığına düşüp düşmediği kontrol; group_rooming_list satırı yaz, status=pending
- Başarılı satır sayısı döner: { data: { imported: N, skipped: M }, meta: {...} }

### `POST /api/v1/groups/{id}/rooming-list/auto-match`
- Auth: superadmin, manager
- Pending rooming_list satırları ↔ room_blocks otomatik eşleştir; eşleşenlerin status=matched → reservation otomatik create (TASK-003 flow)
- 200 döner { data: { matched: N, unmatched: M }, meta: {...} }

### `POST /api/v1/events`
- Auth: superadmin, manager, fb (etkinlik)
- Body: { group_id, title, event_type, venue_id?, capacity_required, setup_type, start_datetime, end_datetime, catering_required?, notes? }
- venue_id varsa müsaitlik kontrol (start/end aralığında başka etkinlik yok)

### `GET /api/v1/events/calendar`
- Auth: superadmin, manager, frontdesk, fb
- Query: ?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&venue_id?
- 200 döner { data: [{ event_id, title, venue, time, group_name, status }], meta: {...} }

### `GET /api/v1/venues`
- Auth: superadmin, manager, frontdesk, fb
- 200 döner { data: [{ id, name, capacity_min/max, setup_types, status }], meta: {...} }

### `POST /api/v1/lost-found` (TASK-005 yeniden kullanılır — grup contextinde refactor opsiyonel)

## 3. İş Mantığı

- **Grup oluştur**: group → group_folio (master account) otomatik; konaklamalara folio_id referans
- **Room block akışı**: block pending → availability API kontrol → confirmed; envanter "reserved" durumuna set (release tarihinde auto-revert)
- **Rooming list**: CSV/upload → group_rooming_list; auto-match → reservation otomatik (sayı eşleşirse)
- **Etkinlik**: salon müsaitlik önlemesi; catering_required=true → F&B operasyonu başlatmak için flag
- **İndirim**: grup discount_rate, grup folio'sunun tüm satırlarına apply (invoice'de "grup indirimi" satırı)
- **Pickup raporu** (opsiyonel, outbox'ta describe edilir): blok pickup_date'inde housekeeping otomatik görev (TASK-005)

## 4. EventIQ AI Ajanı

### Model: `app/core/agents/event_qi.py`
- Miras: BaseAgent
- agent_name: "event_qi"
- model_provider: "deepseek" (fallback: "openai", "claude")

### `POST /api/v1/ai/eventiq/suggest-setup`
- Auth: superadmin, manager, fb
- Body: { event_type, pax_count, group_preferences?: str }
- LLM prompt (PII masked): "Verilen etkinlik tipi ve pax için salon kurulumu + kapasite + catering önerisi"
- Mock: event_type="conference" → output: { suggested_venue: "Balroom A", setup: "classroom", capacity: 150, catering_items: ["coffee", "lunch"], confidence: 0.85 }
- LLM (gerçek): DeepSeek API çağrısı
- 200 döner { data: { venue_suggestion, setup_type, catering_items, confidence, rationale }, meta: {...} }

### `GET /api/v1/ai/eventiq/upsell`
- Auth: superadmin, manager, fb
- Query: ?group_id=UUID
- LLM prompt: "Grup için F&B + oda upgrade fırsatı; geçmiş satın alma patternı"
- Mock: output: { upsell_items: [{ type: "wine_package", estimated_revenue: 5000 }, ...], confidence: 0.72 }
- 200 döner { data: { opportunities: [...] }, meta: {...} }

## 5. Testler (minimum 16)
- grup create → group_folio otomatik
- room_block create → envanter reservation
- block release → envanter revert
- rooming_list import → N/M satır, dupe kontrolü
- auto_match → rezervasyon create, status transition
- etkinlik create + salon conflict 409
- discount_rate folio satırlarına apply
- eventiq suggest-setup mock/LLM happy path
- eventiq upsell mock/LLM happy path
- RBAC: fb rolü grup create 403, token'sız 401
- status transition: inquiry→confirmed, cancelled her yerde
- eventiq LLM error handling (timeout, model unavailable)

## 6. Teslim dosyaları
```
### FILE: backend/app/models/group.py
### FILE: backend/app/models/event.py
### FILE: backend/app/routers/groups.py
### FILE: backend/app/routers/events.py
### FILE: backend/app/core/agents/event_qi.py
### FILE: backend/app/services/group_service.py
### FILE: backend/tests/test_modules/test_groups.py
### FILE: backend/migrations/versions/005_add_group_tables.py
```

## 7. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- Room block availability integration TASK-003 ile test edilmiş
- EventIQ ajanı BaseAgent'ı miras alır, registry'ye kaydolı, mock modu test için
- OpenAPI Türkçe; error kodları `INSUFFICIENT_INVENTORY`, `NO_AVAILABILITY`, `TASK_EXISTS`
