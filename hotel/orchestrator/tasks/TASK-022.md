---
id: TASK-022
modül: Faz 4 - Voice Control
kapsam: Alexa + Google Assistant entegrasyonu + sesli komut işleme + multi-lingual
durum: kuyrukta (Faz 3 tamamlanınca)
tur: —
bağımlılık: TASK-002 (rooms), TASK-007 (AI agents), TASK-020 (IoT devices)
---

# TASK-022 — Faz 4: Sesli Kontrol — Alexa / Google for Hospitality

> "Alexa, oda ısısını 22 dereceye ayarla" / "Google, ışıkları kıs" — Misafir + resepsiyon sesli komut desteği.

## 1. Veri Modeli

### `voice_integrations`
- id (UUID, PK) [BaseModel]
- integration_type (VARCHAR 30) — alexa / google / siri (ileride)
- api_key (VARCHAR 255, encrypted + .env referans)
- skill_id / project_id (VARCHAR 100)
- status (VARCHAR 15, default="active") — active / testing / disabled
- webhook_endpoint (VARCHAR 255) — SMS'de misafir'e gönderilen entegrasyon URL
- supported_languages (JSON array) — ["tr", "en", "ru"]
- last_tested_at (DATETIME nullable)
- Index: integration_type, status

### `voice_commands`
- id (UUID, PK) [BaseModel]
- command_text (VARCHAR 200) — "oda ısısını 22 dereceye ayarla"
- command_type (VARCHAR 30) — iot_control / service_call / room_query / folio_info
- intent (VARCHAR 50) — set_temperature / dim_lights / call_concierge / check_balance / book_service
- language (VARCHAR 5, default="tr") — tr / en / ru
- required_params (JSON) — {param_name: "value_or_slot_name"}
- response_template (VARCHAR 255) — "Oda ısısı {{value}} olarak ayarlandı"
- context_aware (BOOLEAN, default=false) — previous command referansı gerekli mi
- allow_guest_access (BOOLEAN, default=true) — misafir kullanabilir mi
- min_confidence_threshold (DECIMAL 5,2, default=0.85) — NLU güven eşiği
- Index: intent, command_type

### `voice_sessions`
- id (UUID, PK) [BaseModel]
- user_id (UUID FK → users.id nullable, misafir) / guest_device_id (VARCHAR 100 nullable, anonim cihaz)
- integration_type (VARCHAR 30)
- device_id (VARCHAR 100) — Alexa device_id / Google Home device_id
- session_start (DATETIME)
- session_end (DATETIME nullable)
- language_detected (VARCHAR 5)
- commands_count (INT, default=0)
- status (VARCHAR 15, default="active") — active / closed / error
- Index: user_id, device_id, status

### `voice_interactions` (her komut)
- id (UUID, PK) [BaseModel]
- session_id (UUID FK → voice_sessions.id)
- command_id (UUID FK → voice_commands.id nullable, matched)
- raw_audio_transcript (VARCHAR 500) — STT output
- intent_detected (VARCHAR 50)
- slots (JSON) — {"temperature": "22", "duration": "10 minutes"}
- nlu_confidence (DECIMAL 5,2, default=0) — intent matching confidence
- action_taken (VARCHAR 200 nullable)
- result_status (VARCHAR 15, default="pending") — pending / success / failed / clarification_needed
- error_details (VARCHAR 200 nullable)
- tts_response (VARCHAR 500) — sesli yanıt metni
- response_audio_url (VARCHAR 255 nullable, S3)
- execution_time_ms (INT nullable)
- created_at (auto)
- Index: session_id, intent_detected, result_status

### `voice_intents_mapping`
- id (UUID, PK) [BaseModel]
- intent_name (VARCHAR 50) — set_temperature / dim_lights
- iot_command (VARCHAR 100) — device_type + action (e.g., "thermostat.set_temperature")
- api_endpoint (VARCHAR 255 nullable) — POST /api/v1/iot/device/{id}/set
- service_integration (VARCHAR 50 nullable) — room_service / concierge / maintenance
- requires_confirmation (BOOLEAN, default=false) — kullanıcıdan onay gerekli mi
- max_execution_time_ms (INT, default=5000)
- fallback_response (VARCHAR 200) — başarısızsa "Üzgünüm, şu anda bu işlem yapamıyorum"
- Index: intent_name

## 2. Endpoint'ler

### `POST /api/v1/voice/webhook/alexa`
- Auth: (AWS IAM signature verification)
- Body: Alexa request (intent, slots, session_id, device_id, user_id)
- İşlem: intent parse → voice_interactions kaydı → action execute → TTS yanıt → S3 audio URL
- 200 döner { response: "Oda ısısı 22°C olarak ayarlandı", audio_url: "...", session_token }

### `POST /api/v1/voice/webhook/google`
- Auth: (Google OAuth token verification)
- Body: Google Assistant request (intent, parameters, conversation_id)
- 200 döner { fulfillment_text, audio, suggestions: [] }

### `GET /api/v1/voice/commands`
- Auth: manager, superadmin
- Query: ?intent=set_temperature&language=tr
- 200 döner { commands: [{id, text, intent, params, response_template}] }

