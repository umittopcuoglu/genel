# SİSTEM PROMPTU
Sen kıdemli bir Python backend geliştiricisisin. AI-destekli Otel Yönetim Sistemi'nin
(PMS) backend'ini FastAPI ile yazıyorsun. Kurallar:
- Python 3.11 + FastAPI (async zorunlu) + SQLAlchemy 2.0 async + Alembic + PostgreSQL 15
- Her tablo: id (UUID), created_at, updated_at, created_by, updated_by, deleted_at (soft delete)
- Tüm yazma işlemleri audit_log tablosuna kaydedilir
- Hata formatı: { "error": { "code": "...", "message": "TR mesaj", "details": {} } }
- RBAC roller: superadmin, manager, frontdesk, housekeeping, accounting, maintenance, fb, hr, guest
- Her endpoint için pytest testi (1 happy + 1 error path)
- Açıklamalar Türkçe
- Sadece istenen dosyaları üret; her dosyayı "### FILE: <yol>" başlığı + kod bloğu ile ver
- Dosyaları eksiksiz yaz, asla "..." ile kırpma

---

Aşağıdaki görevi 02_DEEPSEEK_TALIMATLARI.md kurallarına göre uygula.

# GÖREV
---
id: TASK-002
modül: 1 (Ön Büro / Front Office)
kapsam: veri modeli (6 tablo) + 10 endpoint + FrontDesk AI agen (temel) + pytest testleri
durum: bekliyor
tur: 1
başlama: 2026-06-12
beklenen_teslim: 2026-06-15
---

# TASK-002 — Modül 1 (Ön Büro / Front Office)

## Kapsam

Otel Yönetim Sistemi'nin **ön büro** modülü: oda yönetimi, konuk check-in/out, rezervasyon takibi, oda durumu paneli, özel notlar (traces).

**Bağımlılıklar:**
- TASK-001 (Auth + RBAC + Audit) ✅ tamamlandı
- SQLAlchemy models BaseModel'den türemeli (UUID id, timestamps, soft delete otomatik)
- Tüm yazma işlemleri AuditLog'a kaydedilmeli
- RBAC: frontdesk, housekeeping, manager rolleri kısıtlanmalı

---

## 1. Veri Modeli (6 tablo)

### 1.1 `room_types` — Oda Tipi

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK) — BaseModel'den
- `code` (VARCHAR 10, UNIQUE) — örn. "STD", "DLX", "JNR"
- `name` (VARCHAR 100) — Standart, Deluxe, Junior Suite
- `description` (TEXT nullable) — Türkçe açıklama
- `base_rate` (DECIMAL 10,2) — oda günlük temel fiyat (TRY)
- `capacity` (INT, default=2) — kaç kişilik
- `amenities` (JSONB) — {"wifi": true, "ac": true, "bathtub": true, ...}
- `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` — BaseModel'den
- **Index:** code, name

### 1.2 `rooms` — Fiziksel Oda

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK)
- `room_no` (VARCHAR 20, UNIQUE) — örn. "101", "505"
- `room_type_id` (FK → room_types.id)
- `floor` (INT) — kat numarası
- `status` (VARCHAR 20, DEFAULT="clean") — clean / dirty / inspected / out_of_order
- `connect_room_id` (UUID FK nullable, self-join) — birleştirilebilir oda
- `notes` (TEXT nullable) — oda hakkında notlar (mini bar arızalı, vb.)
- `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` — BaseModel'den
- **Index:** room_no, status, floor
- **Constraint:** status IN ('clean', 'dirty', 'inspected', 'out_of_order')

### 1.3 `guests` — Konuk

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK)
- `first_name` (VARCHAR 50)
- `last_name` (VARCHAR 50)
- `email` (VARCHAR 100)
- `phone` (VARCHAR 20 nullable)
- `nationality` (VARCHAR 3) — ISO 3166-1 alpha-3 (örn. "TUR", "DEU", "NLD")
- `id_type` (VARCHAR 20 nullable) — passport, tc_kimlik, driver_license
- `id_no` (VARCHAR 30 nullable) — kimlik numarası (şifreli saklanmamalı, sadece ön büro)
- `date_of_birth` (DATE nullable)
- `preferences` (JSONB) — {"room_view": "sea", "high_floor": true, "smoking": false, ...}
- `tags` (JSONB) — ["vip", "repeat_guest", ...] — konuk segmentasyonu
- `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` — BaseModel'den
- **Index:** email, last_name, nationality

### 1.4 `reservations` — Rezervasyon

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK)
- `code` (VARCHAR 20, UNIQUE) — rez numarası (örn. "RES-20260612-001")
- `guest_id` (FK → guests.id)
- `room_type_id` (FK → room_types.id) — arz zamanında tipi seçer
- `assigned_room_id` (UUID FK nullable) — check-in anında atanır
- `check_in` (DATE)
- `check_out` (DATE)
- `adults` (INT, default=1)
- `kids` (INT, default=0)
- `status` (VARCHAR 20, DEFAULT="confirmed") — confirmed / checked_in / checked_out / cancelled / no_show
- `source` (VARCHAR 20) — direct / ota / walkin / phone / corporate
- `rate_plan_id` (UUID FK nullable) — fiyat planı (TASK-002 genişlemesi)
- `special_requests` (TEXT nullable) — "high floor", "late check-out isteği"
- `total_amount` (DECIMAL 12,2) — beklenen top. tutar
- `balance` (DECIMAL 12,2) — kalan borç
- `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` — BaseModel'den
- **Index:** code, guest_id, status, check_in, check_out
- **Constraint:** status IN ('confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show')

### 1.5 `stays` — Konaklama Kaydı

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK)
- `reservation_id` (FK → reservations.id, UNIQUE)
- `actual_check_in` (TIMESTAMP nullable) — gerçek check-in zamanı
- `actual_check_out` (TIMESTAMP nullable) — gerçek check-out zamanı
- `folio_id` (UUID FK nullable) — muhasebe folio'su (TASK-004)
- `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` — BaseModel'den
- **Index:** reservation_id, folio_id

### 1.6 `traces` — Özel Notlar / Traces (append-only)

