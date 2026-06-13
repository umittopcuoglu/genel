# HotelOps PMS — Sürüm Notları

Bu dosya teslim edilen sürümleri ve oturum bazlı önemli değişiklikleri kaydeder.

---

## v1.0.1 — "Birleştirme sonrası tamamlama + QA" (2026-06-13)

Birleştirme sonrası boşlukların kapatılması, FrontDesk AI eklenmesi ve görsel QA.

### Genel durum
- **Backend:** 356 test yeşil (350 → +6 FrontDesk AI), 0 hata
- **Frontend:** 33 route · 30/30 sayfa görsel QA'dan geçti
- **Migration:** tek head `022` (çoklu-head onarıldı)

### Değişiklikler
- **Alembic migration onarımı:** çoklu-head (`013`+`021`) tek zincire bağlandı
  (`014_add_hr` → `013` relink); birleştirme kolunun migration'sız 7 tablosu için
  **migration 022** eklendi (`payment_transactions`, `crm_*`, `guest_wifi_sessions`,
  `integration_settings`) — upgrade+downgrade SQLite'ta doğrulandı.
- **FrontDesk AI (temel)** ajanı: `POST /ai/frontdesk/checkin-assist` (karşılama +
  oda/upgrade önerisi + upsell + öncelik), 6 test. Registry artık 9 ajan.
- **TASK-006 doğrulandı:** WebSocket (`app/ws/`), E2E (`qa/e2e/`), Docker, 8 CI
  workflow zaten mevcuttu — PROJECT_STATUS güncellendi.
- **Görsel QA (Playwright):** `qa/e2e/tests/screenshots.spec.ts` — 30 rotanın tamamı
  için fullPage ekran görüntüsü + sağlık testi. 30/30 sayfa render oldu.
  - Bulgu 1: 27 app sayfasında kurtarılabilir hydration uyarısı (i18n SSR↔CSR dil farkı; kozmetik).
  - Bulgu 2: `payments` + `insights` backend kapalıyken yakalanmamış `fetch` hatası
    (ham fetch; operasyon kolu `useApiData` ile zarif fallback yapıyor). Sayfa yine render oluyor.

### Açık (opsiyonel)
- D2: Bounded context fiziksel taşıma (riskli/opsiyonel — diğer kol ertelemişti)
- Hydration uyarıları ve payments/insights fetch yakalama (kozmetik iyileştirme)

---

## v1.0.0 — "Birleştirme" (2026-06-13)

İlk tam fonksiyonel sürüm. Proje **iki paralel Claude oturumunda** inşa edildi ve bu
sürümde tek koda birleştirildi.

### Genel durum
- **Backend:** 350 test yeşil (0 hata)
- **Frontend:** 33 route temiz derleniyor (`npm run build`)
- **TypeScript:** `tsc --noEmit` temiz
- **Faz:** 1–4 tamamlandı

### Birleştirme (merge) — iki geliştirme kolu

**Operasyon kolu** (`ecstatic-gates`):
- Ön Büro, Rezervasyon & Müsaitlik, Muhasebe & Cashiering, Housekeeping
- Gruplar & Etkinlikler (MICE) + EventIQ AI
- Bakım & Teknik Servis + TechCare AI
- F&B & POS + ChefIQ AI
- Güvenlik & Erişim & KVKK + SecureAI
- HR & Vardiya + ShiftAI
- GDS Entegrasyonu (Amadeus/Sabre/Travelport)
- IoT / Akıllı Oda (Nest/KNX/Hue)
- Computer Vision (Oda Kalite Kontrol), Sesli Kontrol (Alexa/Google)
- Multi-Property (Otel Zinciri), Mobil Check-in (OCR + EGM), Blockchain Kimlik
- Analitik Dashboard (occupancy/revenue trend + source-mix)
- Misafir Wi-Fi Portal
- Tüm frontend i18n (TR/EN) + canlı API wiring (mock fallback + MockBanner)

**İş/Finans kolu** (`wonderful-gates`):
- Payment Gateway (iyzico / PayTR / Stripe / Craftgate — parametrik provider)
- GİB e-Fatura (Foriba / İzibiz / Logo / Uyumsoft connector'ları)
- CRM & Misafir 360 & Segment & Kampanya
- Revenue Management / RevenueIQ
- WhatsApp Business API (Meta Cloud)
- InsightAI (KPI özeti + kanal mix + aksiyon önerileri)
- OTA Connector'lar (Booking / Expedia / Agoda)
- **EventBus / Modular Monolith** mimarisi (5 bounded context)
- Rate limiting, AI audit/cost tracking, observability, CI/CD pipeline

### Çakışma çözümleri (merge)
- **F&B + Güvenlik/KVKK** (her iki kol farklı yazmıştı): daha kapsamlı operasyon-kolu
  implementasyonu korundu
- **`main.py`**: tüm router'lar birleştirildi; `currency` + `guest_wifi` geri eklendi,
  `initialize_agents()` lifespan'e eklendi
- **`models/__init__.py`**: `payment_transaction` + `crm` modelleri eklendi; fnb/security
  class isimleri operasyon koluna göre düzeltildi
- **`conftest.py`**: session-scoped init + per-test temizlik fixture'ı korundu
- **4 AI ajanı** (EventIQ/TechCare/ChefIQ/SecureAI) yeni `BaseAgent._run` sözleşmesine
  uyarlandı (`execute` → `_run`)
- **Sidebar + i18n**: 6 yeni sayfa (payments/crm/whatsapp/einvoice/revenue/insights)
  navigasyona ve TR/EN çevirilere eklendi

### Altyapı (TASK-006 — doğrulandı, mevcut)
- WebSocket (`app/ws/`), E2E testleri (`qa/e2e/` Playwright)
- Docker (`Dockerfile` + `docker-compose.{yml,prod.yml}`)
- CI/CD: 8 GitHub Actions workflow (backend/frontend/docker/e2e/full-stack/nightly-qa/pre-commit)

### Bilinen sınırlamalar
- Dış servisler (POS, GDS, IoT, kapı kilidi, ödeme, e-Fatura, WhatsApp) **mock-first**;
  gerçek anahtarlar `.env`'den girilince canlıya geçer
- `api.deepseek.com` cloud ortam allowlist'inde kapalı → AI görevleri manuel/mock modda
