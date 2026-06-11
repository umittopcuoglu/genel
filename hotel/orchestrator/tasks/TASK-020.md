---
id: TASK-020
modül: IoT / Akıllı Oda Entegrasyonu
kapsam: IoT cihaz yönetimi + durum oku/yaz + sahneler + automation + telemetri/uyarılar
durum: kuyrukta (TASK-002, TASK-006, TASK-015 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-002 (rooms), TASK-006 (WebSocket), TASK-015 (maintenance work_orders)
---

# TASK-020 — IoT / Akıllı Oda Entegrasyonu (Nest, KNX, Philips Hue)

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md — IoT adapter deseni.

## 1. Veri Modeli

### `iot_devices`
- id (UUID, PK) [BaseModel]
- room_id (UUID FK → rooms.id nullable, null=ortak alan)
- device_name (VARCHAR 100)
- device_type (VARCHAR 30) — thermostat / lighting / blind / smart_lock / sensor / other
- protocol (VARCHAR 30) — nest | knx | hue | zigbee | generic
- manufacturer (VARCHAR 50)
- model_number (VARCHAR 100 nullable)
- device_address (VARCHAR 100) — IP / MAC / device_id
- online_status (VARCHAR 15, default="unknown") — online / offline / error / unknown
- last_heartbeat (TIMESTAMP nullable)
- battery_level (INT nullable, %)
- firmware_version (VARCHAR 50 nullable)
- status (VARCHAR 15, default="active") — active / inactive / decommissioned
- notes (TEXT nullable)
- Index: room_id, device_type, online_status

### `device_states`
- id (UUID, PK) [BaseModel]
- iot_device_id (UUID FK → iot_devices.id)
- state_type (VARCHAR 30) — temperature / humidity / brightness / position / lock_status / co2
- current_value (VARCHAR 100) — value, unit'le birlikte okunur (e.g., "22.5°C", "75%")
- unit (VARCHAR 20 nullable) — "°C", "%", "lux", "status"
- timestamp (TIMESTAMP)
- source (VARCHAR 30) — direct_read | webhook | manual_set
- Index: iot_device_id, state_type, timestamp

### `iot_scenes`
- id (UUID, PK) [BaseModel]
- scene_name (VARCHAR 100) — "welcome", "eco", "checkout", "do_not_disturb", "cinema"
- description (TEXT nullable)
- actions (JSON array) — [{ device_id, device_type, action: "set_temp=22" | "brightness=100" | ... }]
- status (VARCHAR 15, default="active") — active / inactive
- notes (TEXT nullable)
- Index: status

### `device_events`
- id (UUID, PK) [BaseModel]
- iot_device_id (UUID FK → iot_devices.id)
- event_type (VARCHAR 30) — offline | low_battery | sensor_alert | state_change | manual_override
- severity (INT, default=3) — 1 critical … 5 info
- description (TEXT)
- action_taken (VARCHAR 200 nullable) — "work_order created", "notification sent"
- timestamp (TIMESTAMP)
- Index: iot_device_id, event_type, severity

## 2. Endpoint'ler

### `POST /api/v1/iot/devices`
- Auth: superadmin, manager, maintenance
- Body: { room_id?, device_name, device_type, protocol, manufacturer, model_number?, device_address }
- 201 döner iot_device (status=active, online_status=unknown)

### `GET /api/v1/iot/devices`
- Auth: superadmin, manager, maintenance, frontdesk
- Query: ?room_id=&device_type=&online_status=&status=
- 200 döner { data: [{...}], meta: { online_count, offline_count, by_device_type } }

### `GET /api/v1/iot/devices/{id}/state`
- Auth: superadmin, manager, maintenance, frontdesk
- 200 döner { data: { current_states: [{ state_type, current_value, unit, timestamp }], battery_level, online_status }, meta: {...} }

### `POST /api/v1/iot/devices/{id}/command`
- Auth: superadmin, manager, frontdesk, housekeeping (opsiyonel), maintenance
- Body: { command } — "set_temperature=22" | "set_brightness=100" | "unlock" | "close_blinds" | ...
- Adapter (protocol'e göre) activate; device'a komut gönder (async, WS subscribe için await opsiyonel)
- command fail ise 503 `DEVICE_OFFLINE` veya 400 `INVALID_COMMAND`
- Başarılı: device_state update, device_event log, WS broadcast (room subscribers)
- 200 döner { success: true, new_state: {...} }

### `POST /api/v1/iot/scenes/{id}/apply`
- Auth: superadmin, manager, frontdesk, housekeeping (opsiyonel)
- Body: { room_id }
- Scene'nin actions → tüm devices'a command batch işle
- 200 döner { data: { applied_count, failed_count }, meta: {...} }

### `GET /api/v1/iot/scenes`
- Auth: superadmin, manager, frontdesk
- 200 döner { data: [{...}], meta: {...} }

### `POST /api/v1/iot/scenes`
- Auth: superadmin, manager
- Body: { scene_name, description?, actions: [{ device_id, action }] }
- 201 döner scene

### `GET /api/v1/iot/devices/{id}/events`
- Auth: superadmin, manager, maintenance
- Query: ?event_type=&from_datetime=&to_datetime=&severity=
- 200 döner { data: [{...}], meta: { by_type: {...}, by_severity: {...} } }

### `POST /api/v1/iot/webhook`
- Auth: IoT provider (webhook signature doğrulama)
- Body: { device_id, event, data: {...} } — event="state_change" | "offline" | "low_battery" | ...
- device_state update / device_event create
- severity >= 3 ise action logic:
  - offline → TASK-015 work_order create opsiyonel (maintenance alert)
  - low_battery → maintenance bildir
  - sensor_alert → relevant team WS notify
- 200 döner { success: true }

### `GET /api/v1/iot/automations`
- Auth: superadmin, manager
- 200 döner { data: { check_in_automation: { scene: "welcome", enabled }, check_out_automation: { scene: "eco", enabled } }, meta: {...} }

### `PATCH /api/v1/iot/automations`
- Auth: superadmin, manager
- Body: { check_in_scene_id?, check_out_scene_id?, enabled?: boolean }
- Check-in otomasyon: TASK-003 check-in'de "welcome" scene auto-apply (opsiyonel, enable flag)
- Check-out: "eco" scene otomatik
- 200 döner { automations: {...} }

## 3. İş Mantığı

- **Cihaz keşfi**: protocol adapter'dan (Nest, KNX, Hue) eşleştirme ve inventory; heartbeat monitoring (offline detect)
- **Durum oku**: device_state query; real-time → WS subscribe (TASK-006 entegrasyonu); canlı sıcaklık/ışık/perde pozisyonu
- **Komut gönder**: command normalize → adapter → device; komut log (audit)
- **Sahne uygulama**: scene actions batch execute; bir device fail ise diğerleri continue
- **Check-in automation**: konaklamada check-in complete → "welcome" scene: sıcaklık 22°C, ışık 80%, perde open (enabled ise)
- **Check-out automation**: check-out → "eco" scene: sıcaklık 18°C, ışık 30%, perde close (energy saving)
- **Telemetri/Uyarı**: low_battery event → maintenance WS; offline → retry interval (exponential backoff); sensor alert (CO2 yüksek) → housekeeping/maintenance
- **Bakım entegrasyonu**: offline event → opsiyonel TASK-015 work_order create (maintenance review)

## 4. Dış Sistem Integrasyon (Mock-First)

### Adapter Deseni
```
integrations/iot/base.py: BaseIoTAdapter (abstract)
  - read_state(device_id, state_type) → async value
  - send_command(device_id, command) → async result
  - discover_devices() → async [device_list]
  - handle_webhook(data) → async processed_event
  
integrations/iot/nest.py: NestAdapter (mock-first)
integrations/iot/knx.py: KNXAdapter (mock-first)
integrations/iot/hue.py: HueAdapter (mock-first)
```
- Mock: in-memory device state, webhook simulation
- Test: mock adapter; gerçek API key → .env

## 5. WebSocket Integration (TASK-006)

- Channel: `ws://host/ws/rooms/{room_id}/iot`
- Broadcast: device state change, command result, device_event (severity >= 3)
- Message format:
  ```json
  {
    "type": "device_state_change",
    "device_id": "...",
    "new_state": { "state_type": "temperature", "value": "22.5°C" },
    "timestamp": "2026-06-11T14:30:00Z"
  }
  ```

## 6. Testler (minimum 14)
- iot_device create + discovery (mock adapter)
- device state read → current_states
- command send → device_state update, WS broadcast
- command fail → 503 DEVICE_OFFLINE | 400 INVALID_COMMAND
- scene apply → batch commands, partial failure handling
- webhook state_change → device_state update
- webhook offline → device_event create, maintenance alert (opsiyonel)
- low_battery event → severity flag, housekeeping WS notify
- check-in automation → "welcome" scene apply
- check-out automation → "eco" scene apply
- adapter mock mode: in-memory queue
- RBAC: frontdesk scene apply ✓, device command ✓, create 403; maintenance device command ✓
- heartbeat monitoring: no heartbeat > threshold → offline mark (mock timer)

## 7. Teslim dosyaları
```
### FILE: backend/app/models/iot.py
### FILE: backend/app/routers/iot.py
### FILE: backend/app/services/iot_service.py
### FILE: backend/integrations/iot/base.py
### FILE: backend/integrations/iot/nest.py
### FILE: backend/integrations/iot/knx.py
### FILE: backend/integrations/iot/hue.py
### FILE: backend/tests/test_modules/test_iot.py
### FILE: backend/migrations/versions/005_add_iot_tables.py
```

## 8. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- Check-in/out automation end-to-end test edilmiş (TASK-003 entegrasyonu)
- IoT device offline detection + maintenance alert (TASK-015) test edilmiş
- Adapter mock-first; production key → .env
- WebSocket broadcast (TASK-006) test edilmiş (room subscription)
- OpenAPI Türkçe; error kodları `DEVICE_OFFLINE`, `INVALID_COMMAND`, adapter-spesifik hatalar