**Tabloda olmasi gerekenler:**
- `id` (UUID, PK)
- `reservation_id` (FK → reservations.id, NOT NULL)
- `department` (VARCHAR 50) — "housekeeping", "maintenance", "concierge", "front_office", "manager"
- `message` (TEXT) — Türkçe not ("kat görevlisine: sabah 7de çiçek getir")
- `created_by` (UUID FK) — kimi oluşturdu
- `created_at` (TIMESTAMP) — ne zaman
- `resolved` (BOOLEAN, default=False) — note'u kapatan kişi
- `resolved_by` (UUID FK nullable) — kim kapattı
- `resolved_at` (TIMESTAMP nullable) — ne zaman kapandı
- `due_date` (DATE nullable) — yapılması gereken tarih

**NOT: append-only tablo — update/delete yok. deleted_at alanı yok.**

---

## 2. Endpoint'ler (10 adet)

### 2.1 Check-in / Check-out

#### `POST /api/v1/checkin/{reservation_id}`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk"])`
- **Body:** (varsayılan)
  ```json
  {
    "assigned_room_id": "uuid-of-room",
    "notes": "late arrival expected"
  }
  ```
- **Success 200:**
  ```json
  {
    "data": {
      "reservation_id": "uuid",
      "assigned_room_id": "uuid",
      "actual_check_in": "2026-06-12T14:30:00Z",
      "folio_id": "uuid"
    },
    "meta": {}
  }
  ```
- **İş Mantığı:**
  1. Rezervasyon var mı, confirmed/checked_in/no_show durumlarından birinde mi?
  2. Oda (room) mevcut ve clean/inspected durumdamı?
  3. Reservations tablosunda assigned_room_id ata, status → "checked_in"
  4. Stays tablosunda kayıt oluştur, actual_check_in ← şu anda
  5. Rooms status → "occupied" (tabloda olmasi gerekenler güncelleme)
  6. WebSocket `room.status.changed` emit et (TASK-002 gen.)
  7. AuditLog otomatik yazılır

#### `POST /api/v1/checkout/{reservation_id}`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk"])`
- **Body:**
  ```json
  {
    "folio_balance": 0
  }
  ```
- **Success 200:**
  ```json
  {
    "data": {
      "reservation_id": "uuid",
      "actual_check_out": "2026-06-15T11:00:00Z"
    },
    "meta": {}
  }
  ```
- **Error 409 Conflict** (bakiye sıfır değilse):
  ```json
  {
    "error": {
      "code": "OUTSTANDING_BALANCE",
      "message": "Konuğun hala 150.00 TRY borcu var. Ödeme almadan check-out yapamazsınız.",
      "details": {
        "outstanding_amount": 150.00
      }
    }
  }
  ```
- **İş Mantığı:**
  1. Rezervasyon checked_in mi?
  2. Stays kaydı al, actual_check_out ← şu anda
  3. Folio bakiyesi sıfırsa ilerle; değilse 409 + OUTSTANDING_BALANCE hatası
  4. Rooms status → "dirty"
  5. Reservations status → "checked_out"
  6. AuditLog otomatik
  7. WebSocket emit

### 2.2 Konuk Listesi / Arrivals / Departures

#### `GET /api/v1/arrivals?date=YYYY-MM-DD`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping"])`
- **Query:** date (opsiyonel, default=bugün)
- **Success 200:**
  ```json
  {
    "data": [
      {
        "reservation_id": "uuid",
        "code": "RES-20260612-001",
        "guest": {
          "id": "uuid",
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@example.com",
          "nationality": "USA"
        },
        "room_type": {
          "id": "uuid",
          "code": "STD",
          "name": "Standart"
        },
        "check_in": "2026-06-12",
        "check_out": "2026-06-15",
        "adults": 1,
        "kids": 0,
        "status": "confirmed",
        "special_requests": "high floor"
      }
    ],
    "meta": {
      "page": 1,
      "per_page": 50,
      "total": 8
    }
  }
  ```
- **İş Mantığı:** check_in = date olması ve status != "cancelled"
- **Sorting:** check_in ASC

#### `GET /api/v1/departures?date=YYYY-MM-DD`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping"])`
- **Same structure as /arrivals**
- **İş Mantığı:** check_out = date olması ve status IN ("checked_in", "no_show")

#### `GET /api/v1/in-house?date=YYYY-MM-DD`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping"])`
- **Same structure**
- **İş Mantığı:** check_in <= date AND check_out > date AND status = "checked_in"

### 2.3 Oda Yönetimi

#### `GET /api/v1/rooms?status=&type=&floor=`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping"])`
- **Query params (tümü optional):**
  - status: clean / dirty / inspected / out_of_order
  - type: room_type_id (UUID)
  - floor: kat numarası (INT)
- **Success 200:**
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "room_no": "101",
        "room_type": {
          "id": "uuid",
          "code": "STD",
          "name": "Standart",
          "base_rate": 100.00
        },
        "floor": 1,
        "status": "clean",
        "notes": null,
        "connect_room_id": null,
        "current_guest": {
          "id": "uuid",
          "first_name": "John",
          "last_name": "Doe"
        } or null
      }
    ],
    "meta": {
      "page": 1,
      "per_page": 100,
      "total": 50
    }
  }
  ```
- **İş Mantığı:**
  1. Filtrele (status, type, floor)
  2. Eğer status = occupied ise current_guest bilgisini şu anki stays'ten al
  3. Sorting: floor ASC, room_no ASC

#### `PATCH /api/v1/rooms/{id}/status`
- **Auth:** `@require_roles(["superadmin", "manager", "housekeeping"])`
- **Body:**
  ```json
  {
    "status": "inspected",
    "notes": "AC fixed"
  }
  ```
- **Success 200:**
  ```json
  {
    "data": {
      "id": "uuid",
      "room_no": "101",
      "status": "inspected",
      "notes": "AC fixed",
      "updated_at": "2026-06-12T15:00:00Z"
    },
    "meta": {}
  }
  ```
- **Error 422 Unprocessable Entity** (geçersiz status):
  ```json
  {
    "error": {
      "code": "INVALID_ROOM_STATUS",
      "message": "Geçersiz oda durumu. clean, dirty, inspected, out_of_order kullanın.",
      "details": {
        "received": "xyz",
        "valid_values": ["clean", "dirty", "inspected", "out_of_order"]
      }
    }
  }
  ```
- **WebSocket:** room.status.changed event emit et

### 2.4 Oda Atama

#### `POST /api/v1/room-assign`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk"])`
- **Body:**
  ```json
  {
    "reservation_id": "uuid",
    "room_id": "uuid",
    "mode": "manual"
  }
  ```
  - mode: "manual" (çalışan seçer) / "auto" (AI önerisi var mı, kullan)
