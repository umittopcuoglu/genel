# Ekran Görüntüsü Testi Raporu — Tüm Sayfalar

**Tarih:** 2026-06-13 · **Araç:** Playwright (chromium-light) · **Spec:** `tests/screenshots.spec.ts`
**Kapsam:** 30 rota (3 public + 27 uygulama) · **Mod:** Backend kapalı (mock fallback)

## Özet

| Sonuç | Sayı |
|---|---|
| Render olan + ekran görüntüsü alınan sayfa | **30 / 30** ✅ |
| Görsel olarak bozuk / boş sayfa | 0 |
| Next.js hata ekranı (error boundary) gösteren | 0 |
| Ölümcül olmayan hydration uyarısı olan (app sayfaları) | 27 |
| Yakalanmamış `fetch` hatası olan | 2 (payments, insights) |

Her sayfa için `screenshots/<label>.png` (fullPage) üretildi. Testler backend
gerektirmez: `(app)` layout'unda auth guard yoktur, sayfalar API'ye ulaşamayınca
mock veriyle (MockBanner) render olur.

## Test edilen sayfalar

**Public:** login, book, guest-wifi
**Operasyon:** dashboard, front-office, reservations, channels, housekeeping, finance, maintenance, analytics
**İş/Finans:** payments, crm, whatsapp, einvoice, revenue, insights
**Genişleme:** groups, fnb, security, hr, gds, iot
**İleri teknoloji:** cv, voice, properties, mobile-checkin, blockchain
**Sistem:** settings, settings/integrations

## Bulgular

### 1. Hydration uyarıları (kozmetik, kurtarılabilir) — 27 app sayfası
React hata #418/#423/#425: SSR (sunucu, varsayılan dil) ile CSR (istemci,
localStorage/`navigator.language` → TR) arasındaki dil farkından kaynaklanıyor.
React kendini kurtarıyor; ekran bozulmuyor. **Öneri:** dil/tema okuyan bileşenlerde
`useEffect` ile mount sonrası set veya `suppressHydrationWarning`.

### 2. Yakalanmamış `fetch` hatası — payments, insights
Bu iki birleştirme-kolu sayfası backend kapalıyken ham `fetch()` ile istek atıp
hatayı yakalamıyor (`TypeError: Failed to fetch` konsola düşüyor). Operasyon-kolu
sayfaları aynı durumu `useApiData` ile zarifçe mock fallback'e çeviriyor.
Sayfa yine de render oluyor ama konsol hatası üretiyor. **Öneri:** `useApiData`
desenine veya try/catch + fallback'e geçir.

## Çalıştırma

```bash
cd hotel/frontend && npx next start -p 3000   # prod build :3000
cd hotel/qa/e2e && npm install
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
  npx playwright test screenshots.spec.ts --project=chromium-light
# çıktı: hotel/qa/e2e/screenshots/*.png
```