### `POST /api/v1/voice/commands/{command_id}/test`
- Auth: manager
- Body: { slots_test: {param: "value"} }
- İşlem: Komut template'ini slots'la test et (IoT mock'a gönder)
- 200 döner { execution_result: {...}, response: "..." }

### `GET /api/v1/voice/sessions/{session_id}/history`
- Auth: user (kendi session'ı), manager, superadmin
- 200 döner { session: {...}, interactions: [{transcript, intent, result, timestamp}], total_commands }

### `POST /api/v1/voice/integrations/{type}/test-connection`
- Auth: superadmin
- Body: {} (test webhook'u trigger et)
- 200 döner { status: "connected", device_count: 5, latency_ms: 150 }

### `PATCH /api/v1/voice/commands/{command_id}`
- Auth: manager, superadmin
- Body: { response_template, min_confidence_threshold, allow_guest_access }
- 200 döner güncellenen komut

## 3. İş Mantığı

1. **Webhook alış (Alexa/Google):**
   - AWS/Google imza doğrula
   - `voice_sessions` kaydı create/reuse
   - Intent + slots parse

2. **Intent matching:**
   - `voice_commands` tablosunda intent ara
   - NLU confidence >= min_threshold ise devam
   - Aksi halde clarification_needed (TTS: "Anlaşılamadı, tekrar söyler misiniz?")

3. **Action execution (IoT/Service call):**
   - Intent ↔ IoT cihaz mapping (`voice_intents_mapping`)
   - requires_confirmation=true ise → TTS: "Bunu onaylıyor musunuz? (1=Evet, 2=Hayır)"
   - Evet ise TASK-020 IoT endpoint'ini çağır (device_id, action, params)
   - IoT response (success/timeout/error) kaydedilir

4. **TTS response:**
   - response_template'i slots'la doldur
   - `integrations/voice/tts_service.py` (Google Cloud TTS mock) → S3 audio
   - response_audio_url ile döndür

5. **Service call'lar:**
   - call_concierge → resepsiyon WS notification
   - book_service → room_service folio item auto-create
   - check_balance → guest folio.balance

6. **Audit log:**
   - Tüm interactions kaydedilir (session'lar 30 gün tutulur)
   - Sensible data (klima ayarları, folio balance) PII mask'a gökere (TASK-001 audit)

7. **Multi-language:**
   - Intent'ler language-agnostic (slot names sabit)
   - Response template'leri language field'ı ile store
   - Gerçek ortamda: Google Translate API mock-first

8. **Test ortamında:**
   - Alexa/Google webhook'u mock: random intent + confidence
   - IoT control: instant success, instant TTS
   - Audio generation: mock base64 WAV data

## 4. Minimum Test Sayısı

- [ ] 6 unit test (`test_voice_commands.py`):
  - Intent matching + confidence threshold
  - Slots extraction
  - Response template fill
  - Confirmation flow
  - TTS mock URL generation
  - Service call intent (room_service, concierge)

- [ ] 4 integration test (`test_voice_webhook_e2e.py`):
  - Alexa webhook → IoT command (TASK-020) → TTS → response
  - Google Assistant webhook → service call (folio post) → response
  - Multi-language (tr/en) command processing
  - Clarification flow (low confidence)

- [ ] 2 load test:
  - 10 concurrent sessions, 50 commands each < 2s p95
  - TTS generation parallelization

## 5. Acceptance Criteria

- [ ] Webhook endpoints HMAC/OAuth doğrulama
- [ ] Intent matching `voice_commands` dan (updatable, manager panel)
- [ ] IoT device control (TASK-020) + service calls (folio, room_service)
- [ ] Confirmation flow (requires_confirmation=true)
- [ ] TTS mock (Google Cloud TTS, base64 audio S3 store)
- [ ] Multi-language support (tr/en/ru templates)
- [ ] PII masking (folio balance, klima ayarı maskeleme)
- [ ] Session history + interaction audit
- [ ] Tüm endpoint'ler RBAC + hata zarfı
- [ ] OpenAPI Türkçe
- [ ] pytest backend/tests yeşil

---

## 6. Teslim Dosyaları

### FILE: hotel/backend/app/models/voice.py
```python
# Voice integration models
```

### FILE: hotel/backend/app/routers/voice_webhooks.py
```python
# Alexa + Google webhook endpoints
```

### FILE: hotel/backend/app/services/voice_service.py
```python
# Intent matching + action orchestration
```

### FILE: hotel/backend/integrations/voice/base.py
```python
# Abstract voice adapter
```

### FILE: hotel/backend/integrations/voice/alexa_adapter.py
```python
# Alexa signature verification + request parsing
```

### FILE: hotel/backend/integrations/voice/google_adapter.py
```python
# Google Assistant signature verification
```

### FILE: hotel/backend/integrations/voice/tts_service.py
```python
# TTS mock (Google Cloud TTS emulation)
```

### FILE: hotel/backend/migrations/versions/0NN_add_voice_control.py
```python
# Migration: voice_integrations, voice_commands, voice_sessions, voice_interactions, voice_intents_mapping
```

### FILE: hotel/backend/tests/test_modules/test_voice_commands.py
```python
# Unit + integration tests
```
