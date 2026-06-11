# HotelOps — Geliştirme Rehberi

## Genel Akış

```
Claude görev yazar → DeepSeek backend üretir → Claude denetler → kabul/düzeltme
                                                      │
Claude frontend'i gerçek API'ye bağlar → screenshot doğrulaması → bug raporu
```

Detaylı protokol: [`docs/05_DEEPSEEK_PROTOKOL.md`](docs/05_DEEPSEEK_PROTOKOL.md)

## Kurulum

```bash
# 1. Ortam değişkenleri (repo kökünde .env — .env.example'dan kopyala)
cd ..  # repo kökü
cp .env.example .env   # DEEPSEEK_API_KEY ve diğer anahtarları doldur
source setup_env.sh

# 2. Backend (TASK-001 teslim edildikten sonra)
cd hotel/backend
docker compose up -d
python seed.py
pytest

# 3. Frontend
cd hotel/frontend
npm install
npm run dev   # http://localhost:3000
```

## DeepSeek'e Görev Gönderme (Orkestratör)

### API modu (DeepSeek API erişimi olan makinede)
```bash
cd hotel
python orchestrator/run_task.py TASK-001
# → görevi gönderir, dönen kodu backend/'e yazar, review.py'yi otomatik koşar
```

### Manuel mod (API erişimi yoksa — örn. bu cloud ortamı)
```bash
python orchestrator/run_task.py TASK-001 --manual
# → orchestrator/outbox/TASK-001.prompt.md üretilir
# → içeriği chat.deepseek.com'a yapıştır
# → yanıtı orchestrator/inbox/TASK-001.md olarak kaydet
python orchestrator/run_task.py TASK-001 --ingest
# → dosyalar backend/'e yazılır, denetim raporu üretilir
```

### Düzeltme turu
```bash
python orchestrator/run_task.py TASK-001 --feedback FB-001
```

## Denetim (Claude'un kontrol noktası)

```bash
python orchestrator/review.py --task TASK-001
# → docs/reviews/REVIEW-{tarih}-TASK-001.md
# Kontroller: kontrat testleri, backend testleri, model alanları,
#             hata formatı, audit log, qa/ dokunulmazlığı
```

- `qa/contract/` — Claude'un bağımsız sözleşme testleri. **DeepSeek buraya yazamaz.**
- `qa/checklists/` — modül kabul kriterleri.
- Kontrat testleri çalışan backend ister: `BACKEND_URL=http://localhost:8000 pytest qa/contract`

## Tekrarlayan QA Job'u

- **Claude oturumdayken:** `/loop 30m` ile inbox + teslimat kontrolü.
- **Oturum dışı:** `.github/workflows/nightly-qa.yml` her gece testleri koşar ve
  `PROJECT_STATUS.md`'yi günceller.

## Cloud Ortam Notu (önemli)

Bu Claude Code cloud ortamında `api.deepseek.com` ağ allowlist'inde **kapalı**.
Tam otomasyon istiyorsanız: Claude Code web → environment ayarları → network
policy → `api.deepseek.com` ekleyin. Aksi halde manuel mod kullanılır.

## Dizin Haritası

| Yol | Sahip | İçerik |
|---|---|---|
| `backend/` | DeepSeek | FastAPI + PostgreSQL |
| `frontend/` | Claude | Next.js 14 + Tailwind + shadcn/ui |
| `qa/` | Claude | Bağımsız kontrat testleri + checklistler |
| `orchestrator/` | Claude | Görev gönderme + denetim araçları |
| `docs/` | Ortak | Talimatlar, review/bug raporları, screenshot'lar |
