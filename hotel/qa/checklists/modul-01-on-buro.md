# Modül 1 (Ön Büro) — Kabul Checklisti

> Claude bu listeyi review sırasında işaretler. Tamamı ✅ olmadan modül kapanmaz.

## Backend (DeepSeek teslimatı)
- [ ] `POST /api/v1/checkin/{reservation_id}` — 200'de folio oluşuyor, oda occupied
- [ ] `POST /api/v1/checkout/{reservation_id}` — bakiye sıfır değilse 409 + hata zarfı
- [ ] `GET /api/v1/arrivals?date=` — {data, meta} zarfı, tarih filtresi çalışıyor
- [ ] `GET /api/v1/departures?date=` — aynı zarf
- [ ] `GET /api/v1/in-house?date=` — aynı zarf
- [ ] `GET /api/v1/rooms?status=&type=&floor=` — filtreler çalışıyor
- [ ] `PATCH /api/v1/rooms/{id}/status` — geçersiz durum 422
- [ ] `POST /api/v1/room-assign` — otomatik + manuel mod
- [ ] `GET /api/v1/guests/{id}/history`
- [ ] `POST /api/v1/traces` + `PATCH /api/v1/traces/{id}/resolve`
- [ ] Tüm tablolarda UUID id + timestamps + soft delete
- [ ] Tüm yazma işlemleri audit_log'da
- [ ] RBAC: housekeeping rolü check-in YAPAMAZ (403)
- [ ] Her endpoint için 1 happy + 1 error pytest testi
- [ ] OpenAPI'de Türkçe summary/description

## Frontend (Claude teslimatı)
- [ ] Tape Chart: 14 gün görünümü, drag-drop, hover popover
- [ ] Arrivals / Departures / In-House listeleri
- [ ] Check-in akışı ≤ 3 tıklama
- [ ] Loading / empty / error state'leri mevcut
- [ ] Light + dark tema, mobil + desktop
- [ ] axe-core erişilebilirlik taraması temiz
- [ ] Playwright screenshot baseline'ları alındı (4 varyant)

## Entegrasyon
- [ ] WebSocket `room.status.changed` eventi UI'ı güncelliyor
- [ ] API p95 < 300ms (review raporunda ölçüm)
