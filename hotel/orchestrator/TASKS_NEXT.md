# HotelOps — Devam Görev Listesi

**Branch:** `claude/wonderful-gates-cahvpv`
**Son commit:** `67c23e0` — Modular Monolith refactor (EventBus + Connector pattern)
**Test durumu:** 306 test (294 önceki + 12 architecture); arch tested lokal yeşil, tam regresyon CI'da koşacak.

> Devralan oturum: önce `git pull origin claude/wonderful-gates-cahvpv` ve
> tam regresyon (`cd hotel/backend && rm -f test.db && pytest tests/`)
> çalıştırarak başla. Yeşil değilse buradaki sıraya geçme — önce kırığı onar.

---

## A. Acil Doğrulama (önkoşul)

- [ ] **A1. Tam pytest regresyon** — hedef: 306 yeşil. Kırılırsa `test_architecture.py`
      ve `channel_sync_service` değişikliklerine bak. Önce bunu doğrula, sonra ilerle.
- [ ] **A2. Frontend production build** — `cd hotel/frontend && npm run build`.
      Sidebar'a son eklenen `/payments /crm /whatsapp /einvoice /revenue /insights`
      linkleri için bazı ekranlar mock (einvoice, revenue) — eksik sayfaları
      `/insights` patern'ine göre ekle.

---

## B. EventBus Yayılımı (mimari kompletasyon)

Şu an sadece `reservations.create` event yayınlıyor. Mimarinin tam değerini almak için:

- [ ] **B1. CheckIn / CheckOut event yayını**
  - `routers/front_office.py` içinde check-in ve check-out aksiyonlarına
    `CheckInCompleted` / `CheckOutCompleted` publish ekle.
  - Beklenen abone: housekeeping (oda durumu), CRM (teşekkür mesajı), revenue (recompute).
- [ ] **B2. Payment success event**
  - `services/payment_service.py::charge` başarılı dönerse `PaymentSucceeded` yayınla.
  - Abone: folio bakiye güncellemesi, audit log.
- [ ] **B3. ReservationCancelled event**
  - Cancel endpoint'ten event publish + channel sync cancel push handler'ı.
- [ ] **B4. EventBus → Channel Sync handler**
  - Şu an `reservations.py` HEM `ChannelSyncService.push_inventory_update` çağırıyor
    HEM `ReservationCreated` yayınlıyor (geçiş için duplicate).
  - `event_handlers.py`'a `channel_sync_on_reservation` ekle (subscribe ReservationCreated)
    ve sync çağrıyı router'dan kaldır → temiz gevşek bağ.
- [ ] **B5. Bus testleri**
  - Yukarıdaki her event için `test_architecture.py` patern'i ile yeni testler.

---

## C. Connector Pattern Genişletme

- [ ] **C1. Real-OTA connector iskeleti**
  - Booking için XML push gerçek payload'ları (sözleşme bağlanınca enable edilecek).
  - Expedia EQC ARI message + reservation pull endpoint'leri.
  - Şu an mock — connector içinde `if params.endpoint_url: httpx.post(...)` patern'i.
- [ ] **C2. Payment provider connector refactor**
  - `payment_service.py` içindeki provider switch'i `payment_connectors/`
    altına çıkar: `IyzicoConnector`, `StripeConnector`, `PayTRConnector`, `CraftgateConnector`.
- [ ] **C3. e-Fatura entegratör connector**
  - `einvoice_service.py` → `einvoice_connectors/{foriba,logo,uyumsoft,izibiz}.py`.
  - `ForibaConnector.submit(xml)` her biri için ayrı dosya, base ABC.
- [ ] **C4. Connector marketplace endpoint**
  - `GET /api/v1/connectors` → `{available: [booking, expedia, agoda, iyzico, ...]}`.
  - Frontend "Entegrasyon Ayarları" sayfasında "Plugin Marketplace" sekmesi.

---

## D. Bounded Context Hard Boundary

Şu an dokümantasyon var ama linter yok. Sınırları forceleyelim:

- [ ] **D1. import-linter contract**
  - `pyproject.toml`'a `[tool.importlinter]` ekle.
  - Kontratlar: `pms_core` `distribution`'ı import edemez; `guest_experience`
    `revenue`'yu import edemez; cross-context yalnızca `app.core.events` üzerinden.
  - CI'a `lint-imports` adımı.
- [ ] **D2. Fiziksel taşıma (opsiyonel, riskli)**
  - `app/contexts/{pms_core,distribution,guest_experience,revenue,integration_hub}/`
    klasörlerini oluştur, mevcut router/service/model'leri taşı.
  - **Risk:** 294 testin import path'leri kırılır → çok küçük adımlarla yap,
    her taşımadan sonra regresyon.
  - Alternatif: taşıma yerine `__init__.py` re-export'larıyla "façade" oluştur.

---

## E. Frontend Eksik Ekranlar

