# DeepSeek Çalışma Protokolü — Görev / Teslim / Geri Bildirim

> Bu doküman, Claude (orkestratör + denetçi) ile DeepSeek (backend kodlayıcı) arasındaki
> çalışma protokolünü tanımlar. Teknik gereksinimler `02_DEEPSEEK_TALIMATLARI.md`'dedir;
> bu doküman **nasıl iletişim kurulacağını** tanımlar.

---

## 1. Roller

| Rol | Sorumlu | Görev |
|---|---|---|
| Orkestratör + Denetçi | **Claude** | Görev yazar (TASK), teslimatı denetler (REVIEW), düzeltme ister (FB) |
| Backend Kodlayıcı | **DeepSeek** | TASK'a göre kod üretir, FB'ye göre düzeltir |
| Frontend | **Claude** | Tüm UI tasarım + kod |

## 2. Akış

```
Claude TASK-NNN.md yazar (orchestrator/tasks/)
        │
        ▼
orchestrator/run_task.py  ──►  DeepSeek API (deepseek-chat)
        │                          │
        │                          ▼
        │                  Kod dosyaları üretilir
        ▼                          │
backend/ altına yazılır  ◄─────────┘
        │
        ▼
orchestrator/review.py  ──►  docs/reviews/REVIEW-{tarih}-{görev}.md
        │
   ┌────┴─────┐
   │          │
 KABUL    DÜZELTME GEREKLİ
   │          │
   ▼          ▼
 commit   orchestrator/feedback/FB-NNN.md → DeepSeek'e yeni tur
```

## 3. Görev Formatı — `orchestrator/tasks/TASK-NNN.md`

```markdown
---
id: TASK-001
modül: Altyapı / Auth
durum: open          # open | in-progress | review | done
öncelik: critical
tur: 1               # kaçıncı deneme
---

## Kapsam
(Ne yapılacak — 2-3 cümle)

## Üretilecek Dosyalar
- backend/app/core/auth.py
- backend/tests/test_auth.py
- ...

## Endpoint'ler
(Varsa, tam liste — 02 dokümanından kopyalanır)

## Kabul Kriterleri
- [ ] ... (ölçülebilir maddeler)

## Test Beklentileri
- Her endpoint için 1 happy-path + 1 error-path (pytest + httpx)

## Bağlam
(DeepSeek'in bilmesi gereken mevcut kod / önceki kararlar)
```

## 4. Teslim Kuralları (DeepSeek'in uyacağı)

1. **Sadece TASK'ta istenen dosyaları üret.** Kapsam dışına çıkma.
2. Her dosyayı şu blok formatında ver (orchestrator otomatik ayrıştırır):
   ````
   ### FILE: backend/app/core/auth.py
   ```python
   (dosya içeriği — eksiksiz, kırpılmamış)
   ```
   ````
3. Kod + migration + test + OpenAPI güncellemesi **birlikte** teslim edilir.
4. `qa/` klasörüne ASLA dosya yazma — orası Claude'un bağımsız denetim alanıdır.
5. Açıklama ve docstring'ler Türkçe.
6. `02_DEEPSEEK_TALIMATLARI.md` §0'daki tüm genel kurallar geçerli (UUID id, audit log, soft delete, hata formatı, p95<300ms).

## 5. Geri Bildirim Formatı — `orchestrator/feedback/FB-NNN.md`

```markdown
---
id: FB-001
task: TASK-001
şiddet: high         # critical | high | medium | low
durum: open
---

## Bulgu
(Ne yanlış — review raporundan)

## Reproduce
(Komut / test adı / endpoint çağrısı)

## Beklenen
(Doğru davranış — 02 dokümanı referansı ile)

## Not
(Varsa öneri: "transaction içine al", "şemayı X yap" gibi)
```

DeepSeek FB'yi alınca: önce reproduce eden test ekler → düzeltir → aynı FILE blok formatında teslim eder.

## 6. Sistem Promptu (orchestrator her çağrıda gönderir)

```
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
```

## 7. Denetim Kriterleri (Claude'un review.py'de baktıkları)

| Kontrol | Araç |
|---|---|
| Kontrat testleri geçiyor mu | `pytest qa/contract` |
| DeepSeek'in kendi testleri geçiyor mu | `pytest backend/tests` |
| Beklenen endpoint'ler mevcut mu | OpenAPI spec diff |
| Zorunlu model alanları (UUID, timestamps, soft delete) | statik tarama |
| Audit log entegrasyonu | statik tarama + test |
| Hata formatı uyumu | kontrat testi |
| `qa/` klasörüne dokunulmamış mı | git diff kontrolü |

Sonuç raporu: `docs/reviews/REVIEW-{YYYY-MM-DD}-{task-id}.md` → `KABUL` veya `DÜZELTME GEREKLİ`.

## 8. Tekrarlayan Denetim (Claude'un QA Job'u)

- **Aktif oturumda:** Claude `/loop 30m` ile inbox + yeni teslimat kontrolü yapar.
- **Oturum dışı:** `.github/workflows/nightly-qa.yml` her gece testleri koşar,
  `PROJECT_STATUS.md`'yi günceller. Claude her oturum başında bu raporu okur.
