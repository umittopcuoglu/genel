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
id: TASK-006
modül: Altyapı & DevOps (WebSocket + E2E + Docker + CI/CD)
kapsam: WebSocket real-time + Playwright E2E + prod Docker Compose + GitHub Actions
durum: kuyrukta (TASK-003 ile paralel gönderilebilir)
tur: —
bağımlılık: TASK-002 (front_office router'daki WebSocket TODO'ları)
---

# TASK-006 — Altyapı & DevOps

> Bu görev modül değil; tüm modülleri ayakta tutan altyapı. WebSocket gerçek-zamanlı
> güncellemeler, uçtan uca testler, prod-hazır konteynerleme ve sürekli entegrasyon.
> Mevcut: `backend/Dockerfile`, `backend/docker-compose.yml` (db+redis+api),
> `.github/workflows/{backend-ci,frontend-ci,nightly-qa}.yml`. Bunları GENİŞLET, bozma.

---

## 1. WebSocket Gerçek-Zamanlı Altyapı

### 1.1 Bağlantı yöneticisi — `backend/app/ws/manager.py`
- `ConnectionManager` sınıfı: aktif WebSocket bağlantılarını yönetir
  - `connect(websocket, user_id, role)` — bağlantıyı kaydet
  - `disconnect(websocket)` — bağlantıyı kaldır
  - `broadcast(event: dict)` — tüm bağlı istemcilere yayınla
  - `broadcast_to_roles(event, roles: list)` — belirli rollere yayınla (örn. sadece housekeeping)
- Redis Pub/Sub ile çoklu worker desteği (uvicorn --workers N): bir worker'da emit edilen olay
  Redis kanalı `hotelops:events` üzerinden diğer worker'lara dağıtılır.

