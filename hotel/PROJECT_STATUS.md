# HotelOps — Proje Durum Panosu

> Bu dosya canlı durum kaydıdır. Her review/teslimat sonrası güncellenir.
> Nightly QA workflow'u test sonuçlarını buraya işler.

> **2026-06-12 — HotelRunner/Cloudbeds denklemi tamamlandı:**
> PMS + **Booking Engine** (`/api/v1/public/*`, komisyonsuz doğrudan satış, `/book` misafir ekranı)
> + **Channel Manager** (rezervasyonda tüm aktif OTA'lara otomatik stok push + sync log, `/channels` ekranı)
> + **Entegrasyon Ayarları** (GİB e-Fatura · OTA · GDS · WhatsApp · **Payment Gateway** · IoT/MQTT —
> admin parametreleri çalışma zamanında girer, şifreli saklanır, tek tıkla canlı bağlantı testi)
> Frontend "Grand Hotel" tasarım dili + sayfa geçiş animasyonları. Testler: 201 + 23 yeni = **224 yeşil**.

**Son güncelleme:** 2026-06-13 (İKİ GELİŞTİRME KOLU BİRLEŞTİRİLDİ — `ecstatic-gates` operasyon kolu + `wonderful-gates` iş/finans kolu tek projede; çakışmalar çözüldü, tüm testler yeşil) · **Faz:** 1-4 · **Test Suite:** 350 yeşil · **Frontend build:** 33 route ✓

> **2026-06-13 — Çok-kollu birleştirme (merge):** Proje iki paralel Claude oturumunda inşa edildi ve bu tarihte
> tek koda birleştirildi. **Operasyon kolu** (bu branch): F&B/POS, Güvenlik & KVKK, HR & Vardiya, GDS, IoT,
> Computer Vision, Sesli Kontrol, Multi-Property, Mobil Check-in, Blockchain, Analitik + tüm frontend i18n/wiring.
> **İş/Finans kolu** (devralınan): Payment Gateway (iyzico/PayTR/Stripe/Craftgate), GİB e-Fatura
> (Foriba/İzibiz/Logo/Uyumsoft), CRM & Misafir 360 & Segment & Kampanya, Revenue Management, WhatsApp Business,
> InsightAI, OTA Connector'lar (Booking/Expedia/Agoda) + **EventBus / Modular Monolith** mimarisi (bounded context).
> Çakışan F&B/Güvenlik modüllerinde daha kapsamlı operasyon-kolu implementasyonu korundu; AI ajanları yeni
> `BaseAgent._run` sözleşmesine uyarlandı. Birleşik test: **350 yeşil**, frontend **33 route** derleniyor.

## Modül Durumu

| # | Modül | Backend (DeepSeek) | Frontend (Claude) | Review | Faz |
|---|-------|--------------------|--------------------|--------|-----|
| 0 | Altyapı (Auth+RBAC+Audit) | ✅ KABUL (tur 2) | — | REVIEW-...-tur2 | 1 |
| 1 | Ön Büro | ✅ KABUL (tur 1) | ✅ ekranlar live (backend API entegre) | REVIEW-2026-06-11-TASK-002 | 1 |
| 2 | Rezervasyon | ✅ KABUL (tur 1) | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-11-TASK-003 | 1 |
| 4 | Muhasebe & Cashiering | ✅ KABUL (tur 1) | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-11-TASK-004 | 1 |
| 5 | Housekeeping | ✅ KABUL | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-13-TASK-005 | 1-2 |
| — | FrontDesk AI (temel) | ⬜ | ⬜ | — | 1 |
| 3 | Groups & Events | ✅ KABUL | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-13-TASK-014 | 3 |
| 6 | Bakım & Teknik | ✅ KABUL | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-13-TASK-015 | 3 |
| 7 | F&B (dış entegrasyon) | ✅ KABUL | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-13-TASK-016 | 3 |
| 8 | CRM & Misafir 360 & GuestAI | ✅ KABUL (birleştirme kolu) | ✅ ekran live (`/crm`) | REVIEW-2026-06-13-TASK-011/012 | 2 |
| 9 | Güvenlik & KVKK | ✅ KABUL | ✅ ekran live (canlı API + mock fallback) | REVIEW-2026-06-13-TASK-017 | 3 |
| 10 | Raporlama & InsightAI | ✅ KABUL (analitik uçları + InsightAI servis/ekran) | ✅ ekran live (`/analytics`, `/insights`) | REVIEW-2026-06-13-TASK-013 | 2 |
| 11 | Payment Gateway (iyzico/PayTR/Stripe) | ✅ KABUL (birleştirme kolu) | ✅ ekran live (`/payments`) | REVIEW-2026-06-13 | 2 |
| 12 | GİB e-Fatura (Foriba/İzibiz/Logo/Uyumsoft) | ✅ KABUL (birleştirme kolu) | ✅ ekran live (`/einvoice`) | REVIEW-2026-06-13 | 2 |
| 13 | Revenue Management / RevenueIQ | ✅ KABUL (birleştirme kolu) | ✅ ekran live (`/revenue`) | REVIEW-2026-06-13 | 2 |
| 14 | WhatsApp Business API | ✅ KABUL (birleştirme kolu) | ✅ ekran live (`/whatsapp`) | REVIEW-2026-06-13 | 2 |

Durum: ⬜ bekliyor · 🟡 devam · 🟠 review'da · ✅ kabul · ❌ düzeltmede

## Açık Görevler (orchestrator/tasks/)
| Görev | Modül | Durum | Faz | Tur |
|---|---|---|---|---|
| TASK-001 | Altyapı: Auth + RBAC + Audit | ✅ KABUL | 1 | 2 |
| TASK-002 | Modül 1: Ön Büro | ✅ KABUL | 1 | 1 |
| TASK-003 | Modül 2: Rezervasyon & Müsaitlik | ✅ KABUL | 1 | 1 |
| TASK-004 | Modül 4: Muhasebe & Cashiering | ✅ KABUL | 1 | 1 |
| TASK-005 | Modül 5: Housekeeping | ✅ KABUL | 1 | 1 |
| TASK-006 | Altyapı: WebSocket + E2E + Docker + CI/CD | ⬜ sıraya girecek | 1 | 1 |
| TASK-007 | Altyapı: Ortak AI Çekirdeği (BaseAgent + LLM + PII maskeleme) | ✅ KABUL | 2 | 1 |
| TASK-008 | Modül 2 AI Genişleme: Channel Manager & OTA | ✅ KABUL | 2 | 1 |
| TASK-009 | Modül 2 AI Genişleme: RevenueIQ Advisor | ✅ KABUL | 2 | 1 |
| TASK-010 | Modül 4 Genişleme: Tam Muhasebe & GİB e-Fatura | ✅ KABUL | 2 | 1 |
| TASK-011 | Modül 8: CRM & Misafir 360 & Loyalty | ✅ KABUL | 2 | 1 |
| TASK-012 | Modül 8 AI: GuestAI Chatbot (WhatsApp) | ✅ KABUL | 2 | 1 |
| TASK-013 | Modül 10: Raporlama & InsightAI | ✅ KABUL | 2 | 1 |
| TASK-014 | Modül 3: Gruplar & Etkinlikler (MICE) + EventIQ AI | ✅ KABUL | 3 | 1 |
| TASK-015 | Modül 6: Bakım & Teknik Servis + TechCare AI | ✅ KABUL | 3 | 1 |
| TASK-016 | Modül 7: F&B & POS Entegrasyonu + ChefIQ AI | ✅ KABUL | 3 | 1 |
| TASK-017 | Modül 9: Güvenlik & Erişim Kontrol & KVKK + SecureAI | ✅ KABUL | 3 | 1 |
| TASK-018 | HR & Vardiya Modülü + ShiftAI | ✅ KABUL | 3 | 1 |
| TASK-019 | GDS Entegrasyonu (Amadeus/Sabre/Travelport) | ✅ KABUL | 3 | 1 |
| TASK-020 | IoT / Akıllı Oda Entegrasyonu (Nest, KNX, Hue) | ✅ KABUL | 3 | 1 |
| TASK-021 | Faz 4: Computer Vision — Oda Kalite Kontrol + Hasar Tespiti | ✅ KABUL | 4 | 1 |
| TASK-022 | Faz 4: Sesli Kontrol — Alexa / Google Assistant | ✅ KABUL | 4 | 1 |
| TASK-023 | Faz 4: Çok-Mülk Yönetimi — Otel Zinciri Konsolidasyonu | ✅ KABUL | 4 | 1 |
| TASK-024 | Faz 4: Mobil Check-in — Pasaport OCR & EGM Bildirimi | ✅ KABUL | 4 | 1 |
| TASK-025 | Faz 4: Blockchain Misafir Kimliği — Self-Sovereign Identity | ✅ KABUL | 4 | 1 |

## Notlar
- **Gelişmiş Analitik Dashboard** = Claude frontend görev (TASK-013 ekranlarının genişletilmesi); ayrı backend task değil
- **Faz 3-4 modül ekranları (2026-06-13):** HR, GDS, IoT, CV, Voice, Multi-Property, Mobile Check-in,
  Blockchain ekranları `useApiData` deseniyle canlı `/api/v1/*` uçlarına bağlandı (mock fallback + MockBanner).
  Toplu liste ucu olmayan alt-sekmeler (groups→events, cv→defects) mock'ta bırakıldı.
- **Analytics (Gelişmiş Analitik Dashboard) — ✅ canlandı (2026-06-13):** Gerçek raporlama uçları eklendi
  (`/reports/occupancy-trend` haftalık YoY, `/reports/revenue-trend` aylık oda geliri, `/reports/source-mix`
  rezervasyon kaynak dağılımı — `analytics_service` ile DB'den hesap). Ekran bu uçlara bağlı; veri boşsa
  mock'a düşer. Kalan TASK-013 kapsamı: InsightAI günlük brief/öneri üretimi (ai_endpoints'te mock mevcut).

## Açık Geri Bildirimler (orchestrator/feedback/)
_Yok. (FB-001 kapatıldı — düzeltmeler ağ engeli nedeniyle denetçi/Claude tarafından uygulandı.)_

## Son Review Raporları (docs/reviews/)
- `REVIEW-2026-06-11-TASK-001-tur2.md` — **KABUL** ✅ (6/6 backend testi + 6 kontrat testi yeşil, canlı API doğrulandı)
- `REVIEW-2026-06-11-TASK-001.md` — DÜZELTME GEREKLİ ❌ (tur 1, FB-001)

## Bilinen Engeller
- ⚠️ `api.deepseek.com` cloud ortam allowlist'inde kapalı → görevler manuel modla
  (`run_task.py --manual`) veya kullanıcının makinesinden API moduyla yürür.
  Tam otomasyon için: Claude Code web → ortam ayarları → network allowlist'e
  `api.deepseek.com` eklenmeli.
