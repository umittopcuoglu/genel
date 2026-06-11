---
id: TASK-006
modül: Altyapı & DevOps (WebSocket + E2E + Docker + CI/CD)
kapsam: WebSocket real-time + Playwright E2E + prod Docker Compose + GitHub Actions
durum: kuyrukta (TASK-003 ile paralel gönderilebilir)
tur: —
bağımlılık: TASK-002 (front_office router'daki WebSocket TODO'ları)
---

# TASK-006 — Altyapı & DevOps

> Bu görev modül değil; tüm modülleri ayakta tutan altyapı. WebSocket gerçek-zamanlı
> güncellemeler, uçtan uca testler, prod-hazır konteynerleme ve sürekli entegrasyon.
> Mevcut: `backend/Dockerfile`, `backend/docker-compose.yml` (db+redis+api),
> `.github/workflows/{backend-ci,frontend-ci,nightly-qa}.yml`. Bunları GENİŞLET, bozma.

---

## 1. WebSocket Gerçek-Zamanlı Altyapı

### 1.1 Bağlantı yöneticisi — `backend/app/ws/manager.py`
- `ConnectionManager` sınıfı: aktif WebSocket bağlantılarını yönetir
  - `connect(websocket, user_id, role)` — bağlantıyı kaydet
  - `disconnect(websocket)` — bağlantıyı kaldır
  - `broadcast(event: dict)` — tüm bağlı istemcilere yayınla
  - `broadcast_to_roles(event, roles: list)` — belirli rollere yayınla (örn. sadece housekeeping)
- Redis Pub/Sub ile çoklu worker desteği (uvicorn --workers N): bir worker'da emit edilen olay
  Redis kanalı `hotelops:events` üzerinden diğer worker'lara dağıtılır.

