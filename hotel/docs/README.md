# HotelOps — AI-Destekli Otel Yönetim Sistemi (PMS)

Dökümantasyon dizini:

| Döküman | İçerik |
|---|---|
| [01_PROJE_PLANI.md](./01_PROJE_PLANI.md) | Genel plan, fazlar, modül haritası, mimari, UX prensipleri |
| [02_DEEPSEEK_TALIMATLARI.md](./02_DEEPSEEK_TALIMATLARI.md) | DeepSeek için backend geliştirme talimatları (veri modeli + endpoint'ler + AI ajanları) |
| [03_FRONTEND_TASARIM.md](./03_FRONTEND_TASARIM.md) | Tasarım sistemi, IA, ekran detayları, klasör yapısı (Claude) |
| [04_DOGRULAMA_DONGUSU.md](./04_DOGRULAMA_DONGUSU.md) | Ekran görüntüsü ile hata tespit ve düzeltme süreci |

## İş Bölümü
- **Frontend tasarım + kod:** Claude
- **Backend kod:** DeepSeek
- **Doğrulama:** Claude (screenshot loop + bug raporu)

## Hızlı Başlangıç (öneri)
1. Bu 4 dökümanı paydaşlarla onayla.
2. `02_DEEPSEEK_TALIMATLARI.md`'yi DeepSeek'e ilet.
3. Claude Faz 1 frontend sprintine başlar (bkz. 03 §13).
4. DeepSeek OpenAPI spec yayınladığında entegrasyon başlar.
5. Her modül sonrası 04'teki döngü uygulanır.
