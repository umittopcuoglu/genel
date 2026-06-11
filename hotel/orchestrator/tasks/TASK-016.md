---
id: TASK-016
modül: 7 (F&B & POS Entegrasyonu)
kapsam: POS outlet yönetimi + menü + adisyon + room charge + stok + POS integrations (dış firma) + ChefIQ AI
durum: kuyrukta (TASK-004, TASK-007 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-004 (folio post), TASK-007 (BaseAgent, registry, PII mask)
---

# TASK-016 — Modül 7: F&B & POS Entegrasyonu + ChefIQ AI

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §7. ChefIQ AI tahminleri — bu görevde sadece çekirdek akış.

## 1. Veri Modeli

### `pos_outlets`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100) — "Main Restaurant", "Room Service", "Bar"
- outlet_type (VARCHAR 30) — restaurant / bar / room_service / cafe
- location_description (VARCHAR 100)
- status (VARCHAR 15, default="active") — active / inactive / closed
- pos_integration_id (UUID FK → pos_integrations.id nullable, dış POS bağlantısı)
- Index: status, outlet_type

### `menu_items`
- id (UUID, PK) [BaseModel]
- outlet_id (UUID FK → pos_outlets.id)
- name (VARCHAR 100)
- description (TEXT nullable)
- price (DECIMAL 10,2)
- tax_rate (DECIMAL 5,2, default=18) — KDV %
- category (VARCHAR 30) — appetizer / main / dessert / beverage / other
- recipe_id (UUID FK → recipes.id nullable, reçete bağı)
- status (VARCHAR 15, default="active") — active / inactive
- Index: outlet_id, category, status

### `pos_checks` (adisyon başlık)
- id (UUID, PK) [BaseModel]
- outlet_id (UUID FK → pos_outlets.id)
- room_id (UUID FK → rooms.id nullable, null=restoran adisyonu)
- server_name (VARCHAR 100 nullable)
- table_number (VARCHAR 20 nullable)
- open_time (TIMESTAMP)
- close_time (TIMESTAMP nullable)
- subtotal (DECIMAL 10,2, default=0)
- tax_amount (DECIMAL 10,2, default=0)
- total_amount (DECIMAL 10,2, default=0)
- status (VARCHAR 15, default="open") — open / closed / voided
- folio_id (UUID FK → folios.id nullable, room charge posted)
- notes (TEXT nullable)
- Index: room_id, outlet_id, status, open_time

### `pos_check_items` (adisyon satır)
- id (UUID, PK) [BaseModel]
- pos_check_id (UUID FK → pos_checks.id)
- menu_item_id (UUID FK → menu_items.id)
- qty (INT)
- unit_price (DECIMAL 10,2)
- subtotal (DECIMAL 10,2)
- notes (VARCHAR 100 nullable)
- Index: pos_check_id

### `stock_items`
- id (UUID, PK) [BaseModel]
- outlet_id (UUID FK → pos_outlets.id)
- item_name (VARCHAR 100)
- qty_on_hand (DECIMAL 10,2)
- reorder_level (DECIMAL 10,2)
- unit_cost (DECIMAL 10,2)
- last_recount_date (DATE nullable)
- status (VARCHAR 15, default="active") — active / discontinued
- Index: outlet_id, status

### `stock_movements`
- id (UUID, PK) [BaseModel]
- stock_item_id (UUID FK → stock_items.id)
- movement_type (VARCHAR 20) — sold / received / adjustment / loss / recipe_usage
- qty (DECIMAL 10,2)
- reference_id (VARCHAR 100 nullable) — pos_check_id | purchase_order_id | ...
- notes (VARCHAR 200 nullable)
- Index: stock_item_id, movement_type

### `pos_integrations` (dış POS firma bağlantısı)
- id (UUID, PK) [BaseModel]
- provider_name (VARCHAR 50) — "simphony" | "generic" | "other"
- api_key (VARCHAR 200, encrypted)
- api_secret (VARCHAR 200, encrypted)
- webhook_url (VARCHAR 200 nullable)
- status (VARCHAR 15, default="active") — active / inactive / error
- last_sync_datetime (TIMESTAMP nullable)
- notes (TEXT nullable)
- Index: provider_name, status

### `recipes`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 100)
- description (TEXT nullable)
- status (VARCHAR 15, default="active") — active / inactive
- Index: status

### `recipe_items` (reçete ürün bağı)
- id (UUID, PK) [BaseModel]
- recipe_id (UUID FK → recipes.id)
- stock_item_id (UUID FK → stock_items.id)
- qty_per_unit (DECIMAL 10,2) — 1 porsiyonda kullanılan miktar
- Index: recipe_id

## 2. Endpoint'ler

### `GET /api/v1/pos/outlets`
- Auth: superadmin, manager, fb
- 200 döner { data: [{ id, name, outlet_type, status, pos_integration_id }], meta: {...} }

### `POST /api/v1/pos/outlets`
- Auth: superadmin, manager
- Body: { name, outlet_type, location_description, pos_integration_id? }
- 201 döner outlet

### `GET /api/v1/pos/menu/{outlet_id}`
- Auth: superadmin, manager, fb, frontdesk
- 200 döner { data: [{ id, name, price, category, tax_rate }], meta: {...} }

### `POST /api/v1/pos/menu`
- Auth: superadmin, manager, fb
- Body: { outlet_id, name, description?, price, tax_rate, category, recipe_id? }
- 201 döner menu_item

### `POST /api/v1/pos/checks`
- Auth: superadmin, manager, fb
- Body: { outlet_id, room_id?, server_name?, table_number? }
- 201 döner pos_check (status=open)

### `POST /api/v1/pos/checks/{id}/items`
- Auth: superadmin, manager, fb
- Body: { menu_item_id, qty, notes? }
- menu_item'in price + tax otomatik; subtotal hesapla
- recipe_id varsa stock hareket (stock_movements); stok yetersiz ise 409 `LOW_STOCK`
- pos_check.subtotal, tax, total updatede
- 201 döner pos_check_item

### `PATCH /api/v1/pos/checks/{id}/close`
- Auth: superadmin, manager, fb
- Body: { room_charge?: boolean } — room charge'a post edecek mi?
- status=closed, close_time=now, final subtotal/tax/total hesapla
- room_charge=true ve room_id varsa:
  - aktif konaklama sorgu (TASK-003 stays'dan)
  - aktif konaklama yoksa 409 `NO_ACTIVE_STAY`
  - folio'ya type=fnb satır post (TASK-004 deseni): { item_count, amount, tax_amount }
  - folio_id set
- 200 döner { status: "closed", folio_id? }

### `GET /api/v1/pos/checks`
- Auth: superadmin, manager, fb
- Query: ?outlet_id=&room_id=&status=&from_date=&to_date=
- 200 döner { data: [{...}], meta: { total_amount, count_by_status } }

### `POST /api/v1/pos/stock`
- Auth: superadmin, manager, fb
- Body: { outlet_id, item_name, qty_on_hand, reorder_level, unit_cost }
- 201 döner stock_item

### `GET /api/v1/pos/stock`
- Auth: superadmin, manager, fb
- Query: ?outlet_id=&low_stock=true
- 200 döner { data: [{...}], meta: { low_stock_count } }

### `POST /api/v1/pos/stock/movement`
- Auth: superadmin, manager, fb
- Body: { stock_item_id, movement_type, qty, reference_id?, notes? }
- stock_item.qty_on_hand güncelle
- qty_on_hand < reorder_level ise WS bildir (düşük stok uyarısı)
- 201 döner stock_movement

### `POST /api/v1/pos/webhook`
- Auth: dış POS (API key doğrulama)
- Body: { event, data: {...} } — event="check_closed" | "check_voided" | ...
- pos_integrations'ten provider_name fetch; adapter (simphony.py / generic.py) activate
- check verisi normalize edip local check'e senkronize
- 200 döner { success: true }

### `POST /api/v1/pos/recipes`
- Auth: superadmin, manager, fb
- Body: { name, description?, recipe_items: [{ stock_item_id, qty_per_unit }] }
- 201 döner recipe + recipe_items

## 3. İş Mantığı

- **Adisyon aç**: pos_check (status=open); room_id varsa room charge intent işaretlenir
- **Satır ekle**: menu_item + qty; reçete varsa stok düşümü (stock_movements); stok < reorder ise flag
- **Adisyon kapat**: close_time, final subtotal/tax/total; room_charge ise folio'ya FNB satırı post (aktif konaklama kontrolü, 409 NO_ACTIVE_STAY)
- **Reçete kullanımı**: menu_item.recipe_id varsa satın alınan qty → recipe_items × qty / qty_per_unit stok hareket
- **POS entegrasyonu**: dış POS firma (webhook) → check data gönder → local base.py adapter (mock-first: simphony.py, generic.py)
- **Stok yönetimi**: movement → qty_on_hand güncelle; < reorder_level ise WS bildir
- **KDV**: menu_item.tax_rate otomatik hesapla; adisyon satırında subtotal × (1 + tax_rate/100)

## 4. Dış Sistem Integrasyon (Mock-First)

### Adapter Deseni
```
integrations/pos/base.py: BasePOSAdapter (abstract)
  - send_check(check_data) → async
  - receive_webhook(event_data) → async
integrations/pos/simphony.py: SimphonyAdapter (mock-first)
integrations/pos/generic.py: GenericAdapter (mock-first)
```
- Gerçek anahtar `pos_integrations.api_key` → .env'den
- Test: adapter mock mode (in-memory queue)

## 5. ChefIQ AI Ajanı

### Model: `app/core/agents/chef_iq.py`
- Miras: BaseAgent
- agent_name: "chef_iq"
- model_provider: "deepseek" (fallback: "openai", "claude")

### `POST /api/v1/ai/chefiq/forecast-demand`
- Auth: superadmin, manager, fb
- Body: { outlet_id, days_ahead: 7, from_date?: YYYY-MM-DD }
- LLM prompt (PII masked): "Geçmiş satış verisi → ürün talep tahmini, sezonalite"
- Mock: output: { forecast: [{ menu_item_id, predicted_qty, confidence }, ...], rationale }
- LLM (gerçek): DeepSeek API (son N gün satış fetch → prompt)
- 200 döner { data: { forecast: [...], peak_hours: [...] }, meta: {...} }

### `GET /api/v1/ai/chefiq/menu-insights`
- Auth: superadmin, manager, fb
- Query: ?outlet_id=&metric=profit|popularity
- LLM prompt: "Menu items profitability + popularity matrisi"
- Mock: output: { insights: [{ menu_item_id, profit_margin, popularity_rank, action: "promote" | "review" }, ...] }
- 200 döner { data: { insights: [...] }, meta: {...} }

## 6. Testler (minimum 16)
- outlet CRUD
- menu_item create + tax otomatik
- pos_check create → status=open
- pos_check_item add → subtotal hesapla, reçete varsa stok düş
- low_stock flag, WS bildir
- pos_check close → final amounts, folio post (room_charge=true)
- room_charge=true, no active stay → 409 NO_ACTIVE_STAY
- pos_webhook → adapter normalize
- stock_movement → qty_on_hand update
- recipe create + recipe_items
- chefiq forecast-demand mock/LLM happy path
- chefiq menu-insights mock/LLM happy path
- RBAC: fb outlet create ✓, recipe create ✓, outlet_id change 403
- KDV tax calculation doğru
- adapter error handling (webhook malformed, API timeout)

## 7. Teslim dosyaları
```
### FILE: backend/app/models/pos.py
### FILE: backend/app/routers/pos.py
### FILE: backend/app/services/pos_service.py
### FILE: backend/app/core/agents/chef_iq.py
### FILE: backend/integrations/pos/base.py
### FILE: backend/integrations/pos/simphony.py
### FILE: backend/integrations/pos/generic.py
### FILE: backend/tests/test_modules/test_pos.py
### FILE: backend/migrations/versions/005_add_pos_tables.py
```

## 8. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- POS webhook → adapter normalize test edilmiş; mock vs. gerçek mod
- ChefIQ ajanı BaseAgent'ı miras alır, registry'ye kaydolı, mock modu test için
- Folio post entegrasyonu (TASK-004 deseni) test edilmiş
- OpenAPI Türkçe; error kodları `LOW_STOCK`, `NO_ACTIVE_STAY`, adapter-spesifik hatalar
