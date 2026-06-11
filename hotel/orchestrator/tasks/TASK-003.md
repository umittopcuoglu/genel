---
id: TASK-003
modül: 2 (Rezervasyon & Müsaitlik)
kapsam: rate_plans + availability + rezervasyon CRUD + occupancy takvimi
durum: kuyrukta (TASK-002 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-002 (rooms, room_types, guests, reservations tabloları)
---

# TASK-003 — Modül 2: Rezervasyon & Müsaitlik

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §2. Channel Manager entegrasyonları Faz 2'dir, bu görevde YOK.

## 1. Veri Modeli (yeni tablolar)

### `rate_plans`
- id (UUID, PK) [BaseModel: timestamps + soft delete + created_by/updated_by]
- code (VARCHAR 20, UNIQUE) — örn. "BAR", "NONREF", "BB"
- name (VARCHAR 100)
- room_type_id (FK → room_types.id)
- base_rate (DECIMAL 10,2) — bu plan için gecelik fiyat
- restrictions (JSONB) — { "min_los": 2, "cta": false, "ctd": false, "closed": false }
- active (BOOLEAN, default=true)
- Index: code, room_type_id

### `availability`
- id (UUID, PK) [BaseModel]
- room_type_id (FK → room_types.id)
- date (DATE)
- available_count (INT) — satılabilir oda sayısı
- sold_count (INT, default=0)
- UNIQUE(room_type_id, date)
- Index: (room_type_id, date)

## 2. Endpoint'ler

### `POST /api/v1/reservations`
- Auth: superadmin, manager, frontdesk
- Body: { guest_id | guest: {inline yeni misafir}, room_type_id, check_in, check_out, adults, kids, source, rate_plan_id?, special_requests? }
- İş mantığı:
  1. check_in < check_out, geçmiş tarih reddi (422)
  2. Müsaitlik kontrolü: her gece için available_count - sold_count > 0, yoksa 409 `NO_AVAILABILITY`
  3. rate_plan varsa restrictions kontrolü (min_los, closed) — ihlalde 409 `RATE_RESTRICTION`
  4. code üret: "RES-YYYYMMDD-NNN"
  5. total_amount = gece sayısı × rate (rate_plan.base_rate yoksa room_type.base_rate); balance = total_amount
  6. availability.sold_count her gece için +1
- 201: { data: {rezervasyon objesi}, meta: {} }

### `PUT /api/v1/reservations/{id}`
- Auth: superadmin, manager, frontdesk
- Tarih/oda tipi değişiminde müsaitlik yeniden hesaplanır (eski geceler -1, yeni geceler +1)
- checked_out/cancelled rezervasyon değiştirilemez → 409 `RESERVATION_LOCKED`

### `POST /api/v1/reservations/{id}/cancel`
- Auth: superadmin, manager, frontdesk
- status → cancelled, availability.sold_count her gece -1
- checked_in rezervasyon iptal edilemez → 409

### `GET /api/v1/reservations?status=&from=&to=&q=`
- Auth: superadmin, manager, frontdesk
- q: code veya misafir adında arama; {data, meta} zarfı + sayfalama (page, per_page)

### `GET /api/v1/availability/calendar?from=&to=`
- Auth: superadmin, manager, frontdesk
- Dönen: oda tipi başına gün-gün müsaitlik matrisi
- { data: [ { room_type: {...}, days: [ {date, available, sold} ] } ], meta: {} }

### `GET /api/v1/occupancy?from=&to=`
- Auth: superadmin, manager
- Gün bazında doluluk %: { data: [ {date, occupancy_pct, sold, capacity} ], meta: {} }

### `POST /api/v1/rate-plans` + `PATCH /api/v1/rate-plans/{id}` + `GET /api/v1/rate-plans`
- Auth: superadmin, manager
- Standart CRUD; restrictions JSONB validasyonu (bilinmeyen anahtar 422)

## 3. Testler (minimum 16)
- Rezervasyon oluşturma happy (201, availability düştü)
- Müsaitlik yoksa 409 NO_AVAILABILITY
- min_los ihlali 409 RATE_RESTRICTION
- Geçmiş tarih 422
- PUT tarih değişikliği → availability doğru güncellenir
- checked_out PUT → 409 RESERVATION_LOCKED
- Cancel happy → sold_count düşer
- checked_in cancel → 409
- GET reservations filtre + arama + sayfalama
- availability/calendar doğru matris
- occupancy hesabı doğru
- rate-plans CRUD happy + 422
- RBAC: housekeeping rezervasyon oluşturamaz (403)
- Token'sız 401

## 4. Teslim dosyaları
```
### FILE: backend/app/models/reservation_ext.py     (RatePlan, Availability)
### FILE: backend/app/routers/reservations.py
### FILE: backend/app/routers/rate_plans.py
### FILE: backend/app/routers/availability.py
### FILE: backend/tests/test_modules/test_reservations.py
### FILE: backend/migrations/versions/003_add_reservation_tables.py
```

## 5. Kabul kriterleri
- pytest backend/tests + qa/contract tümü yeşil
- Hata zarfı, audit log, soft delete, RBAC — review.py PASS
- OpenAPI Türkçe summary/description
