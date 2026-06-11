# Otel Yönetim Sistemi (AI-Destekli PMS) — Proje Planı

## 1. Genel Bakış
AI ajanları ile güçlendirilmiş, modüler, bulut tabanlı bir Otel Yönetim Sistemi (PMS). Roadmap 4 fazda ilerler (MVP → Büyüme → Olgunlaşma → İleri Özellikler).

**İş Bölümü:**
- **Frontend (Tasarım + Kod):** Claude — UI/UX, ekran akışları, bileşen kütüphanesi, dashboard tasarımı, prototip ve nihai React/Next.js implementasyonu.
- **Backend (Kod):** DeepSeek — API katmanı, veri modeli, AI Agent servisleri, dış entegrasyonlar, güvenlik.
- **Doğrulama döngüsü:** Her DeepSeek teslimatından sonra Claude ekran görüntüsü alır → hataları tespit eder → DeepSeek'e geri bildirim verir.

---

## 2. Roadmap (Fazlar)

### Faz 1 — MVP (0-3 Ay)
- Ön Büro: Check-in/Out, Oda Yönetimi
- Rezervasyon Motoru (direkt rezervasyon)
- Temel Cashiering & Folio
- Housekeeping Oda Durumu
- Kullanıcı & Rol Yönetimi (RBAC)
- FrontDesk AI (temel)

### Faz 2 — Büyüme (3-6 Ay)
- Channel Manager (3-5 OTA)
- RevenueIQ AI (dinamik fiyatlama)
- Tam Muhasebe + e-Fatura (GİB)
- GuestAI Chatbot (WhatsApp Business API)
- Mobil Housekeeping uygulaması

### Faz 3 — Olgunlaşma (6-12 Ay)
- Tüm AI Ajanları aktif (FinanceAI, CleanOps, TechCare, ChefIQ, ShiftAI, SecureAI, InsightAI, EventIQ)
- F&B / POS entegrasyonu (DIŞ FİRMA)
- HR & Vardiya Modülü
- GDS entegrasyonu
- IoT / Akıllı Oda (Nest, KNX, Philips Hue)
- Gelişmiş Analitik Dashboard

### Faz 4 — İleri Özellikler (12+ Ay)
- Computer Vision (oda kalite kontrolü)
- Sesli Kontrol (Alexa / Google for Hospitality)
- Çok-mülk yönetimi (zincir oteller)
- Mobil Check-in (pasaport tanıma / EGM bildirimi)
- Blockchain tabanlı misafir kimlik doğrulama

---

## 3. Modül Haritası (10 Modül)

| # | Modül | AI Agent | Faz |
|---|-------|----------|-----|
| 1 | Ön Büro (Front Office) | FrontDesk AI | 1 |
| 2 | Rezervasyon & Channel Manager | RevenueIQ | 1-2 |
| 3 | Groups & Events (MICE) | EventIQ | 3 |
| 4 | Muhasebe & Cashiering | FinanceAI | 1-2 |
| 5 | Housekeeping | CleanOps AI | 1-2 |
| 6 | Bakım & Teknik Servis | TechCare AI | 3 |
| 7 | F&B (Yiyecek & İçecek) | ChefIQ | 3 (DIŞ FİRMA entegrasyonu) |
| 8 | Misafir Deneyimi & CRM | GuestAI | 2-3 |
| 9 | Güvenlik & Erişim Kontrol | SecureAI | 3 |
| 10 | Revenue Management & Raporlama | InsightAI | 2-3 |

İK için **ShiftAI** ayrıca yer alır (vardiya planlama, devamsızlık tahmini).

---

## 4. Mimari Yaklaşım

```
┌────────────────────────────────────────────────────────┐
│  FRONTEND (Claude)                                     │
│  Next.js 14 (App Router) + TypeScript + Tailwind       │
│  shadcn/ui + Recharts + TanStack Query + Zustand       │
└────────────────────────────────────────────────────────┘
                     ↓ REST/GraphQL + WebSocket
┌────────────────────────────────────────────────────────┐
│  API GATEWAY (DeepSeek)                                │
│  Kimlik (JWT + RBAC) · Rate limit · Audit log          │
└────────────────────────────────────────────────────────┘
                     ↓
┌──────────────┬──────────────┬──────────────┬──────────┐
│ Core Services│ AI Agents    │ Integrations │ Reporting│
│ (FastAPI/    │ (Python +    │ (OTA, POS,   │ (ETL +   │
│  NestJS)     │  LangChain)  │  e-Fatura)   │  OLAP)   │
└──────────────┴──────────────┴──────────────┴──────────┘
                     ↓
        PostgreSQL · Redis · S3 · Kafka (event bus)
```

