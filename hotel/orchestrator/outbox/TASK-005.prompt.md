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
