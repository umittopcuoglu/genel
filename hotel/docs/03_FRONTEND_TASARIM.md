# Frontend Tasarım Dökümanı (Claude)

> Hedef: User-friendly, hızlı, erişilebilir, AI-destekli PMS arayüzü. Resepsiyon personeli "vardiya başında 30 saniyede bağlanıp 3 saniyede oda durumunu görebilmeli."

---

## 1. Tasarım Sistemi

### 1.1 Marka & Tipografi
- **Logo alanı:** sol-üst, 32px yükseklik. Şimdilik metin: "**HotelOps**" (placeholder).
- **Font:** Inter (UI) + IBM Plex Mono (sayısal raporlar, kodlar).
- **Boyut skalası:** 12 / 14 / 16 / 18 / 24 / 32 / 48 px.

### 1.2 Renk Paleti (Light + Dark)

| Token | Light | Dark | Kullanım |
|---|---|---|---|
| primary | `#0F4C81` (lacivert) | `#5AA9E6` | CTA, link, vurgu |
| success | `#16A34A` | `#22C55E` | Clean, Paid, Available |
| warning | `#D97706` | `#F59E0B` | Dirty, Pending |
| danger | `#DC2626` | `#EF4444` | OOO, Overdue, Alert |
| info | `#0284C7` | `#38BDF8` | Inspected, Confirmed |
| bg | `#F8FAFC` | `#0B1220` | Sayfa zemin |
| surface | `#FFFFFF` | `#111827` | Kart |
| border | `#E2E8F0` | `#1F2937` | Çizgi |
| text-1 | `#0F172A` | `#F1F5F9` | Birinci |
| text-2 | `#475569` | `#94A3B8` | İkincil |

### 1.3 Layout Grid
- Container 1440 max-width, 24px gutters.
- Yan menü 256px (collapse 64px).
- Üst bar 56px sabit.
- Ana içerik 24px padding.
- Mobil: yan menü drawer, alt bar (5 sekme).

### 1.4 Temel Bileşenler (shadcn/ui üzerine)
`Button`, `Input`, `Select`, `DatePicker`, `RangePicker`, `Table` (TanStack), `Tabs`, `Dialog`, `Drawer`, `Toast`, `Badge` (renk durumlu), `Avatar`, `Stat` (KPI kartı), `Calendar` (Tape Chart için özelleştirme), `Kanban` (Housekeeping), `EmptyState`, `LoadingSkeleton`, `ErrorState`, `AIPanel` (önerileri gösteren standart panel — "Kabul/Düzenle/Reddet" butonları).

### 1.5 İkonografi
Lucide-react. Tutarlı: oda=🛏 BedDouble, misafir=Users, ödeme=CreditCard, temizlik=Sparkles, bakım=Wrench, AI=Sparkles+ (özel).

---

## 2. Navigasyon (IA — Information Architecture)

**Yan Menü (rol bazlı görünür):**
```
🏠 Dashboard
🛏 Ön Büro
   ├ Arrivals
   ├ Departures
   ├ In-House
   ├ Tape Chart (oda planı)
   └ Misafir Profilleri
📅 Rezervasyon
   ├ Yeni Rezervasyon
   ├ Takvim
   ├ Rate Yönetimi
   └ Channel Manager
🧹 Housekeeping
   ├ Oda Panosu
   ├ Görevler
   ├ Mini Bar
   └ Kayıp Eşya
💰 Muhasebe
   ├ Folios
   ├ Ödemeler
   ├ Faturalar (e-Fatura)
   ├ Night Audit
   └ Raporlar
🔧 Bakım
   ├ İş Emirleri
   ├ Ekipmanlar
   └ Önleyici Bakım
🍽 F&B
   ├ Restoran Rez
   ├ Oda Servisi
   └ Stok (dış)
🎉 Events (MICE)
   ├ Lead/Quote
   ├ BEO
   └ Run-of-Show
👥 CRM
   ├ Misafir 360°
   ├ Sadakat
   ├ Anketler
   └ Şikayetler
🔐 Güvenlik
   ├ Kart/Anahtar
   ├ Erişim Logu
   ├ Alarm
   └ KVKK
📊 Analitik
   ├ Yönetici Dashboard
   ├ Standart Raporlar
   ├ Özel Rapor
   └ User Activity Log
⚙ Ayarlar
```

