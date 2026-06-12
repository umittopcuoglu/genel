---
id: TASK-021
modül: Faz 4 - Computer Vision
kapsam: oda kalite kontrolü + hasar tespiti + temizlik doğrulama + CV pipeline
durum: kuyrukta (Faz 3 tamamlanınca)
tur: —
bağımlılık: TASK-005 (housekeeping), TASK-015 (maintenance work orders)
---

# TASK-021 — Faz 4: Computer Vision — Oda Kalite Kontrol

> AI-destekli görüntü analizi ile ev temizliğinin kalitesini otomatik doğrula, hasar tespiti, inventori gözleme.

## 1. Veri Modeli

### `room_inspections` (CV tabanlı denetimler)
- id (UUID, PK) [BaseModel]
- room_id (UUID FK → rooms.id)
- inspection_type (VARCHAR 20) — post_checkout / pre_checkin / maintenance / damage_report
- inspector_user_id (UUID FK → users.id)
- photo_urls (JSON array, S3 paths)
- cv_analysis (JSON) — {defects: [{area, type, severity, confidence}], occupancy_score, cleanliness_score, inventory_status}
- defects_found_count (INT, default=0)
- status (VARCHAR 15, default="pending") — pending / completed / flagged / resolved
- flagged_reason (VARCHAR 200 nullable) — hasar/eksik eşya
- resolved_date (DATETIME nullable)
- Index: room_id, inspection_type, status

### `cv_models`
- id (UUID, PK) [BaseModel]
- model_name (VARCHAR 50) — yolov8_damage, yolov8_cleanliness, inventory_detector
- model_version (VARCHAR 20) — 1.0.0, 2.0.0
- endpoint_url (VARCHAR 255) — ML servis URL (mock-first)
- accuracy_score (DECIMAL 5,2) — son test accuracy
- last_trained_date (DATE nullable)
- status (VARCHAR 15, default="active") — active / archived / training
- Index: model_name, status

### `inspection_defects` (CV bulduğu sorunlar)
- id (UUID, PK) [BaseModel]
- inspection_id (UUID FK → room_inspections.id)
- defect_type (VARCHAR 30) — stain / crack / broken_item / missing_item / odor
- location (VARCHAR 100) — bathroom, bedroom, carpet, wall
- severity (VARCHAR 15, default="minor") — minor / moderate / severe
- cv_confidence (DECIMAL 5,2) — 0-100 (model güven skoru)
- photo_url (VARCHAR 255 nullable, S3)
- manual_verified (BOOLEAN, default=false)
- verified_by (UUID FK → users.id nullable)
- action_taken (VARCHAR 200 nullable)
- resolved_at (DATETIME nullable)
- Index: inspection_id, defect_type, severity

### `inventory_snapshots`
- id (UUID, PK) [BaseModel]
- room_id (UUID FK → rooms.id)
- inspection_id (UUID FK → room_inspections.id nullable)
- inventory_items (JSON) — {item_name: expected_count, detected_count, status}
- photo_evidence (JSON array, S3 paths)
- discrepancies_found (INT, default=0)
- created_at (auto)
- Index: room_id, created_at

## 2. Endpoint'ler

### `POST /api/v1/rooms/{room_id}/inspections/start-cv`
- Auth: housekeeping, maintenance, manager
- Body: { inspection_type, photo_urls (base64 array or S3 URLs) }
- İşlem: Photo'ları S3'e yükle → CV pipeline'a gönder (async job) → `cv_models` seç
- 202 döner inspection kaydı (status=pending, job_id)

### `GET /api/v1/rooms/{room_id}/inspections/{id}/cv-results`
- Auth: housekeeping, manager
- 200 döner { defects: [{type, location, severity, confidence, photo}], cleanliness_score, occupancy_score, inventory_status, errors: [] }
- 202 job hala çalışıyorsa (status=pending)

### `POST /api/v1/inspections/{id}/defects/{defect_id}/verify`
- Auth: manager, maintenance
- Body: { manual_verified, action_taken? }
- Defect'i doğrula/düzelt → inspection status → work_order auto-create (TechCare TASK-015)

### `GET /api/v1/cv/models`
- Auth: manager, superadmin
- 200 döner { models: [{name, version, accuracy, status, last_trained}] }

