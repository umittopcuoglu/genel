---
id: TASK-024
modül: Faz 4 - Mobile Check-in
kapsam: pasaport OCR + EGM bildirimi + yüz tanıma + QR kodu + mobil check-in flow
durum: kuyrukta (Faz 3 tamamlanınca)
tur: —
bağımlılık: TASK-001 (check-in), TASK-017 (KVKK/guest data), TASK-021 (computer vision)
---

# TASK-024 — Faz 4: Mobil Check-in — Pasaport OCR & EGM Bildirimi

> Misafir mobil app'ten pasaportunu scan et → OCR pasaport verisini çeksin → EGM'ye oto-bildir → check-in tamam. Yüz tanıma (optional).

## 1. Veri Modeli

### `ocr_document_scans` (taraşmış belge kayıtları)
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id)
- reservation_id (UUID FK → reservations.id)
- document_type (VARCHAR 30) — passport / national_id / visa / residence_permit
- document_image_url (VARCHAR 255, S3)
- ocr_extracted_data (JSON) — {firstname, lastname, passport_no, nationality, birth_date, issue_date, expiry_date, mrz_check}
- ocr_confidence (DECIMAL 5,2, default=0) — Tesseract + mrz_reader güven skoru
- manual_verified (BOOLEAN, default=false)
- verified_by (UUID FK → users.id nullable)
- corrections_applied (JSON nullable) — {field: "corrected_value"}
- status (VARCHAR 15, default="pending") — pending / verified / rejected
- rejection_reason (VARCHAR 200 nullable)
- Index: guest_id, reservation_id, status

### `egm_submissions` (Emniyet Genel Müdürlüğü — EGM bildirimleri)
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id)
- reservation_id (UUID FK → reservations.id)
- document_scan_id (UUID FK → ocr_document_scans.id)
- egm_submission_xml (LONGTEXT) — XML formatted EGM talep şablonu
- submission_status (VARCHAR 15, default="pending") — pending / submitted / acknowledged / rejected / error
- submission_timestamp (DATETIME nullable)
- egm_request_id (VARCHAR 100 nullable, EGM yanıt ID'si)
- error_message (VARCHAR 500 nullable)
- retry_count (INT, default=0)
- next_retry_at (DATETIME nullable)
- submission_logs (JSON array) — [{timestamp, status, message}]
- Index: guest_id, submission_status, reservation_id

### `checkin_sessions` (mobil check-in session'ları)
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id)
- reservation_id (UUID FK → reservations.id)
- session_token (VARCHAR 100, unique) — mobile app'te geçerlilik 24h
- qr_code (VARCHAR 500) — QR code base64 (session_token codlanmış)
- device_id (VARCHAR 100) — mobile device unique ID
- ip_address (VARCHAR 50)
- user_agent (VARCHAR 200)
- session_start (DATETIME)
- session_end (DATETIME nullable)
- checkin_completed_at (DATETIME nullable)
- session_status (VARCHAR 15, default="active") — active / completed / expired / cancelled
- steps_completed (JSON array) — ["identity_verification", "document_scan", "facial_recognition", "signature", "nfc_room_key"]
- Index: session_token, guest_id, session_status

### `facial_recognition_scans` (yüz tanıma — opsiyonel)
- id (UUID, PK) [BaseModel]
- checkin_session_id (UUID FK → checkin_sessions.id)
- guest_id (UUID FK → guests.id)
- face_image_url (VARCHAR 255, S3)
- passport_face_image_url (VARCHAR 255, S3) — pasaport fotoğrafından extracted
- face_match_score (DECIMAL 5,2 default=0) — 0-100 (DeepFace/FaceNet güven)
- face_match_status (VARCHAR 15, default="pending") — pending / match / no_match / inconclusive
- liveness_check_passed (BOOLEAN nullable) — blink test / head movement
- timestamp (DATETIME)
- Index: guest_id, face_match_status

### `nfc_room_keys` (NFC oda anahtarları — check-in sonrası)
- id (UUID, PK) [BaseModel]
- guest_id (UUID FK → guests.id)
- room_id (UUID FK → rooms.id)
- checkin_session_id (UUID FK → checkin_sessions.id nullable)
- key_code (VARCHAR 50, unique) — NFC card UID (encrypted)
- activation_time (DATETIME)
- deactivation_time (DATETIME nullable) — check-out'ta
- validity_start, validity_end (DATETIME) — konaklama tarihi aralığı
- access_count (INT, default=0)
- status (VARCHAR 15, default="active") — active / expired / revoked
- Index: guest_id, room_id, status

## 2. Endpoint'ler (Mobil API — /api/v1/mobile/)

### `POST /api/v1/mobile/checkin-session`
- Auth: Guest (reservation code + email)
- Body: { reservation_code, guest_email, device_id }
- İşlem: Reservation match → session oluştur → 24h token gen → QR code gen
- 201 döner { session_id, session_token, qr_code, steps_required: ["document_scan", "facial_recognition", "signature"] }

### `POST /api/v1/mobile/checkin/{session_id}/scan-document`
- Auth: session token
- Body: { document_image: "base64_or_url", document_type: "passport" }
- İşlem: Image → S3 upload → OCR (Tesseract + MRZ reader) → ocr_document_scans kaydı
- 200 döner { ocr_data: {firstname, lastname, passport_no, expiry_date}, confidence: 95.2, requires_manual_verification: false }

### `POST /api/v1/mobile/checkin/{session_id}/facial-recognition`
- Auth: session token
- Body: { face_image: "base64", liveness_check: true/false }
- İşlem: Image → S3 → DeepFace'e gönder (mock) → face comparison (passport photo ile) → score
- 200 döner { match_score: 87.5, status: "match" / "no_match" / "inconclusive", liveness_passed: true }