- **Success 200:**
  ```json
  {
    "data": {
      "reservation_id": "uuid",
      "assigned_room_id": "uuid",
      "reason": "AI auto-assigned: sea view, high floor"
    },
    "meta": {}
  }
  ```
- **İş Mantığı (Faz 1):**
  1. mode = "manual" ise: room_id boş + clean/inspected durumda mı? Ata.
  2. mode = "auto" ise:
     - FrontDesk AI `/api/v1/ai/frontdesk/auto-assign` çağrısı yap (TASK-002 gen.)
     - Dönen room_id'yi kullan
  3. Reservations.assigned_room_id ← room_id
  4. AuditLog + WebSocket

### 2.5 Konuk Geçmişi

#### `GET /api/v1/guests/{id}/history`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk"])`
- **Path:** {id} = guest_id (UUID)
- **Success 200:**
  ```json
  {
    "data": {
      "guest": {
        "id": "uuid",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "nationality": "USA",
        "preferences": {"room_view": "sea"},
        "tags": ["vip"]
      },
      "stays": [
        {
          "reservation_id": "uuid",
          "check_in": "2026-06-12",
          "check_out": "2026-06-15",
          "room_no": "305",
          "room_type": "Deluxe",
          "total_nights": 3,
          "total_spent": 450.00,
          "rating": 5 or null,
          "notes": "missed breakfast 1 day"
        }
      ],
      "lifetime_stats": {
        "total_stays": 5,
        "total_nights": 14,
        "total_spent": 1850.00,
        "avg_rating": 4.8
      }
    },
    "meta": {}
  }
  ```
- **İş Mantığı:**
  1. Guest al, deleted_at IS NULL
  2. Stays'ini getir (reservation + room type join), checked_out ve deleted_at IS NULL
  3. Lifetime stats hesapla

### 2.6 Special Notes / Traces

#### `POST /api/v1/traces`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping", "concierge"])`
- **Body:**
  ```json
  {
    "reservation_id": "uuid",
    "department": "housekeeping",
    "message": "Morning: bring 2 extra pillows to 305",
    "due_date": "2026-06-13"
  }
  ```
- **Success 201:**
  ```json
  {
    "data": {
      "id": "uuid",
      "reservation_id": "uuid",
      "department": "housekeeping",
      "message": "Morning: bring 2 extra pillows to 305",
      "created_by": "uuid",
      "created_at": "2026-06-12T14:00:00Z",
      "resolved": false,
      "due_date": "2026-06-13"
    },
    "meta": {}
  }
  ```