### `POST /api/v1/cv/models/{model_id}/retrain`
- Auth: superadmin
- Body: { training_data_set_id, target_accuracy }
- Async task başlat (ML retraining)

### `GET /api/v1/rooms/{room_id}/inventory-check`
- Auth: housekeeping, manager
- 200 döner { expected_items: {...}, latest_snapshot: {...}, discrepancies: [{item, missing_count}] }

## 3. İş Mantığı

1. **Inspection başlatma:**
   - Fotoğraf dizisi POST'lanır (base64 + filename)
   - Her fotoğraf S3'e async yüklenir, encryption
   - Yükleme bittiğinde CV pipeline'a gönder (job queue — Celery/AWS Lambda mock)

2. **CV analiz pipeline (mock-first adapter):**
   - `integrations/cv/base.py` (abstract)
   - `integrations/cv/yolov8_service.py` (mock: random defects + confidence scores)
   - Çıktı: JSON {defects: [...], cleanliness_score: 65-95, occupancy_detected: true/false}

3. **Hasar bulunca:**
   - Defect otomatik `inspection_defects` kaydına
   - Severity=severe ise manager WS notification + work_order (TASK-015) auto-create
   - Photo evidence S3 URL kaydedilir

4. **Envanteri kontrol:**
   - Room setup'ındaki expected items (bed, towels, amenities...)
   - CV snapshot'ı beklenen sayıyla karşılaştır
   - Eksik item → notification + "restock required" folio ile HK task'a

5. **Test ortamında (`ENABLE_LLM_MOCK=true`):**
   - CV servis mock: random {defects: 2-4, cleanliness_score: 70-92, inventory_discrepancy: 10%}
   - Tüm async joblar sync mock'a

6. **Model yönetimi:**
   - Accuracy tracking, version control
   - Retrain endpoint (mock: immediate success)

## 4. Minimum Test Sayısı

- [ ] 5 unit test (`test_cv_models.py`):
  - Model listesi fetch
  - Inspection başlat + async job oluştur
  - Hasar doğrulama
  - Envanteri karşılaştırma
  - Mock CV sonucu parse et

- [ ] 3 integration test (`test_room_inspections_e2e.py`):
  - Fotoğraf upload → CV sonuç + defect kaydı
  - Severity=severe → WS notification + work order (TASK-015 mock)
  - Envanteri eksiklik tespit

- [ ] 2 performance test:
  - Defect doğrulama < 100ms
  - Inspection sorgusu (10 odanın 30 gün geçmişi) < 500ms

## 5. Acceptance Criteria

- [ ] CV pipeline async (job queue mock), inspection durumu polling ile
- [ ] Hasar bulunca manager WS bildir (WebSocket TASK-006)
- [ ] S3 upload mock (local temp dir test'te)
- [ ] Envanteri discrepancy otomatik HK task'ı trigger et
- [ ] Defect doğrulama adımı (manual_verified flag)
- [ ] CV model yönetimi (version, accuracy, status)
- [ ] Tüm endpoint'ler RBAC + hata zarfı (error: {code, message, details})
- [ ] OpenAPI açıklamaları Türkçe
- [ ] Mock-first: `integrations/cv/yolov8_service.py` mock döner realistic defects
- [ ] pytest backend/tests yeşil

---

## 6. Teslim Dosyaları

### FILE: hotel/backend/app/models/cv.py
```python
# CV inspection + defect models
```

### FILE: hotel/backend/app/routers/cv_inspections.py
```python
# CV inspection endpoints
```

### FILE: hotel/backend/app/services/cv_service.py
```python
# CV pipeline orchestration
```

### FILE: hotel/backend/integrations/cv/base.py
```python
# Abstract CV adapter
```

### FILE: hotel/backend/integrations/cv/yolov8_service.py
```python
# Mock YOLOv8 implementation
```

### FILE: hotel/backend/migrations/versions/0NN_add_cv_inspection.py
```python
# Migration: cv_inspections, cv_models, inspection_defects, inventory_snapshots
```

### FILE: hotel/backend/tests/test_modules/test_cv_inspections.py
```python
# Unit + integration tests
```