### 1.2 WebSocket endpoint — `backend/app/ws/routes.py`
- `WS /api/v1/ws?token=JWT` — JWT query param ile auth (header WS'te zor)
  - Token geçersiz → 1008 policy violation ile kapat
  - Bağlantı sonrası `{"type": "connected", "user_id": "..."}` gönder
- `WS /api/v1/ws/housekeeping?token=JWT` — sadece housekeeping/manager rolü; oda görev push'u

### 1.3 Olay yayıncısı — `backend/app/ws/events.py`
- `emit_room_status_changed(room_id, room_no, old_status, new_status)` →
  `{"type": "room.status.changed", "data": {...}, "ts": "ISO"}`
- `emit_reservation_created(reservation)` → `{"type": "reservation.created", ...}`
- `emit_checkin(reservation_id, room_no)` / `emit_checkout(...)`
- `emit_housekeeping_task(task)` → housekeeping rolüne push

### 1.4 Mevcut endpoint'lere entegrasyon (TASK-002 revizyonu — TAM dosya gönder)
- `front_office.py`: check-in/check-out/room-status-patch sonrası ilgili `emit_*` çağrısı
- TODO yorumları gerçek emit çağrılarıyla değiştirilir

### 1.5 Testler — `backend/tests/test_ws.py`
- WS bağlantı + auth happy (geçerli token bağlanır)
- Geçersiz token → kapanış (1008)
- room.status.changed emit → bağlı istemci olayı alır (httpx/websockets test client)
- RBAC: housekeeping WS'e guest rolü bağlanamaz

---

## 2. Playwright E2E Testleri (docs/04 Doğrulama Döngüsü)

### 2.1 Kurulum — `qa/e2e/`
```
qa/e2e/
├── playwright.config.ts      # baseURL, 4 proje: chromium-light, chromium-dark, mobile-light, mobile-dark
├── package.json              # @playwright/test
├── fixtures/auth.ts          # login helper (token localStorage'a yazar)
├── tests/
│   ├── login.spec.ts
│   ├── front-office.spec.ts  # arrivals/departures/in-house/rooms/tape-chart sekmeleri
│   └── smoke.spec.ts         # her ana sayfa 200 + ekran görüntüsü
└── screenshots/              # baseline görseller (4 varyant)
```

### 2.2 Test senaryoları
- **login.spec.ts:** geçersiz parola hata gösterir; geçerli giriş dashboard'a yönlendirir
- **front-office.spec.ts:**
  - 5 sekme (Gelenler/Gidenler/Konaklayanlar/Oda Panosu/Tape Chart) tıklanır, içerik render olur
  - Oda Panosu filtre butonları çalışır (temiz/kirli/dolu)
  - Tape Chart hafta kaydırma (← 7 gün / 7 gün →) çalışır
  - Her sekmede `toHaveScreenshot()` baseline karşılaştırması
- **smoke.spec.ts:** /dashboard, /front-office sayfaları yüklenir, console error yok
- **Erişilebilirlik:** her testte `@axe-core/playwright` ile a11y taraması (kritik ihlal = fail)

### 2.3 Mock backend modu
- Backend ayakta değilse: Playwright `route.fulfill()` ile API yanıtlarını mock'lar
- `fixtures/mock-api.ts`: arrivals/departures/rooms için sabit JSON döndürür
- Böylece E2E backend olmadan da CI'da koşar (görsel regresyon için yeterli)

---

## 3. Prod-Hazır Docker Compose

### 3.1 Frontend Dockerfile — `frontend/Dockerfile`
- Multi-stage: `node:20-alpine` build → `next build` → standalone output
- Runtime: minimal image, `next start` veya standalone server, port 3000
- `.dockerignore`: node_modules, .next, .git

### 3.2 Prod compose — `docker-compose.prod.yml` (hotel/ kökünde)
- Servisler: `db` (postgres:15), `redis`, `api` (backend), `web` (frontend), `nginx` (reverse proxy)
- `api`: --workers 4, --reload YOK, env_file ile secrets
- `web`: NEXT_PUBLIC_API_URL=http://api:8000, build frontend/
- `nginx`: 80/443 → web (/, statik) + api (/api, /api/v1/ws WebSocket upgrade header'ları)
  - `nginx/default.conf`: `proxy_set_header Upgrade $http_upgrade; Connection "upgrade"` (WS için)
- Healthcheck'ler + `restart: unless-stopped`
- Named volumes: postgres_data, redis_data

### 3.3 Env şablonu — `hotel/.env.prod.example`
- DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET, CORS_ORIGINS
- Yorum: "production'da gerçek secret'larla doldur, asla commit etme"

---

## 4. GitHub Actions CI/CD Genişletme

### 4.1 `e2e-ci.yml` (YENİ)
- Trigger: frontend/ veya qa/e2e/ değişiminde
- `npm ci` + `npx playwright install --with-deps chromium`
- `next build` + `next start` arka planda → Playwright koş (mock API modu)
- Görsel regresyon başarısızsa diff'leri artifact olarak yükle

### 4.2 `docker-ci.yml` (YENİ)
- Trigger: Dockerfile veya docker-compose değişiminde
- `docker compose -f docker-compose.prod.yml build` (smoke: image'lar derleniyor mu)
- `docker compose up -d` + `curl http://localhost/api/v1/health` → 200 beklenir, sonra `down`

### 4.3 `backend-ci.yml` (GENİŞLET — TAM dosya gönder)
- PostgreSQL service container ekle (gerçek DB ile entegrasyon testi)
- `alembic upgrade head` migration testi
- WebSocket testleri (`test_ws.py`) dahil

### 4.4 Branch koruması notu
- README'ye not: main branch'e merge için tüm CI yeşil olmalı (kullanıcı GitHub Settings'ten ayarlar)

---

## 5. Teslim dosyaları
```
### FILE: backend/app/ws/__init__.py
### FILE: backend/app/ws/manager.py
### FILE: backend/app/ws/routes.py
### FILE: backend/app/ws/events.py
### FILE: backend/app/routers/front_office.py     (WS emit entegrasyonu — TAM dosya)
### FILE: backend/app/main.py                      (WS router + Redis pubsub başlatma — TAM dosya)
### FILE: backend/tests/test_ws.py
### FILE: frontend/Dockerfile
### FILE: frontend/.dockerignore
### FILE: hotel/docker-compose.prod.yml
### FILE: hotel/nginx/default.conf
### FILE: hotel/.env.prod.example
### FILE: qa/e2e/package.json
### FILE: qa/e2e/playwright.config.ts
### FILE: qa/e2e/fixtures/auth.ts
### FILE: qa/e2e/fixtures/mock-api.ts
### FILE: qa/e2e/tests/login.spec.ts
### FILE: qa/e2e/tests/front-office.spec.ts
### FILE: qa/e2e/tests/smoke.spec.ts
### FILE: .github/workflows/e2e-ci.yml
### FILE: .github/workflows/docker-ci.yml
### FILE: .github/workflows/backend-ci.yml          (PostgreSQL + alembic + WS — TAM dosya)
```

> NOT: `.github/workflows/` repo kökündedir (hotel/ değil). Yollar buna göre.
> `qa/e2e/` Claude'un alanıdır ama bu altyapı görevinde DeepSeek yazabilir — istisna onaylandı.

## 6. Kabul kriterleri
- `backend/tests/test_ws.py` yeşil (WS bağlantı + auth + emit + RBAC)
- `front_office.py` artık gerçek `emit_*` çağrıları içerir (TODO kalmamış)
- `docker compose -f docker-compose.prod.yml build` hatasız (5 servis)
- `nginx/default.conf` WebSocket upgrade header'ları içerir
- Playwright config 4 proje (light/dark × desktop/mobile) tanımlar
- 3 yeni workflow geçerli YAML; mevcut 3 workflow bozulmamış
- review.py PASS (model/audit/hata-formatı/qa-dokunulmazlığı uyarısı kabul)
- OpenAPI Türkçe (WS endpoint'leri için açıklama)


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
