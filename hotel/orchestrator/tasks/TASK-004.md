---
id: TASK-004
modül: 4 (Muhasebe & Cashiering)
kapsam: folio + folio_items + payments + night audit + temel raporlar
durum: kuyrukta (TASK-003 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-002 (stays.folio_id), TASK-003 (reservations.balance)
---

# TASK-004 — Modül 4: Muhasebe & Cashiering

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §4. GİB e-Fatura, Logo/SAP, sanal POS Faz 2'dir — bu görevde YOK.

## 1. Veri Modeli

### `folios`
- id (UUID, PK) [BaseModel]
- reservation_id (FK → reservations.id)
- guest_id (FK → guests.id)
- status (VARCHAR 10, default="open") — open / closed
- total (DECIMAL 12,2, default=0)
- balance (DECIMAL 12,2, default=0)
- Index: reservation_id, guest_id, status

### `folio_items`
- id (UUID, PK) [BaseModel]
- folio_id (FK → folios.id)
- type (VARCHAR 10) — room / fnb / extra / tax / adj
- description (VARCHAR 255)
- qty (INT, default=1)
- unit_price (DECIMAL 10,2)
- tax_rate (DECIMAL 5,2) — KDV %: 1, 8, 18, 20
- total (DECIMAL 12,2) — qty × unit_price × (1 + tax_rate/100)
- posted_at (TIMESTAMP)
- Index: folio_id, type

### `payments`
- id (UUID, PK) [BaseModel]
- folio_id (FK → folios.id)
- method (VARCHAR 10) — cash / card / transfer / vpos
- amount (DECIMAL 12,2)
- currency (VARCHAR 3, default="TRY")
- ref (VARCHAR 100 nullable) — dekont/slip no
- status (VARCHAR 10, default="completed") — completed / refunded / failed
- Index: folio_id, method

### `night_audit_runs` (append-only)
- id (UUID, PK)
- business_date (DATE, UNIQUE)
- run_by (UUID FK)
- run_at (TIMESTAMP)
- stats (JSONB) — { rooms_posted, total_room_revenue, no_shows_marked }

## 2. Endpoint'ler

### `POST /api/v1/folios/{id}/charge`
- Auth: superadmin, manager, frontdesk, accounting
- Body: { type, description, qty, unit_price, tax_rate }
- folio closed ise 409 `FOLIO_CLOSED`; total/balance yeniden hesaplanır

### `POST /api/v1/folios/{id}/payment`
- Auth: superadmin, manager, frontdesk, accounting
- Body: { method, amount, currency?, ref? }
- amount > balance ise 422 `OVERPAYMENT` (detayda kalan bakiye)
- balance güncellenir; reservations.balance senkron tutulur

### `POST /api/v1/folios/{id}/close`
- Auth: superadmin, manager, accounting
- balance != 0 → 409 `OUTSTANDING_BALANCE`
- status → closed

### `GET /api/v1/folios/{id}` + `GET /api/v1/folios?reservation_id=&status=`
- Auth: superadmin, manager, frontdesk, accounting
- Detayda items + payments gömülü döner

### `POST /api/v1/night-audit/run`
- Auth: superadmin, manager
- Body: { business_date }
- İş mantığı:
  1. Aynı business_date için tekrar koşulamaz → 409 `AUDIT_ALREADY_RUN`
  2. in-house tüm konaklamalara o gecenin oda ücretini folio'ya post et (type=room)
  3. Bugün check-in olması gereken ama gelmeyen confirmed rezervasyonları no_show işaretle
  4. night_audit_runs kaydı + stats
- 200: { data: { business_date, stats }, meta: {} }

### Raporlar (Auth: superadmin, manager, accounting)
- `GET /api/v1/reports/occupancy?from=&to=` — gün bazında doluluk
- `GET /api/v1/reports/adr?from=&to=` — ADR = oda geliri / satılan oda
- `GET /api/v1/reports/revpar?from=&to=` — RevPAR = oda geliri / toplam oda
- Hepsi { data: [...gün satırları], meta: { summary: {...} } }

### Check-out entegrasyonu (TASK-002 revizyonu)
- `POST /api/v1/checkout/{reservation_id}` artık folio balance'ı gerçek folio'dan okumalı (request body'deki folio_balance kaldırılır).

## 3. Testler (minimum 16)
- charge happy → total/balance doğru (KDV dahil)
- closed folio'ya charge 409
- payment happy → balance düşer
- overpayment 422
- close happy / balance!=0 409
- night-audit happy → oda ücretleri post edildi, no_show işaretlendi
- night-audit tekrar 409
- ADR/RevPAR/occupancy hesapları bilinen fixture ile doğrulanır
- checkout folio entegrasyonu: balance>0 → 409
- RBAC: housekeeping charge atamaz 403; token'sız 401

## 4. Teslim dosyaları
```
### FILE: backend/app/models/finance.py
### FILE: backend/app/routers/folios.py
### FILE: backend/app/routers/night_audit.py
### FILE: backend/app/routers/reports.py
### FILE: backend/app/routers/frontoffice.py        (checkout revizyonu — tam dosya)
### FILE: backend/tests/test_modules/test_finance.py
### FILE: backend/migrations/versions/004_add_finance_tables.py
```

## 5. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- Para alanlarında float YOK — Decimal zorunlu
- OpenAPI Türkçe
