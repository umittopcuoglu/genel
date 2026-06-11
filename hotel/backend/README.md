# HotelOps PMS Backend

AI destekli Otel Yönetim Sistemi backend'i. FastAPI, PostgreSQL, JWT, RBAC ve audit log altyapısı.

## Gereksinimler

- Docker & Docker Compose
- Python 3.11 (yerel geliştirme için)

## Kurulum ve Çalıştırma

1. **Docker Compose ile ayağa kaldır**

```bash
cd backend
docker compose up -d
```

2. **Migration'ları çalıştır**

```bash
docker compose exec api alembic upgrade head
```

3. **Seed verilerini ekle**

```bash
docker compose exec api python seed.py
```

4. **API'yi test et**

Sağlık kontrolü:

```bash
curl http://localhost:8000/api/v1/health
```

Login (superadmin):

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@hotelops.com","password":"Super123!"}'
```

## Yerel Geliştirme

1. Sanal ortam oluşturun:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

3. `.env` dosyasını `.env.example`'den kopyalayın ve düzenleyin.

4. Veritabanını başlatın (Docker'daki PostgreSQL):

```bash
docker compose up -d db redis
```

5. Migration'ları uygulayın:

```bash
alembic upgrade head
```

6. Seed verilerini ekleyin:

```bash
python seed.py
```

7. Uygulamayı çalıştırın:

```bash
uvicorn app.main:app --reload
```

## Testler

```bash
pytest -v
```

Testler, SQLite in-memory veya test veritabanı kullanır. Tüm testler bağımsızdır.

## API Dokümantasyonu

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Roller (RBAC)

- superadmin: Tüm yetkiler
- manager: Yönetim yetkileri
- frontdesk: Ön büro işlemleri
- housekeeping: Kat hizmetleri
- accounting: Muhasebe
- maintenance: Teknik servis
- fb: Yiyecek-içecek
- hr: İnsan kaynakları
- guest: Misafir (sınırlı erişim)

## Audit Log

Tüm POST/PUT/PATCH/DELETE istekleri `audit_logs` tablosuna kaydedilir. Her kayıt; kullanıcı, IP, payload ve zaman damgası içerir.

## Proje Yapısı

```
backend/
├── app/
│   ├── core/          # Konfigürasyon, DB, auth, RBAC, audit
│   ├── models/        # SQLAlchemy modelleri (base, user, audit)
│   ├── routers/       # API endpoint'leri (auth, health)
│   ├── schemas/       # Pydantic modelleri
│   └── main.py        # FastAPI uygulaması
├── migrations/        # Alembic migration dosyaları
├── tests/             # Pytest testleri
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── seed.py
└── README.md
```

## Notlar

- JWT access token süresi: 15 dakika, refresh token: 7 gün.
- Refresh token blacklist için Redis kullanılır (logout).
- Tüm modeller soft delete destekler (`deleted_at`).
- `created_by` ve `updated_by` alanları otomatik olarak token'daki kullanıcı ID'si ile doldurulur.

## Sorun Giderme

- Veritabanı bağlantı hatası: Docker container'larının çalıştığından emin olun (`docker compose ps`).
- Migration hatası: `alembic current` ile versiyonu kontrol edin, `alembic downgrade -1` ile geri alın.
- Token hataları: JWT_SECRET_KEY'in `.env` içinde tanımlandığından emin olun.