- [ ] **E1. `/einvoice` ekranı** — fatura oluştur, listele, gönder, iptal, XML görüntüle.
- [ ] **E2. `/revenue` ekranı** — forecast formu + öneri tablosu + approve/reject butonları.
- [ ] **E3. `/security` (KVKK) ekranı** — consent grant/revoke, DSR talepleri kanban.
- [ ] **E4. `/fnb` backend bağlama** — şu an mock; outlet/menu/check listeleri gerçek API'ye bağlansın.
- [ ] **E5. Guest 360 detay sayfası** — `/crm/guests/[id]` rota; tüm KPI + notes + communications.

---

## F. Production Hardening

- [ ] **F1. Pydantic v2 deprecation warning'leri** (Field `env`, class-based Config)
  → ConfigDict + json_schema_extra'ya migrate.
- [ ] **F2. pytest-asyncio event_loop deprecation** — conftest.py:46'daki
  custom `event_loop` fixture'ı `asyncio_mode` ile değiştir.
- [ ] **F3. Audit middleware "no such table: audit_logs"** —
  test ortamında migrate çalıştır veya middleware'i bypass et.
- [ ] **F4. Rate limiting** — auth endpoint'lerine `slowapi` ile rate limit.
- [ ] **F5. PostgreSQL geçişi** — testlerin SQLite'a bağımlılığını gözden geçir
  (jsonb, array tipi farklılıkları).

---

## G. AI Layer (Otelio diferansiyatörü)

- [ ] **G1. LLM agent base class** — `app/services/ai/agent_base.py`:
  Anthropic Claude / DeepSeek provider-agnostik wrapper, tool-use, streaming.
- [ ] **G2. RevenueIQ AI** — `revenue_service.recommend_rate` şu an rule-based;
  LLM ile rakip fiyat analizi + sezonsal trend yorumu ekle.
- [ ] **G3. GuestAI Chatbot** — `whatsapp_service._bot_reply` kural-tabanlı;
  LLM (Claude Haiku 4.5 önerili — hızlı, ucuz) ile değiştir.
  Context: guest 360 + son rezervasyon + KVKK consent kontrolü.
- [ ] **G4. InsightAI doğal dil özeti** — `/api/v1/insights/narrative` endpoint:
  KPI özeti LLM ile 2-3 paragraflık aksiyon önerisine dönsün.
- [ ] **G5. AI Audit + cost tracking** — `ai_invocation` modeli var ama
  doldurulmuyor; her LLM çağrısında tokens/cost/latency yaz.

---

## H. DevOps / Operasyon

- [ ] **H1. Alembic migration'lar** — şu an `create_all` kullanılıyor (init_db.py);
  Faz 2-4 yeni tablolar için `alembic revision --autogenerate` ile baseline.
- [ ] **H2. Docker imajı production-ready** — multi-stage build (frontend assets
  api'ye dahil), non-root user, health check.
- [ ] **H3. Observability** — OpenTelemetry tracer, Prometheus metrics endpoint,
  structured logging (JSON).
- [ ] **H4. Backup stratejisi** — pg_dump cron + S3 upload + 30 gün retention.
- [ ] **H5. Blue-green deploy plan** — `nginx/` zaten var; CI sonrası canary slot.

---

## Öncelik Önerisi (devralan için)

```
P0 (önce): A1, A2, B4 — mimari değişikliğin tutarlılığını sağla
P1 (sonra): B1-B3, C2-C3 — EventBus + Connector tam genişleme
P2: D1, E1-E3, G3 — sınır enforcement + eksik UI + GuestAI
P3: G1-G2-G4, F1-F5, H1-H5 — AI layer + production hardening
```

## Repo / Branch Detayları

- **Repo:** `umittopcuoglu/genel`
- **Branch:** `claude/wonderful-gates-cahvpv` (her commit buraya push edildi)
- **Mevcut testler:** 306 (önceki 294 + 12 architecture)
- **Eklenen 9 görev:** Payment, CRM, WhatsApp, e-Fatura, Revenue, F&B, Security/KVKK,
  InsightAI, CI/CD — `PROJECT_STATUS.md`'de detay.
- **Mimari refactor:** EventBus + Connector pattern + 5 bounded context — `docs/ARCHITECTURE.md`.

## Önemli Dosyalar (devralan referans noktası)

| Konu | Dosya |
|------|-------|
| EventBus | `hotel/backend/app/core/events.py` |
| Event abonelikleri | `hotel/backend/app/core/event_handlers.py` |
| Connector base | `hotel/backend/app/services/connectors/base.py` |
| Connector registry | `hotel/backend/app/services/connectors/__init__.py` |
| Channel sync (connector kullanan) | `hotel/backend/app/services/channel_sync_service.py` |
| Mimari belge | `hotel/docs/ARCHITECTURE.md` |
| Test paketi giriş | `hotel/backend/tests/test_modules/` |

## İletişim

Soru çıkarsa `PROJECT_STATUS.md`'deki "Son güncelleme" notlarını ve `docs/reviews/`
altındaki review raporlarını incele. Tüm session özeti commit history'sinde:
`git log --oneline -30 origin/claude/wonderful-gates-cahvpv`.
