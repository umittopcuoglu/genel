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