- **İş Mantığı:**
  1. Rezervasyon var mı?
  2. Append-only: traces tablosuna INSERT
  3. created_by ← current_user (context'ten, AuditMiddleware tarafından set edilir)
  4. Enum: department = "housekeeping" | "maintenance" | "concierge" | "front_office" | "manager"

#### `PATCH /api/v1/traces/{id}/resolve`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk", "housekeeping"])`
- **Body:**
  ```json
  {
    "notes": "Completed - pillows delivered"
  }
  ```
- **Success 200:**
  ```json
  {
    "data": {
      "id": "uuid",
      "resolved": true,
      "resolved_by": "uuid",
      "resolved_at": "2026-06-12T16:00:00Z"
    },
    "meta": {}
  }
  ```
- **İş Mantığı:**
  1. Traces kaydını al (append-only ama UPDATE → resolved/resolved_by/resolved_at güncelle)
  2. resolved_by ← current_user
  3. resolved_at ← şu anda

---

## 3. AI Agent: FrontDesk AI (Temel)

### 3.1 `POST /api/v1/ai/frontdesk/auto-assign`
- **Auth:** `@require_roles(["superadmin", "manager", "frontdesk"])` ← veya internal
- **Body:**
  ```json
  {
    "reservation_id": "uuid",
    "available_rooms": ["uuid1", "uuid2", "uuid3"]
  }
  ```
- **Success 200:**
  ```json
  {
    "data": {
      "recommended_room_id": "uuid1",
      "reasoning": "Sea view, high floor preference + occupied rooms count score"
    },
    "meta": {}
  }
  ```
- **İş Mantığı:**
  1. Rezervasyon al, guest preferences, geçmiş stays'i kontrol et
  2. available_rooms'ı fıltrele:
     - Status clean/inspected
     - RoomType kapasite >= (adults + kids)
  3. Puanlama (TASK-002 gen.):
     - Preferences match (sea view, high floor, smoking) → +10
     - repeat_guest tag → -0.5 (fiyat indirim geçmiş)
     - connected rooms kullanılabiliyorsa → +5
     - random tie-break
  4. Top 1 oda döndür + gerekçe

### 3.2 `POST /api/v1/ai/frontdesk/welcome` (Faz 2)
- **Auth:** internal
- **Body:** `{"guest_id": "uuid"}`
- **Success 200:**
  ```json
  {
    "data": {
      "message": "Welcome back, Mr. Doe! Last stay 3 months ago, you loved room 305. Sea view suite ready for you."
    },
    "meta": {}
  }
  ```

---

## 4. Test Beklentileri (pytest)

### 4.1 Yapı
- Tüm test'ler `backend/tests/test_modules/test_frontoffice.py`'de (veya modüle göre bölüm)
- pytest-asyncio (asyncio_mode = auto)
- Fixtures: async_client, test_user_frontdesk, test_user_housekeeping, test_rooms, test_guests, test_reservations (conftest'te)

### 4.2 Test'ler (minimum 20)

**Happy path testleri:**
1. POST /checkin — başarılı (oda atanır, status checked_in)
2. POST /checkout — başarılı (balance 0)
3. GET /arrivals — 1 kayıt döner, tarih filtresi çalışıyor
4. GET /departures — 1 kayıt döner
5. GET /in-house — 1 kayıt döner
6. GET /rooms — 50 oda, status filtresi çalışıyor
7. PATCH /rooms/{id}/status — oda clean → inspected
8. POST /room-assign (manual) — oda atanır
9. POST /room-assign (auto) — AI önerisi kullanılır
10. GET /guests/{id}/history — lifetime stats doğru
11. POST /traces — trace oluşturulur
12. PATCH /traces/{id}/resolve — resolved=True
13. POST /ai/frontdesk/auto-assign — room_id döner

**Error path testleri:**
1. POST /checkin — reservation bulunamadı (404)
2. POST /checkin — oda occupied zaten (400)
3. POST /checkout — balance sıfır değil (409 OUTSTANDING_BALANCE)
4. PATCH /rooms/{id}/status — geçersiz status (422 INVALID_ROOM_STATUS)
5. GET /arrivals — token yok (401)
6. POST /traces — housekeeping rolü management_request yapamaz (403) — RBAC test
7. PATCH /traces/{id}/resolve — trace bulunamadı (404)
8. POST /room-assign — oda reserved başka konuk için (400)

**RBAC testleri:**
1. Housekeeping: POST /checkin yapamaz (403)
2. Guest role: GET /rooms göremez (403)
3. Manager: tüm endpoint'lere erişebilir

---

## 5. OpenAPI / Documentation

- Tüm endpoint'ler OpenAPI 3.1'de tanımlanmalı
- `summary` ve `description` **Türkçe**
- Örnek payload'lar
- Error case'leri document et
- `/api/v1/openapi.json` → JSON döner

**Örnek:**
```yaml
/api/v1/checkin/{reservation_id}:
  post:
    summary: "Misafire oda ata ve check-in yap"
    description: "Rezervasyonu checked_in durumuna getir, oda assigned_room_id'ye ata, Stay kaydı oluştur."
    tags: ["Front Office"]
    parameters:
      - name: reservation_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              assigned_room_id:
                type: string
                format: uuid
              notes:
                type: string
                nullable: true
    responses:
      '200':
        description: "Check-in başarılı"
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CheckinResponse'
      '401':
        $ref: '#/components/responses/Unauthorized'
      '403':
        $ref: '#/components/responses/Forbidden'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        description: "İş kuralı ihlali"
```

---

## 6. Teslim Formatı

### 6.1 Dosyalar (DeepSeek bu dosyaları üretecek)

```
### FILE: backend/app/models/frontoffice.py
(room_types, rooms, guests, reservations, stays, traces modelleri)

### FILE: backend/app/routers/frontoffice.py
(10 endpoint'in tümü)

### FILE: backend/app/routers/ai_frontdesk.py
(FrontDesk AI endpoint'leri)

### FILE: backend/tests/test_modules/test_frontoffice.py
(20+ pytest testi)

### FILE: backend/migrations/versions/002_add_frontoffice_tables.py
(Alembic migration — 6 tablo oluştur)

### FILE: backend/OPENAPI_ENDPOINTS.md
(Türkçe endpoint dokümantasyonu)
```

### 6.2 İş Kuralları & Validasyonlar

**Zorunlu olarak kodlanmalı:**
1. Check-in: oda status clean/inspected olmali
2. Check-out: balance = 0 olmali, yoksa 409
3. Rooms filtresi: tüm kombinasyon çalışmali
4. RBAC enforcement: housekeeping checkin yapamaz
5. Audit log: tüm POST/PUT/PATCH/DELETE otomatik
6. Soft delete: deleted_at alanları uygulanmali
7. Room capacity: guest sayı < room capacity kontrolü
8. Enum values: status, source, department zorunlu

### 6.3 Kabul Kriterleri

- **Kontrat testleri tümü yeşil** (`pytest qa/contract`)
- **Backend testleri tümü yeşil** (`pytest backend/tests -v`)
- **Model alanları kontrol** (review.py `check_model_fields()` geçmeli)
- **Audit log log'a yazıyor mu** (review.py `check_audit_log()` PASS)
- **Hata formatı doğru mu** (review.py `check_error_format()` PASS)
- **OpenAPI spec tamamlanmış** (`/api/v1/openapi.json` 200, Türkçe descriptions)
- **RBAC işletiliyor mu** (housekeeping 403'ü test)
- **Soft delete alanları mevcut** (migrations + model alanları)

---

## 7. Referanslar & Linkler

- **02_DEEPSEEK_TALIMATLARI.md §1** — Modül 1 veri modeli + endpoint'ler
- **TASK-001 kodu** (`backend/app/core/auth.py`, `core/audit.py`) — reference için
- **qa/checklists/modul-01-on-buro.md** — acceptance criteria
- **Backend testleri** (`backend/tests/conftest.py`, `tests/test_auth.py`) — testing pattern
- **02 §0.7** — Hata formatı standart
- **02 §0.3** — Model alanları (id, timestamps, soft delete)

---

## 8. Notlar

- **WebSocket `room.status.changed`** — TASK-002 genişlemesi; şimdilik endpoint'leri yazın, WebSocket dispatch kodu TASK-003 (Events)'de yapılabilir.
- **Fotoğraf upload** (traces, lost & found) — TASK-002 genişlemesi; şimdilik endpoint boş dönsün.
- **Özel fiyatlandırma / rate_plans** — TASK-002 genişlemesi; TASK-003 (Rezervasyon) ile birlikte; şimdilik room_types.base_rate kullanın.
- **Email/SMS** — TASK-002 genişlemesi; check-in/check-out event'leri emit edin, Celery gönderimi TASK-003'de yapılacak.

---

## İletişim & Destek

- Bu TASK tur 1'dir.
- Denetim sonrası feedback'i `/orchestrator/feedback/FB-00X.md` formatında gelen olacak.
- Sorularınız varsa veya bloke kaldıysanız, FB dosyasında belirtilecek.
- Her endpoint için test yazılması zorunlu (review.py `check_pytest` kırmızı ise tur 2 gider).

---

**Son güncelleme:** 2026-06-12 — TASK-002 spec oluşturuldu.


# TEKNİK TALİMATLAR (uyulacak)
# DeepSeek için Backend Geliştirme Talimatları

> **Amaç:** Bu döküman, AI-destekli Otel Yönetim Sistemi (PMS) için backend kodlamasının DeepSeek tarafından üretilmesi için yazılmıştır. Frontend Claude tarafından geliştirilecektir; backend ile sıkı sözleşme (contract) bu dökümanda tanımlıdır.

---

## 0. Genel Kurallar

1. **Dil/Çerçeve:** Python 3.11 + **FastAPI** (varsayılan tercih). Async/await zorunlu.
2. **ORM:** SQLAlchemy 2.0 (async) + Alembic (migration).
3. **Veri tabanı:** PostgreSQL 15+. Her tablo `id (UUID)`, `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` (soft delete) içermelidir.
4. **API standardı:** RESTful + JSON. URL versiyonlama: `/api/v1/...`. OpenAPI 3.1 otomatik üretilmeli.
5. **Auth:** JWT (access 15dk + refresh 7gün). RBAC roller: `superadmin`, `manager`, `frontdesk`, `housekeeping`, `accounting`, `maintenance`, `fb`, `hr`, `guest`.
6. **Audit log:** Tüm POST/PUT/PATCH/DELETE çağrıları `audit_log` tablosuna yazılmalı (kullanıcı, IP, eski/yeni değer, timestamp).
7. **Hata formatı:** `{ "error": { "code": "STRING_CODE", "message": "TR mesaj", "details": {...} } }` — HTTP status doğru kullanılmalı.
8. **Test:** Her endpoint için pytest + httpx ile en az 1 happy-path + 1 error-path testi.
9. **Cevap süresi hedefi:** p95 < 300ms. Ağır işler Celery + Redis ile arka plana atılmalı.
10. **Dokümantasyon:** Her endpoint için OpenAPI summary + description Türkçe + örnek payload zorunlu.
11. **Önemli:** Frontend ekran görüntüleri ile hata raporları gelecek. Her PR'da reproduce + fix + test eklenmeli.

---

## 1. Modül 1 — Ön Büro (Front Office)

### Veri Modeli (tablolar)
- `rooms` — id, room_no, room_type_id, floor, status (clean/dirty/inspected/out_of_order), connect_room_id
- `room_types` — id, code, name, base_rate, capacity, amenities (jsonb)
- `guests` — id, first_name, last_name, email, phone, nationality, id_type, id_no, dob, preferences (jsonb), tags
- `reservations` — id, code, guest_id, room_id?, room_type_id, check_in, check_out, adults, kids, rate_plan_id, status, source (direct/ota/walkin), total_amount, balance, special_requests
- `stays` — id, reservation_id, actual_check_in, actual_check_out, folio_id
- `traces` — id, reservation_id, department, message, resolved, due_date

### Endpoint'ler (örnek seçim)
```
POST   /api/v1/checkin/{reservation_id}
POST   /api/v1/checkout/{reservation_id}
GET    /api/v1/arrivals?date=YYYY-MM-DD
GET    /api/v1/departures?date=YYYY-MM-DD
GET    /api/v1/in-house?date=YYYY-MM-DD
GET    /api/v1/rooms?status=&type=&floor=
PATCH  /api/v1/rooms/{id}/status
POST   /api/v1/room-assign  (otomatik + manuel)
GET    /api/v1/guests/{id}/history
POST   /api/v1/traces
PATCH  /api/v1/traces/{id}/resolve
```

### AI Agent: FrontDesk AI
- `POST /api/v1/ai/frontdesk/welcome` — geçmiş konaklamalardan kişisel karşılama metni üretir.
- `POST /api/v1/ai/frontdesk/sentiment` — misafir mesajından negatif sentiment yakala → yönetici alarmı (WebSocket push).
- `POST /api/v1/ai/frontdesk/auto-assign` — oda atama önerisi (kat, tipo, geçmiş tercihler).
- `POST /api/v1/ai/frontdesk/room-ready-notify` — Housekeeping ile senkron, oda hazırsa misafire SMS/email.

### Self Check-in / EGM
- `POST /api/v1/self-checkin/start` — QR / mobil ile başlat.
- `POST /api/v1/self-checkin/passport-ocr` — pasaport fotoğrafından OCR.
- `POST /api/v1/egm/notify` — Emniyet Genel Müdürlüğü API'ye konaklama bildirimi (TC vatandaşları + yabancılar).

---

## 2. Modül 2 — Rezervasyon & Channel Manager

### Veri Modeli
- `rate_plans` — id, code, name, room_type_id, base_rate, restrictions (jsonb: min_los, cta, ctd, closed)
- `availability` — room_type_id, date, available_count, sold_count
- `channels` — id, name (booking_com, expedia, ...), credentials (şifreli), commission_rate, active
- `channel_mappings` — channel_id, room_type_id, channel_room_code
- `overbooking_rules` — room_type_id, max_overbook_pct
- `groups` — id, name, contact, block_size, cutoff_date

### Endpoint'ler
```
POST   /api/v1/reservations
PUT    /api/v1/reservations/{id}
GET    /api/v1/availability/calendar?from=&to=
POST   /api/v1/rate-plans
PATCH  /api/v1/rate-plans/{id}
POST   /api/v1/channels/{id}/sync
POST   /api/v1/booking-engine/quote   (otel web sitesi için fiyat sorgu)
POST   /api/v1/booking-engine/book
GET    /api/v1/occupancy?from=&to=    (takvim)
```

### AI Agent: RevenueIQ
- `POST /api/v1/ai/revenueiq/recommend-rate` — input: tarih aralığı, oda tipi. Output: önerilen fiyat + gerekçe (doluluk, mevsim, rakip, etkinlik).
- `GET  /api/v1/ai/revenueiq/forecast?horizon=90` — 90 günlük doluluk tahmini (ML modeli).
- `POST /api/v1/ai/revenueiq/channel-optimize` — kanal başına satış dağılımı önerisi.
- `GET  /api/v1/ai/revenueiq/alerts` — rezervasyon düşüşü tespit edildiğinde kampanya önerisi.

### Otomatik Akışlar (Celery beat)
- Yeni rez → tüm kanallar müsaitlik güncelle (event-driven, Kafka topic `availability.changed`)
- Rez sonrası onay e-postası
- Check-in'den 3 gün önce pre-arrival e-mail
- Check-in'den 1 gün önce hatırlatma SMS
- Post-stay feedback isteği (1 gün sonra)

### Channel Manager Entegrasyonları (Faz 2)
- Booking.com (XML), Expedia (EQC API), Agoda, Hotelbeds.
- Her kanalda: ARI push (availability/rate/inventory), reservation pull, mapping yönetimi.

---

## 3. Modül 3 — Groups & Events (MICE)

### Veri Modeli
- `events` — id, name, type, start, end, expected_pax, organizer_id, status
- `event_spaces` — id, name, capacity (theatre, classroom, banquet), amenities
- `event_bookings` — event_id, space_id, setup, rate
- `beo` (Banquet Event Order) — event_id, sections (food, av, room_block, billing), versions
- `event_quotes` — id, lead_id, items (jsonb), total, status
- `leads` — id, contact, source, status (new→qualified→won/lost)

### Endpoint'ler
```
POST   /api/v1/events
POST   /api/v1/events/{id}/beo
GET    /api/v1/events/{id}/beo/pdf       (PDF üret)
POST   /api/v1/events/quote
GET    /api/v1/event-spaces/availability?from=&to=
POST   /api/v1/events/{id}/run-of-show
POST   /api/v1/events/{id}/distribute    (dahili distribütör: mutfak, teknik, HK)
```

### AI Agent: EventIQ
- `POST /api/v1/ai/eventiq/proposal` — lead bilgisinden otomatik teklif (mekan + paket + fiyat).
- `POST /api/v1/ai/eventiq/upsell` — etkinlik süresince upsell fırsatı önerisi.
- `POST /api/v1/ai/eventiq/profitability` — etkinlik bazlı maliyet/kar analizi.
- `POST /api/v1/ai/eventiq/staffing` — etkinlik tarihinde gereken personel sayısı tahmini.

---

## 4. Modül 4 — Muhasebe & Cashiering

### Veri Modeli
- `folios` — id, reservation_id, guest_id, status (open/closed), total, balance
- `folio_items` — folio_id, type (room/fnb/extra/tax/adj), description, qty, unit_price, tax_rate, total, posted_at
- `payments` — id, folio_id, method (cash/card/transfer/vpos), amount, currency, ref, status
- `invoices` — id, folio_id, e_invoice_uuid, einvoice_status, pdf_url, xml_url
- `chart_of_accounts` — TÜRMOB uyumlu hesap planı
- `ledger_entries` — double-entry (debit/credit)
- `tax_rates` — KDV (%1, %8, %18, %20), turizm vergisi, stopaj

### Endpoint'ler
```
POST   /api/v1/folios/{id}/charge
POST   /api/v1/folios/{id}/payment
POST   /api/v1/folios/{id}/split        (folio bölme)
POST   /api/v1/folios/{id}/close
POST   /api/v1/night-audit/run          (kapanış)
GET    /api/v1/reports/revpar?from=&to=
GET    /api/v1/reports/adr
GET    /api/v1/reports/occupancy
GET    /api/v1/reports/gop
POST   /api/v1/einvoice/generate        (GİB e-Fatura)
POST   /api/v1/einvoice/cancel
GET    /api/v1/einvoice/{id}/status
```

### AI Agent: FinanceAI
- `POST /api/v1/ai/finance/anomaly-scan` — günlük olağandışı harcama / sahtekarlık tespiti.
- `POST /api/v1/ai/finance/night-audit` — anomali yoksa kapanışı otomatik yürütür.
- `GET  /api/v1/ai/finance/cost-analysis?period=weekly` — departman sapma raporu.
- `GET  /api/v1/ai/finance/budget-alert` — bütçe aşımı yaklaşıyorsa uyarı.

### Entegrasyonlar (Faz 2)
- **GİB e-Fatura & e-Arşiv** (XML UBL-TR formatı, özel entegratör).
- **Logo Tiger / Logo GO / SAP B1** muhasebe (API veya CSV).
- **Sanal POS:** iyzico, PayTR, Stripe (PCI-DSS scope dışı tutmak için tokenization).
- **TÜRMOB uyumlu hesap planı.**

---

## 5. Modül 5 — Housekeeping

### Veri Modeli
- `housekeeping_tasks` — id, room_id, assigned_to, type (checkout/stayover/inspection/deep), status, priority, started_at, completed_at
- `task_checklist` — task_id, item, checked, photo_url
- `lost_found` — id, room_id, found_by, item_description, photo, status, returned_to, returned_at
- `linen_inventory` — id, item, total, in_use, par_level, supplier_id
- `minibar_consumption` — room_id, item_id, qty, posted_to_folio

### Endpoint'ler
```
GET    /api/v1/housekeeping/board       (oda durumu paneli)
POST   /api/v1/housekeeping/tasks
PATCH  /api/v1/housekeeping/tasks/{id}/status
POST   /api/v1/housekeeping/tasks/{id}/photo
POST   /api/v1/lost-found
POST   /api/v1/minibar/post             (otomatik folio'ya tahakkuk)
POST   /api/v1/housekeeping/maintenance-request   (TechCare'e iş emri)
```

### AI Agent: CleanOps AI
- `POST /api/v1/ai/cleanops/schedule` — check-out zamanları + personel sayısına göre optimal temizlik sırası.
- `GET  /api/v1/ai/cleanops/supply-forecast` — temizlik malzeme tüketim tahmini → otomatik sipariş.
- `GET  /api/v1/ai/cleanops/staff-performance` — temizlik süresi + kalite skoru rapor.
- `POST /api/v1/ai/cleanops/predictive-maintenance` — oda arıza geçmişinden önleyici bakım önerisi.

### Mobil Uygulama API'si (Kat Görevlisi)
- WebSocket `/ws/housekeeping/{user_id}` — anlık görev push.
- Offline-first: çakışma çözümleme (last-write-wins veya CRDT).
- Push notification (FCM / APNs).

---

## 6. Modül 6 — Bakım & Teknik Servis

### Veri Modeli
- `work_orders` — id, room_id?, area, category (electric/plumb/hvac/it), priority, status, sla_due, assigned_to
- `equipment` — id, name, location, install_date, warranty_until, last_maintenance
- `maintenance_schedule` — equipment_id, frequency, next_due
- `energy_readings` — area, kwh, timestamp (IoT'tan)

### Endpoint'ler
```
POST   /api/v1/work-orders
PATCH  /api/v1/work-orders/{id}/assign
PATCH  /api/v1/work-orders/{id}/resolve
GET    /api/v1/work-orders/sla-breach
POST   /api/v1/equipment
GET    /api/v1/equipment/{id}/history
GET    /api/v1/preventive/upcoming
```

### AI Agent: TechCare AI
- `POST /api/v1/ai/techcare/prioritize` — misafir etkisine göre iş emri önceliklendirme.
- `GET  /api/v1/ai/techcare/preventive-recommendations`
- `POST /api/v1/ai/techcare/energy-anomaly` — anormal enerji tüketimi tespiti.

---

## 7. Modül 7 — F&B (DIŞ FİRMA Entegrasyonu)

Restoran POS, KDS, stok dış firma. Bizim sorumluluğumuz **entegrasyon** + **AI overlay**.

### Endpoint'ler (entegrasyon)
```
POST   /api/v1/fb/room-charge           (dış POS check'ini odaya yaz)
GET    /api/v1/fb/orders?from=&to=
POST   /api/v1/fb/reservations          (restoran rez — online + dahili)
POST   /api/v1/integrations/fb/sync     (cron job)
```

### AI Agent: ChefIQ
- `POST /api/v1/ai/chefiq/menu-optimize` — kar marjı + popülerlik analizi.
- `GET  /api/v1/ai/chefiq/waste-analysis`
- `POST /api/v1/ai/chefiq/prep-forecast` — etkinlik + doluluk verisiyle mutfak hazırlık planı.

---

## 8. Modül 8 — Misafir Deneyimi & CRM

### Veri Modeli
- `guest_profiles_360` — birleşik view (geçmiş konaklamalar, harcama, tercihler, alerjiler, şikayetler)
- `loyalty_accounts` — guest_id, tier (silver/gold/platinum), points, lifetime_value
- `feedback` — id, reservation_id, channel (post-stay/tripadvisor/booking), rating, sentiment, text
- `complaints` — id, guest_id, category, severity, status (new→assigned→resolved), resolution_notes

### Endpoint'ler
```
GET    /api/v1/guests/{id}/360
POST   /api/v1/loyalty/earn
POST   /api/v1/loyalty/redeem
POST   /api/v1/feedback/survey/send
POST   /api/v1/feedback/webhook         (TripAdvisor/Booking review webhook)
POST   /api/v1/complaints
PATCH  /api/v1/complaints/{id}/assign
```

### AI Agent: GuestAI (Chatbot — WhatsApp Business)
- `POST /api/v1/ai/guestai/chat` — WhatsApp/web chat handler.
- `POST /api/v1/ai/guestai/personalize` — kişiselleştirilmiş paket önerisi.
- `POST /api/v1/ai/guestai/review-respond` — Google/Booking yorumlarına öncelikli yanıt önerisi.

### Entegrasyonlar
- WhatsApp Business API (Cloud API).
- SMS (Twilio veya yerel sağlayıcı).
- SMTP transactional (SendGrid / Amazon SES).

---

## 9. Modül 9 — Güvenlik & Erişim Kontrol

### Veri Modeli
- `keycards` — id, type (guest/staff), holder_id, room_id?, valid_from, valid_to, encrypted_token
- `access_logs` — id, keycard_id, door_id, granted/denied, timestamp
- `visitors` — id, name, id_no, host_guest_id?, in_at, out_at
- `alarms` — id, type (fire/security/iot), source, status, acknowledged_by
- `kvkk_consents` — guest_id, scope, granted, granted_at, withdrawn_at
- `data_deletion_requests` — guest_id, requested_at, executed_at

### Endpoint'ler
```
POST   /api/v1/keycards/issue
POST   /api/v1/keycards/revoke
GET    /api/v1/access-logs?room=&from=&to=
POST   /api/v1/visitors/checkin
POST   /api/v1/alarms/acknowledge
POST   /api/v1/kvkk/consent
POST   /api/v1/kvkk/erase             (silme talebi)
GET    /api/v1/kvkk/export            (taşınabilirlik — JSON paketi)
```

### AI Agent: SecureAI
- `GET /api/v1/ai/secure/anomaly` — olağandışı giriş saati / başarısız deneme alarmı.
- `GET /api/v1/ai/secure/daily-brief` — günlük güvenlik özeti e-postası.

---

## 10. Modül 10 — Revenue Management & Raporlama

### Veri Modeli
- `reports_kpis` — tarih + saatlik OLAP cube (materialized view'lar)
- `custom_reports` — id, name, owner, definition (jsonb), schedule
- `user_activity_log` — user_id, action, entity, entity_id, payload_diff (jsonb), ip, ua, timestamp

### Endpoint'ler
```
GET    /api/v1/dashboard/manager        (Yönetici Dashboard)
GET    /api/v1/reports/std/str
GET    /api/v1/reports/std/occupancy
GET    /api/v1/reports/std/revpar
GET    /api/v1/reports/std/adr
GET    /api/v1/reports/std/gop
GET    /api/v1/reports/std/arrivals
GET    /api/v1/reports/std/departures
GET    /api/v1/reports/std/cashiering
GET    /api/v1/reports/std/housekeeping
GET    /api/v1/reports/std/manager-flash
POST   /api/v1/reports/custom           (sürükle-bırak özel rapor)
GET    /api/v1/budget/variance?period=
GET    /api/v1/audit/user-activity?user=&from=  (User Activity Log — zorunlu!)
```

### AI Agent: InsightAI
- `POST /api/v1/ai/insight/daily-brief` — her sabah tüm departmanlara otomatik e-posta.
- `POST /api/v1/ai/insight/competitor-scan` — rakip fiyat analizi (Rate Shopping API).

---

## 11. AI Agent Ortak Altyapı

```
core/agents/
  __init__.py
  base.py            # Agent base class (input/output schema)
  registry.py        # Agent kayıt + discovery
  frontdesk.py
  revenueiq.py
  finance.py
  cleanops.py
  techcare.py
  chefiq.py
  shiftai.py
  guestai.py
  secureai.py
  insight.py
  eventiq.py
core/llm/
  client.py          # LLM provider abstraction (OpenAI/Claude/DeepSeek)
  prompts/           # Sistem promptları (versiyonlu)
core/tools/
  db.py              # Agent'ların kullanacağı güvenli SQL erişim
  http.py            # Dış API erişim (whitelist)
```

**Önemli ilkeler:**
- Tüm AI çağrıları `ai_invocations` tablosunda loglanmalı (token sayısı, maliyet, latency).
- Sistem promptları versiyonlu, evals klasöründe test koşulu.
- Misafir verisi LLM'e gönderilirken PII maskeleme katmanı (KVKK).
- Rate limit per-tenant.

---

## 12. Dış Entegrasyonlar Katmanı

| Kategori | Sağlayıcılar |
|---|---|
| Ödeme | Sanal POS (iyzico, PayTR, Stripe) |
| Vergi/Muhasebe | GİB e-Fatura, Logo GO, SAP |
| OTA/GDS | Booking.com, Expedia, Sabre/Amadeus (Faz 3) |
| İletişim | WhatsApp Business API, SMS sağlayıcı, SMTP |
| Akıllı Oda (IoT) | Nest, KNX, Philips Hue |
| Check-in | Self-service kiosk, pasaport okuyucu (MRZ) |
| ERP | Logo Tiger, SAP, Microsoft Dynamics |
| Müzik/Eğlence | IPTV, Spotify for Business |
| F&B | Dış restoran POS (Adisyo, Simpra vs.) |
| Stok | Dış stok programı |

Her entegrasyon için:
- `integrations/{provider}/` modülü
- Retry + circuit breaker (tenacity)
- Webhook receiver endpoint
- Health-check `/api/v1/integrations/{provider}/health`

---

## 13. Güvenlik Gereksinimleri (Zorunlu)

- SOC 2 Type II uyumlu mimari (loglar 1 yıl, MFA, change mgmt).
- PCI-DSS scope minimize (kart verisi token, sanal POS taraflı tokenization).
- KVKK/GDPR: rıza yönetimi, silme/taşınabilirlik endpoint'leri, veri envanter.
- RBAC + ABAC (departman bazlı satır filtreleme).
- AES-256-GCM at-rest, TLS 1.3 in-transit.
- Audit log immutable (append-only).
- Secret yönetimi: Vault veya AWS Secrets Manager.

---

## 14. DeepSeek için İş Akışı

Her modül için aşağıdaki adımları izleyin:

1. **Şema:** Alembic migration üret + ER diagram (mermaid) ekle.
2. **Model:** SQLAlchemy modelleri + Pydantic v2 schemas (request/response ayrı).
3. **Servis:** İş mantığı `services/` altında. Endpoint'te iş mantığı YOK.
4. **Endpoint:** FastAPI router. Bağımlılıklar `Depends()` ile (auth, db, current_user).
5. **Test:** `tests/test_{modül}.py` — pytest fixture + httpx async client.
6. **Doküman:** OpenAPI summary/description Türkçe + örnek payload.
7. **AI Agent (varsa):** `core/agents/{name}.py` — base class'tan türet.
8. **PR:** Tek modül = tek PR. Açıklamada her endpoint için örnek `curl` ver.

---

## 15. Frontend'in Beklediği API Sözleşmesi

Frontend (Claude) tüm liste endpoint'lerinde aşağıdaki ortak şemayı bekler:

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 234,
    "total_pages": 5
  }
}
```

Filtreler her zaman query param: `?q=&status=&from=&to=&page=&per_page=&sort=`.
WebSocket eventleri kanal bazlı: `room.status.changed`, `reservation.created`, `task.assigned`, vb.

---

## 16. Hata Düzeltme Döngüsü

Frontend (Claude) her modülün UI'sını gerçek API'ye bağladıktan sonra ekran görüntüsü ile test eder. Bulunan hatalar şu formatta DeepSeek'e iletilir:

```
[BUG] Modül: Front Office / Check-in
Reproduce: POST /api/v1/checkin/123 → 500
Beklenen: 200, folio oluşur
Gerçekleşen: NullPointerException (folio_id null)
Screenshot: docs/bugs/2026-06-10-checkin-500.png
```

DeepSeek bu bug raporlarını öncelikli olarak ele alıp:
1. Reproduce eden test ekler.
2. Düzeltir.
3. PR'da "Closes [BUG-id]" ile referans verir.

---

## 17. Çıktılar (Faz 1 sonu için DeepSeek'ten beklenenler)

- [ ] PostgreSQL şeması + migration'lar
- [ ] Auth + RBAC + audit altyapısı
- [ ] Modül 1 (Ön Büro) tüm endpoint'leri + testler
- [ ] Modül 2 (Rezervasyon direkt) tüm endpoint'leri + testler
- [ ] Modül 4 (Cashiering temel) endpoint'leri + testler
- [ ] Modül 5 (Housekeeping temel) endpoint'leri + testler
- [ ] FrontDesk AI temel uçları
- [ ] OpenAPI spec yayını + Postman koleksiyonu
- [ ] Docker compose ile yerel ayağa kalkma (`docker compose up`)
- [ ] Seed data script'i (10 oda + 5 misafir + 3 rezervasyon)