### 1.2 WebSocket endpoint — `backend/app/ws/routes.py`
- `WS /api/v1/ws?token=JWT` — JWT query param ile auth (header WS'te zor)
  - Token geçersiz → 1008 policy violation ile kapat
  - Bağlantı sonrası `{"type": "connected", "user_id": "..."}` gönder
- `WS /api/v1/ws/housekeeping?token=JWT` — sadece housekeeping/manager rolü; oda görev push'u

### 1.3 Olay yayıncısı — `backend/app/ws/events.py`
- `emit_room_status_changed(room_id, room_no, old_status, new_status)` →
  `{"type": "room.status.changed", "data": {...}, "ts": "ISO"}`
- `emit_reservation_created(reservation)` → `{"type": "reservation.created", ...}`
- `emit_checkin(reservation_id, room_no)` / `emit_checkout(...)`
- `emit_housekeeping_task(task)` → housekeeping rolüne push

### 1.4 Mevcut endpoint'lere entegrasyon (TASK-002 revizyonu — TAM dosya gönder)
- `front_office.py`: check-in/check-out/room-status-patch sonrası ilgili `emit_*` çağrısı
- TODO yorumları gerçek emit çağrılarıyla değiştirilir

### 1.5 Testler — `backend/tests/test_ws.py`
- WS bağlantı + auth happy (geçerli token bağlanır)
- Geçersiz token → kapanış (1008)
- room.status.changed emit → bağlı istemci olayı alır (httpx/websockets test client)
- RBAC: housekeeping WS'e guest rolü bağlanamaz

---

## 2. Playwright E2E Testleri (docs/04 Doğrulama Döngüsü)

### 2.1 Kurulum — `qa/e2e/`
```
qa/e2e/
├── playwright.config.ts      # baseURL, 4 proje: chromium-light, chromium-dark, mobile-light, mobile-dark
├── package.json              # @playwright/test
├── fixtures/auth.ts          # login helper (token localStorage'a yazar)
├── tests/
│   ├── login.spec.ts
│   ├── front-office.spec.ts  # arrivals/departures/in-house/rooms/tape-chart sekmeleri
│   └── smoke.spec.ts         # her ana sayfa 200 + ekran görüntüsü
└── screenshots/              # baseline görseller (4 varyant)
```

### 2.2 Test senaryoları
- **login.spec.ts:** geçersiz parola hata gösterir; geçerli giriş dashboard'a yönlendirir
- **front-office.spec.ts:**
  - 5 sekme (Gelenler/Gidenler/Konaklayanlar/Oda Panosu/Tape Chart) tıklanır, içerik render olur
  - Oda Panosu filtre butonları çalışır (temiz/kirli/dolu)
  - Tape Chart hafta kaydırma (← 7 gün / 7 gün →) çalışır
  - Her sekmede `toHaveScreenshot()` baseline karşılaştırması
- **smoke.spec.ts:** /dashboard, /front-office sayfaları yüklenir, console error yok
- **Erişilebilirlik:** her testte `@axe-core/playwright` ile a11y taraması (kritik ihlal = fail)

### 2.3 Mock backend modu
- Backend ayakta değilse: Playwright `route.fulfill()` ile API yanıtlarını mock'lar
- `fixtures/mock-api.ts`: arrivals/departures/rooms için sabit JSON döndürür
- Böylece E2E backend olmadan da CI'da koşar (görsel regresyon için yeterli)

---

## 3. Prod-Hazır Docker Compose

### 3.1 Frontend Dockerfile — `frontend/Dockerfile`
- Multi-stage: `node:20-alpine` build → `next build` → standalone output
- Runtime: minimal image, `next start` veya standalone server, port 3000
- `.dockerignore`: node_modules, .next, .git

### 3.2 Prod compose — `docker-compose.prod.yml` (hotel/ kökünde)
- Servisler: `db` (postgres:15), `redis`, `api` (backend), `web` (frontend), `nginx` (reverse proxy)
- `api`: --workers 4, --reload YOK, env_file ile secrets
- `web`: NEXT_PUBLIC_API_URL=http://api:8000, build frontend/
- `nginx`: 80/443 → web (/, statik) + api (/api, /api/v1/ws WebSocket upgrade header'ları)
  - `nginx/default.conf`: `proxy_set_header Upgrade $http_upgrade; Connection "upgrade"` (WS için)
- Healthcheck'ler + `restart: unless-stopped`
- Named volumes: postgres_data, redis_data

### 3.3 Env şablonu — `hotel/.env.prod.example`
- DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET, CORS_ORIGINS
- Yorum: "production'da gerçek secret'larla doldur, asla commit etme"

---

## 4. GitHub Actions CI/CD Genişletme

### 4.1 `e2e-ci.yml` (YENİ)
- Trigger: frontend/ veya qa/e2e/ değişiminde
- `npm ci` + `npx playwright install --with-deps chromium`
- `next build` + `next start` arka planda → Playwright koş (mock API modu)
- Görsel regresyon başarısızsa diff'leri artifact olarak yükle

### 4.2 `docker-ci.yml` (YENİ)
- Trigger: Dockerfile veya docker-compose değişiminde
- `docker compose -f docker-compose.prod.yml build` (smoke: image'lar derleniyor mu)
- `docker compose up -d` + `curl http://localhost/api/v1/health` → 200 beklenir, sonra `down`

### 4.3 `backend-ci.yml` (GENİŞLET — TAM dosya gönder)
- PostgreSQL service container ekle (gerçek DB ile entegrasyon testi)
- `alembic upgrade head` migration testi
- WebSocket testleri (`test_ws.py`) dahil

### 4.4 Branch koruması notu
- README'ye not: main branch'e merge için tüm CI yeşil olmalı (kullanıcı GitHub Settings'ten ayarlar)

---

## 5. Teslim dosyaları
```
### FILE: backend/app/ws/__init__.py
### FILE: backend/app/ws/manager.py
### FILE: backend/app/ws/routes.py
### FILE: backend/app/ws/events.py
### FILE: backend/app/routers/front_office.py     (WS emit entegrasyonu — TAM dosya)
### FILE: backend/app/main.py                      (WS router + Redis pubsub başlatma — TAM dosya)
### FILE: backend/tests/test_ws.py
### FILE: frontend/Dockerfile
### FILE: frontend/.dockerignore
### FILE: hotel/docker-compose.prod.yml
### FILE: hotel/nginx/default.conf
### FILE: hotel/.env.prod.example
### FILE: qa/e2e/package.json
### FILE: qa/e2e/playwright.config.ts
### FILE: qa/e2e/fixtures/auth.ts
### FILE: qa/e2e/fixtures/mock-api.ts
### FILE: qa/e2e/tests/login.spec.ts
### FILE: qa/e2e/tests/front-office.spec.ts
### FILE: qa/e2e/tests/smoke.spec.ts
### FILE: .github/workflows/e2e-ci.yml
### FILE: .github/workflows/docker-ci.yml
### FILE: .github/workflows/backend-ci.yml          (PostgreSQL + alembic + WS — TAM dosya)
```

> NOT: `.github/workflows/` repo kökündedir (hotel/ değil). Yollar buna göre.
> `qa/e2e/` Claude'un alanıdır ama bu altyapı görevinde DeepSeek yazabilir — istisna onaylandı.

## 6. Kabul kriterleri
- `backend/tests/test_ws.py` yeşil (WS bağlantı + auth + emit + RBAC)
- `front_office.py` artık gerçek `emit_*` çağrıları içerir (TODO kalmamış)
- `docker compose -f docker-compose.prod.yml build` hatasız (5 servis)
- `nginx/default.conf` WebSocket upgrade header'ları içerir
- Playwright config 4 proje (light/dark × desktop/mobile) tanımlar
- 3 yeni workflow geçerli YAML; mevcut 3 workflow bozulmamış
- review.py PASS (model/audit/hata-formatı/qa-dokunulmazlığı uyarısı kabul)
- OpenAPI Türkçe (WS endpoint'leri için açıklama)
