# HotelOps — Lokal Çalıştırma Rehberi

Bu rehber projeyi kendi bilgisayarında (Windows / macOS / Linux) çalıştırmanı sağlar.
İki parça vardır: **Backend** (FastAPI · port 8000) ve **Frontend** (Next.js · port 3000).

## Gereksinimler
- **Python 3.11+** (`python --version`)
- **Node.js 18+** ve npm (`node --version`)
- Git
- Veritabanı: varsayılan **SQLite** (kurulum gerektirmez). PostgreSQL şart değil.

---

## 0) Projeyi indir

```bash
git clone https://github.com/umittopcuoglu/genel.git
cd genel
git checkout claude/ecstatic-gates-paa35d
```

---

## 1) Backend (FastAPI · http://localhost:8000)

```bash
cd hotel/backend

# Sanal ortam (önerilir)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt

# Veritabanı tablolarını oluştur (SQLite dev.db)
python init_db.py

# Örnek kullanıcıları ekle (9 rol)
python seed.py

# Sunucuyu başlat
python -m uvicorn app.main:app --reload --port 8000
```

Açılınca:
- API: http://localhost:8000
- **Swagger dokümanı:** http://localhost:8000/api/v1/docs

> Not: `requirements.txt` `bcrypt==4.0.1` içerir (passlib uyumu). Eğer parola
> hatası alırsan `pip install "bcrypt==4.0.1"` çalıştır.

### Örnek giriş bilgileri (seed.py'den)
| Rol | E-posta | Şifre |
|-----|---------|-------|
| superadmin | superadmin@hotelops.com | Super123! |
| manager | manager@hotelops.com | Manager123! |
| frontdesk | frontdesk@hotelops.com | Front123! |
| housekeeping | housekeeping@hotelops.com | House123! |
| accounting | accounting@hotelops.com | Acc123! |
| maintenance | maintenance@hotelops.com | Main123! |
| fb | fb@hotelops.com | FB123! |
| hr | hr@hotelops.com | HR123! |
| guest | guest@hotelops.com | Guest123! |

### Testleri çalıştırmak (opsiyonel)
```bash
python -m pytest -q
```
Beklenen: **201 passed**.

---

## 2) Frontend (Next.js · http://localhost:3000)

**Yeni bir terminal** aç (backend açık kalsın):

```bash
cd hotel/frontend

# Bağımlılıklar
npm install

# Backend adresini ayarla (.env.local)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Geliştirme sunucusu
npm run dev
```

Tarayıcıda aç: **http://localhost:3000**
- Giriş ekranı: yukarıdaki bilgilerle giriş yap (backend kapalıysa demo moduna düşer).
- Sol menüden tüm modül ekranlarına ulaşabilirsin (24 sayfa).

---

## Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|-------|-------|
| `bcrypt` / parola hatası | `pip install "bcrypt==4.0.1"` |
| `cryptography` Rust hatası | `pip install --upgrade cryptography` |
| Port 8000 dolu | `--port 8001` ile başlat, frontend `.env.local`'i güncelle |
| Frontend "Mock veri" rozeti | Şimdilik ekranlar mock veri gösteriyor; canlı API bağlama bir sonraki adım |
| Tabloları sıfırla | `dev.db` dosyasını sil, `python init_db.py && python seed.py` |

---

## Mimari özet
- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2 + JWT/RBAC. 25 modül, 201 test.
- **Frontend:** Next.js 14 (App Router) + TypeScript + TailwindCSS. 24 sayfa, açık/koyu tema.
- **Veritabanı:** SQLite (varsayılan) · PostgreSQL'e `.env` ile geçilebilir.