**Üst Bar:**
- Global arama (Cmd/Ctrl+K) — odalar, misafirler, rezervasyonlar, faturalar.
- Hızlı aksiyon (F1=Yeni Rez, F2=Check-in, F3=Walk-in).
- Bildirimler (badge).
- AI asistan butonu (chat drawer).
- Profil + dil + tema.

---

## 3. Ana Dashboard (Manager Flash)

**Üst satır — 6 KPI kartı:**
1. Occupancy % (bugün) — sparkline son 7 gün
2. ADR — sparkline
3. RevPAR — sparkline
4. Arrivals (kaç gelmiş / kaç bekleniyor)
5. Departures (kaç çıkmış / kaç bekleniyor)
6. OOO odalar

**Orta satır — 2 panel:**
- 14 günlük Pickup grafiği (bar + line).
- Forecast vs Budget (line chart).

**Alt satır — 3 panel:**
- "Bugün dikkat" listesi (VIP gelişler, geciken ödemeler, açık şikayetler, kritik iş emirleri).
- AI Briefing (InsightAI özeti — 5 madde).
- Kanal satış dağılımı (pie + delta).

Tüm KPI'lar tıklanabilir → ilgili rapora derinleşme.

---

## 4. Modül Ekranları (Önemli Olanlar)

### 4.1 Tape Chart (Oda Planı Takvimi)
- Y ekseni: odalar (gruplanmış oda tipine göre).
- X ekseni: gün (varsayılan 14 gün, +/- ile aralık).
- Hücreler: rezervasyon bloğu (renkli: confirmed/in-house/checked-out/blocked).
- Drag-drop ile oda değiştirme + tarih kaydırma (snap-to-day).
- Sol panel: filtreler (tip, kat, durum).
- Üst panel: gün başına müsait sayısı.
- Hücreye hover → mini popover (misafir, kanal, bakiye, traces). Tık → drawer (detay).

### 4.2 Yeni Rezervasyon Sihirbazı (3 adım)
1. Tarih + misafir sayısı + oda tipi + tercih (sigara, üst kat, vb.)
2. Misafir bilgileri (otomatik tamamlama mevcut misafirden) + ödeme yöntemi
3. Özet + onay → otomatik confirmation e-mail
- Sağda canlı fiyat hesabı + AI önerisi ("Bu tarihler için %5 indirim önerilir, doluluk düşük").