### `POST /api/v1/mobile/checkin/{session_id}/verify-egm`
- Auth: session token
- Body: { manual_corrections?: {field: "value"} }
- İşlem: OCR data'yı verify et → EGM XML form'unu doldur → EGM submission kuyruğuna ekle
- 200 döner { egm_status: "pending", estimated_time: "15 minutes", submission_id }

### `POST /api/v1/mobile/checkin/{session_id}/complete`
- Auth: session token
- Body: { signature_image?: "base64" }
- İşlem: Tüm steps completed mi kontrol → check-in transaction (TASK-001) → NFC key generate → session completed
- 200 döner { room_key_token, access_code, access_instructions, check_in_confirmation }

### `GET /api/v1/mobile/checkin/{session_id}/status`
- Auth: session token / guest
- 200 döner { session: {...}, steps_completed: [...], pending_steps: [...], egm_status, errors: [] }

### `POST /api/v1/mobile/checkin/{session_id}/accept-terms`
- Auth: session token
- Body: { consent_video: true, privacy_policy: true, photo_usage: true }
- 200 döner { accepted_at, next_step }

## 3. İş Mantığı

1. **Session başlatma:**
   - Misafir mobil app'te check-in yap → reservation code + email → backend doğrula
   - checkin_sessions kaydı (status=active, 24h TTL)
   - QR code generate (session_token + reservation_id + timestamp'i encode)

2. **Pasaport scan:**
   - Image file S3'e async upload
   - Tesseract OCR + MRZ (Machine Readable Zone) reader → JSON
   - Güven skoru < 80 → requires_manual_verification=true
   - ocr_document_scans kaydı (pending)

3. **EGM bildirimi:**
   - OCR data'yı Turkey EGM XML schema'ya map et (Gümrük Bakanlığı standardı)
   - egm_submissions kaydı (pending) → scheduled job'a
   - Async: XML'i EGM API'sine gönder (mock-first), retry with exponential backoff

4. **Yüz tanıma (opsiyonel):**
   - Misafir canlı fotoğraf çekmesi
   - Liveness check: blink/head movement (mock: random true)
   - Pasaport yüzü OCR'dan extract → DeepFace karşılaştırması
   - Score > 70 ise match, 50-70 inconclusive, < 50 no_match

5. **Check-in completion:**
   - Tüm steps verified → check-in transaction (rooms, reservations, folios update TASK-001)
   - NFC room key generate: key_code (random 50-char) → kripte → nfc_room_keys kaydı
   - validity_end = checkout_date
   - Guest mobile'e push notification + key_code + room number

6. **EGM retry:**
   - submission_status=error ise cron job 1h sonra retry
   - retry_count >= 3 ise manual escalation (manager notification)

7. **Audit & security:**
   - Tüm step'ler checkin_sessions.steps_completed array'ine log
   - IP + device_id + user_agent tracking (fraud detection)
   - Session token 24h validity (security)

8. **Test ortamında:**
   - OCR mock: hardcoded pasaport data
   - EGM submission mock: instant success (accepted)
   - Face recognition mock: random score 75-95
   - NFC key mock: fixed code

## 4. Minimum Test Sayısı

- [ ] 6 unit test (`test_mobile_checkin.py`):
  - Session creation + token generation
  - OCR mock (confidence score)
  - EGM XML generation
  - Face matching logic
  - NFC key generation
  - Step tracking

- [ ] 5 integration test (`test_mobile_checkin_e2e.py`):
  - Full checkin flow (session → document → facial → completion)
  - EGM submission async job
  - Room key access (mock door lock)
  - Session expiry (24h TTL)
  - Fraud detection (IP/device anomaly)

- [ ] 2 load test:
  - 20 concurrent checkin sessions
  - OCR processing 50 images < 5s each

## 5. Acceptance Criteria

- [ ] Session token 24h validity
- [ ] OCR mock (Tesseract output emulation)
- [ ] MRZ (Machine Readable Zone) parser
- [ ] EGM XML schema implementation (Gümrük standart)
- [ ] EGM async submission + retry logic
- [ ] Facial recognition mock (DeepFace output emulation)
- [ ] Liveness check mock
- [ ] NFC room key generation + validity range
- [ ] Check-in completion (TASK-001 entegre)
- [ ] Session audit log (steps_completed tracking)
- [ ] Tüm endpoint'ler RBAC + hata zarfı
- [ ] Signature capture (opsiyonel, test'te mock)
- [ ] OpenAPI Türkçe
- [ ] pytest backend/tests yeşil

---

## 6. Teslim Dosyaları

### FILE: hotel/backend/app/models/mobile_checkin.py
```python
# Mobile checkin + OCR + EGM + face recognition models
```

### FILE: hotel/backend/app/routers/mobile_checkin.py
```python
# Mobile checkin endpoints
```

### FILE: hotel/backend/app/services/mobile_checkin_service.py
```python
# Checkin session + EGM orchestration
```

### FILE: hotel/backend/integrations/ocr/base.py
```python
# Abstract OCR adapter
```

### FILE: hotel/backend/integrations/ocr/tesseract_service.py
```python
# Tesseract + MRZ parser mock
```

### FILE: hotel/backend/integrations/face/deepface_service.py
```python
# Facial recognition mock (DeepFace output)
```

### FILE: hotel/backend/integrations/egm/egm_service.py
```python
# EGM XML builder + async submission
```

### FILE: hotel/backend/migrations/versions/0NN_add_mobile_checkin.py
```python
# Migration: ocr_document_scans, egm_submissions, checkin_sessions, facial_recognition_scans, nfc_room_keys
```

### FILE: hotel/backend/tests/test_modules/test_mobile_checkin.py
```python
# Unit + integration + load tests
```