**Güvenlik:** SOC 2 Type II, PCI-DSS, KVKK/GDPR, RBAC, AES-256, tam audit log.

---

## 5. Çalışma Akışı (Claude ↔ DeepSeek)

Her modül için 5 adım:

1. **Tasarım (Claude):** Wireframe + UI bileşenleri + ekran akışı + bileşen API'si.
2. **Talimat (Claude → DeepSeek):** Endpoint listesi, veri modeli, kabul kriterleri (bkz. `02_DEEPSEEK_TALIMATLARI.md`).
3. **Backend (DeepSeek):** API + servisler + entegrasyonlar implementasyonu.
4. **Entegrasyon (Claude):** Frontend'i gerçek API'ye bağlama.
5. **Doğrulama:** Claude her ekranın screenshot'unu alır → görsel + fonksiyonel hataları listeler → DeepSeek'e PR comment formatında geri bildirim → tekrar.

**Kabul tamamlanma kriteri (her modül):**
- [ ] Tüm ekranlar mobile + desktop'ta sorunsuz.
- [ ] WCAG 2.1 AA erişilebilirlik.
- [ ] API yanıt < 300ms (p95).
- [ ] Tüm CRUD işlemleri audit log'da.
- [ ] Hata durumları için empty/error/loading state mevcut.
- [ ] Ekran görüntüsü incelendi, regresyon yok.

---

## 6. UX Prensipleri (User Friendly)

1. **Tek bakışta görünürlük:** Ana dashboard tüm KPI'ları (occupancy, ADR, RevPAR, check-in/out sayıları, arıza, müsait oda) 3 saniyede iletir.
2. **3-tıklama kuralı:** Hiçbir kritik aksiyon (yeni rezervasyon, check-in, folio kapama) 3 tıklamadan fazla almaz.
3. **Klavye kısayolları:** Resepsiyon personeli için F-tuşları (F1: yeni rez, F2: arrivals, F3: in-house...).
4. **Renkli durum kodları (tutarlı):**
   - Yeşil = Clean / Available / Paid
   - Sarı = Dirty / Pending / In-progress
   - Kırmızı = Out of Order / Overdue / Alert
   - Mavi = Inspected / Confirmed
5. **AI önerileri her zaman opsiyonel:** Otomasyon önerisi → "Kabul et / Düzenle / Reddet". Asla kullanıcıyı baypaslama.
6. **Offline-first kritik ekranlar:** Check-in/out ve housekeeping mobil, internet kesintisinde de çalışmalı (PWA + IndexedDB).
7. **Türkçe + İngilizce** (i18n; ileride Arapça/Rusça için hazır).
8. **Karanlık + açık tema.**

---

## 7. Teknoloji Yığını

**Frontend:**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS + shadcn/ui (Radix tabanlı)
- TanStack Query (server state) + Zustand (client state)
- Recharts (grafikler) + TanStack Table (data grid)
- React Hook Form + Zod (validasyon)
- next-intl (i18n) + next-themes (dark/light)
- Playwright (E2E test) + Storybook (component katalog)

**Backend (DeepSeek için öneri):**
- Python FastAPI **veya** Node.js NestJS (DeepSeek seçer; tek dil olmalı)
- PostgreSQL 15+ (ana veri tabanı)
- Redis (cache + queue)
- Kafka veya RabbitMQ (event bus)
- LangChain / LlamaIndex (AI Agent katmanı)
- OpenAI/Claude/DeepSeek API (LLM)
- S3-compatible object storage (Minio veya AWS S3)
- Docker + Kubernetes (deploy)

**DevOps:**
- GitHub Actions (CI/CD)
- Sentry (hata izleme)
- Grafana + Prometheus (metrik)
- Vercel (frontend) + AWS/GCP (backend)

---

## 8. Sonraki Adım

1. `02_DEEPSEEK_TALIMATLARI.md` dökümanı DeepSeek'e iletilir.
2. `03_FRONTEND_TASARIM.md` dökümanına göre Claude wireframe + bileşenlere başlar.
3. Faz 1 MVP için 12 haftalık sprint planı oluşturulur (her sprint 1 modül).
