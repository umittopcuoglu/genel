# Doğrulama Döngüsü — Ekran Görüntüsü ile Hata Tespit & Düzeltme

> Amaç: DeepSeek backend tamamladıktan sonra Claude frontend'i entegre eder, ekran görüntüsü alır, hataları sistematik raporlar.

---

## 1. Genel Akış

```
DeepSeek PR açar  ─►  Claude entegre eder  ─►  Playwright screenshot
                                                    │
                                                    ▼
                              docs/screenshots/{modül}/...png
                                                    │
                                                    ▼
                              Claude görseli + DOM + axe + console raporu inceler
                                                    │
                              ┌─────────────────────┴───────────────────┐
                              │                                         │
                       Sorun yok ✅                              Sorun var ❌
                              │                                         │
                              ▼                                         ▼
                       PR merge edilir                docs/bugs/{tarih}-{slug}.md yazılır
                                                                        │
                                                                        ▼
                                                       DeepSeek/Frontend'e atanır → fix → tekrar
```

---

## 2. Screenshot Otomasyonu (Playwright)

`tests/visual/{modül}.spec.ts`:

```ts
test('check-in screen — light desktop', async ({ page }) => {
  await page.goto('/front-office/arrivals');
  await page.click('text=Mehmet Yılmaz');
  await page.click('text=Check-in');
  await expect(page).toHaveScreenshot('checkin-light-desktop.png', {
    fullPage: true,
    mask: [page.locator('[data-clock]')], // değişken alanları maskele
  });
});
```

Varyantlar:
- `light-desktop` (1440×900)
- `dark-desktop`
- `light-mobile` (390×844)
- `dark-mobile`

CI'da `--update-snapshots` ile baseline güncellenir (PR review zorunlu).

---

## 3. Bug Raporu Şablonu (`docs/bugs/`)

```markdown
---
id: BUG-2026-06-10-001
modül: Front Office / Check-in
şiddet: high   # critical | high | medium | low
sahip: deepseek   # deepseek | claude
durum: open
açan: claude
açılış: 2026-06-10
---

## Özet
POST /api/v1/checkin/{id} 500 dönüyor, folio oluşmuyor.

## Reproduce
1. /front-office/arrivals
2. "Mehmet Yılmaz" satırı → "Check-in" tıkla
3. Oda 305 seç → Onayla
4. Backend 500 hatası, UI'da kırmızı toast

## Beklenen
- 200 OK
- folio.id mevcut, status=open
- Oda durumu otomatik clean → occupied

## Gerçekleşen
- 500 Internal Server Error
- Sentry: NullPointerException folio_id

## Ekran görüntüsü
![bug](./screenshots/2026-06-10-checkin-500.png)

## Network
```
POST /api/v1/checkin/123  → 500
{ "error": { "code": "INTERNAL", "message": "folio creation failed" } }
```

## Etki
Check-in akışı tümüyle bloke.

## Önerilen düzeltme
folio oluşumu transaction içine alınmalı; folio_id null kalmamalı.
```

---

## 4. Görsel Hata Kontrol Listesi (her ekran için)

- [ ] **Yüklenme:** Skeleton var, layout shift yok.
- [ ] **Boş durum:** EmptyState ikonu + mesaj + CTA.
- [ ] **Hata durumu:** ErrorState + retry CTA.
- [ ] **Hizalama:** 8-pt grid'e uyumlu.
- [ ] **Tipografi:** Hiyerarşi tutarlı (H1>H2>body).
- [ ] **Renk kontrastı:** axe-core uyarı vermiyor.
- [ ] **Etkileşim:** hover/focus/active görsel feedback.
- [ ] **Klavye:** Tab sırası mantıklı, focus trap dialog'larda doğru.
- [ ] **Mobil:** taşma yok, dokunma hedefleri ≥ 44×44.
- [ ] **AI Panel:** beklenen yerde, üç buton (Düzenle/Kullan/Reddet) görünür.
- [ ] **Lokalizasyon:** TR + EN'de overflow/satır kırılması yok.

---

## 5. Önceliklendirme

| Şiddet | Tanım | SLA |
|---|---|---|
| critical | Üretim bloke, veri kaybı, güvenlik | 4 saat |
| high | Ana akış bozuk, geçici workaround mümkün | 1 gün |
| medium | İkincil özellik, UX bozulması | 3 gün |
| low | Kozmetik, küçük string | sprint sonu |

---

## 6. Kapanış

Bug kapanması için:
1. Reproduce test yazılmalı (pytest veya Playwright).
2. Fix uygulanmalı.
3. PR'da `Closes BUG-id` referansı.
4. Claude bir kez daha screenshot alır → baseline ile diff sıfır olmalı.
5. Bug dosyası `durum: closed` yapılır.

---

## 7. Sprint Sonu Görsel Regresyon Raporu

Her sprint sonunda Claude:
- Tüm baseline screenshot'ları yeniler.
- Değişen ekranları markdown raporda listeler (`docs/sprints/{n}-visual-report.md`).
- Onaylanmayan görsel değişikler bug açar.

---

## 8. User Friendly Doğrulama Anketleri

Faz 1 MVP sonunda 3 resepsiyon personeli + 1 housekeeping ile usability testi:
- Görev tamamlama süresi (check-in < 60s, oda atama < 30s).
- SUS (System Usability Scale) ≥ 80.
- Hata oranı < %5.

Sonuçlara göre Faz 2 başında UX iterasyonu.