### 4.3 Check-in Ekranı
- Sol: bugünkü arrivals listesi (filtre: VIP, grup, durum).
- Orta: seçilen rezervasyonun detayı + kişisel karşılama metni (FrontDesk AI üretti → "Düzenle/Kullan/Reddet").
- Sağ: oda atama (önerilen + manuel seçim) + ek hizmet upsell ("Erken check-in 200₺", "Üst kat 150₺").
- Alt: imza alanı + KVKK rıza onayı + EGM bildirimi (otomatik, durum LED'i).

### 4.4 Housekeeping Oda Panosu
- Grid: oda numarası + durum badge (renk) + atanan kat görevlisi + son güncelleme.
- Filtre: durum, kat, görevli, öncelik.
- Hücre tıkla → drawer (checklist, fotoğraf, "Inspected'a geç" butonu, "Arıza bildir").
- Üstte mini istatistik: Clean/Dirty/Inspected/OOO sayıları.
- CleanOps AI önerisi: "Bugün önce 4. kat (3 erken arrival var)".

### 4.5 Mobil Housekeeping (PWA)
- 3 sekme: Görevlerim / Mesajlar / Profil.
- Görev kartı: oda no, tip, checklist (swipe to complete), foto ekle, "Hazır" CTA.
- Offline durumunda kuyruğa al, online olunca senkron.
- Sesli not (opsiyonel) → metne çevir → trace olarak yaz.

### 4.6 Folio & Cashiering
- Sol: misafir + rezervasyon özeti.
- Orta: folio kalemleri (ekle/sil/düzenle/böl) + AI anomali badge'i (FinanceAI işaretlemişse).
- Sağ: ödeme paneli (nakit / kart / havale / sanal POS).
- Alt: "e-Fatura oluştur" / "Folio kapat" / "Bölme" aksiyonları.
- Audit log mini timeline.

### 4.7 Night Audit Sihirbazı
- Adım adım kontrol: açık folio'lar, ödenmemiş, müsaitlik tutarsızlığı.
- AI: "Anomali tespit edilmedi → otomatik kapat" CTA. Manuel devam seçeneği.
- Kapanış raporu PDF + dağıtım listesi.

### 4.8 BEO (Banquet Event Order)
- Üstte sekmeler: F&B, AV, Oda Bloğu, Faturalandırma, Zaman Çizelgesi.
- Versiyon karşılaştırma (diff view).
- "Departmanlara dağıt" → mutfak, teknik, HK için PDF üretir.

### 4.9 GuestAI Chatbot Yönetimi
- Solda canlı sohbetler (WhatsApp + web).
- Ortada konuşma + AI önerilen yanıt (insan onayı opsiyonel modu).
- Sağda misafir 360° özeti.

### 4.10 Misafir 360° Profili
- Üst: avatar + iletişim + tier badge + lifetime value.
- Sekmeler: Geçmiş Konaklamalar / Tercihler / Harcama / Şikayetler / Anketler / İletişim Logu.
- Üst sağ: "Kişisel teklif oluştur" (GuestAI).

### 4.11 User Activity Log
- TanStack table: kullanıcı, aksiyon, varlık, eski/yeni diff, IP, zaman.
- Filtre: kullanıcı, tarih aralığı, modül.
- Detay drawer → JSON diff (Monaco editor).

---

## 5. AI Bileşeni (Tüm Modüllerde Tutarlı)

`<AIPanel>` standart bileşen:

```
┌──────────────────────────────────────────────────┐
│ 🤖 FrontDesk AI önerisi                  [⋯][×]  │
├──────────────────────────────────────────────────┤
│ Mehmet Bey için kişisel karşılama:              │
│ "Tekrar hoşgeldiniz! Geçen ziyaretinizdeki      │
│  yüksek katı bu sefer de ayarladık..."          │
├──────────────────────────────────────────────────┤
│ Gerekçe: 3. ziyaret · üst kat tercihi (geçmiş)   │
│                                                  │
│ [ Düzenle ]  [ Kullan ]  [ Reddet ]              │
└──────────────────────────────────────────────────┘
```

- Asla otomatik uygulamaz; her zaman insan onayı.
- "Reddet" sebebini sorar (model iyileştirme telemetrisi).

---

## 6. State, Veri & Performans

- **Server state:** TanStack Query — anahtar `["module", "entity", filters]`. Stale-while-revalidate 30s.
- **WebSocket:** `useRealtimeChannel(channel)` hook'u; query invalidation tetikler.
- **Optimistic update:** check-in, oda durum değişimi, görev tamamlama.
- **Pagination:** sunucu taraflı + cursor (büyük tablo) ya da offset (küçük).
- **Code splitting:** her modül route bazlı dynamic import.
- **Image:** next/image; oda fotoğrafları S3'ten, WebP/AVIF.

---

## 7. Erişilebilirlik

- WCAG 2.1 AA hedefi. Renk kontrastı ≥ 4.5.
- Tüm kontroller klavye ile erişilebilir. Focus ring belirgin.
- ARIA: tablolarda `aria-sort`, dialoglarda `aria-modal`.
- Tape Chart: klavye navigasyonu (oklar) + screen-reader özet.
- Form hataları için `aria-describedby`.

---

## 8. i18n & l10n

- next-intl ile TR (default) + EN.
- Tüm string'ler `messages/tr.json`, `messages/en.json`.
- Para birimi: Intl.NumberFormat (TRY varsayılan; rapor başlıklarında multi-currency).
- Tarih: date-fns + locale.

---

## 9. Test Stratejisi

| Seviye | Araç | Kapsam |
|---|---|---|
| Unit | Vitest | utils, hooks |
| Component | Vitest + RTL | bileşenler |
| Storybook | Storybook | görsel regresyon (Chromatic) |
| E2E | Playwright | kritik akışlar (check-in, rez oluşturma, folio kapama) |
| Erişilebilirlik | axe-core | her sayfa CI'da otomatik |

---

## 10. Klasör Yapısı

```
app/
  (auth)/login/page.tsx
  (app)/
    layout.tsx                     # sidebar + topbar
    dashboard/page.tsx
    front-office/
      arrivals/page.tsx
      departures/page.tsx
      in-house/page.tsx
      tape-chart/page.tsx
      guests/[id]/page.tsx
    reservations/
      new/page.tsx
      calendar/page.tsx
      rates/page.tsx
      channels/page.tsx
    housekeeping/
      board/page.tsx
      tasks/page.tsx
      minibar/page.tsx
      lost-found/page.tsx
    finance/
      folios/page.tsx
      folios/[id]/page.tsx
      payments/page.tsx
      invoices/page.tsx
      night-audit/page.tsx
      reports/page.tsx
    maintenance/...
    fb/...
    events/...
    crm/...
    security/...
    analytics/...
    settings/...
components/
  ui/                              # shadcn primitives
  ai/AIPanel.tsx
  tape-chart/...
  kpi/StatCard.tsx
  ...
lib/
  api.ts                           # fetch wrapper (auth + tenant header)
  ws.ts
  hooks/...
  schemas/                         # zod
  utils/
messages/
  tr.json
  en.json
```

---

## 11. Görsel Doğrulama Süreci (Screenshot Loop)

Claude her ekran tamamlandığında:

1. Playwright ile ekran görüntüsü alır (light + dark, desktop + mobile).
2. Görseli `docs/screenshots/{modül}/{ekran}__{varyant}.png` altına kaydeder.
3. Görseli inceler ve şu kontrol listesi ile karşılaştırır:
   - [ ] Yüklenme → boş → hata durumları doğru.
   - [ ] Boşluklar, hizalama, kontrast.
   - [ ] AI panel beklenen yerde.
   - [ ] Kritik aksiyonlar 3 tıkdan az.
   - [ ] Klavye kısayolları çalışıyor.
   - [ ] Erişilebilirlik (axe) clean.
4. Hata varsa: `docs/bugs/` altına issue açar, ilgili tarafa (frontend kendisi / backend DeepSeek) yönlendirir.

---

## 12. Faz 1 Frontend Çıktıları (MVP)

- [ ] Auth (login, logout, refresh)
- [ ] Layout (sidebar + topbar + global arama + tema)
- [ ] Manager Dashboard (statik veriyle önce, sonra canlı)
- [ ] Tape Chart + Drawer
- [ ] Arrivals / Departures / In-House
- [ ] Check-in / Check-out akışı
- [ ] Yeni Rezervasyon sihirbazı
- [ ] Misafir 360° (temel sekmeler)
- [ ] Housekeeping oda panosu
- [ ] Folio görünümü + ödeme + kapatma
- [ ] Kullanıcı & Rol yönetimi
- [ ] User Activity Log
- [ ] AIPanel bileşeni + FrontDesk AI entegrasyonu
- [ ] PWA manifest + offline shell

---

## 13. İlk Sprint (2 Hafta)

1. Tasarım sistemi kurulumu (Tailwind tokens + shadcn).
2. Layout + auth scaffold.
3. Dashboard mock + KPI bileşenleri.
4. Tape Chart prototipi (mock veri).
5. Check-in ekranı prototipi.
6. Storybook + Playwright + axe CI kurulumu.
7. DeepSeek'in ürettiği OpenAPI'den TS tipleri (`openapi-typescript`).

Sprint sonunda canlı backend entegrasyonu için hazır olunmalı.
