# HotelOps — Mimari (Modular Monolith + Event Bus + Connector Pattern)

Bu doküman, Cloudbeds/HotelRunner gibi monolith PMS'lerin acılarını
(sıkı bağ, tek deploy, modül-içi domino kırılmalar) çözen ama operasyonel
overhead'i microservice'lere kaçırmadan getiren **modular monolith**
yaklaşımımızı açıklar.

## Bounded Contexts

Kod fiziksel olarak `app/models|services|routers` altında tek pakettedir;
**mantıksal sınırlar** aşağıdaki 5 context ile çizilir. Cross-context iletişim
yalnızca **domain event'ler** (loose coupling) veya **bağlam yöneticisinin**
(integration hub) explicit servisleri üzerinden olur.

### 1. PMS Core (System of Record)
- Modeller: `front_office` (Room, Reservation, Guest, Stay), `reservation_ext`
  (RatePlan, Availability), `housekeeping`, `finance` (Folio, Payment),
  `groups`, `maintenance`.
- Router: `front_office`, `reservations`, `rate_plans`, `availability`,
  `folios`, `night_audit`, `housekeeping`, `groups`, `maintenance`.
- Üretir: `ReservationCreated`, `ReservationCancelled`, `CheckInCompleted`,
  `CheckOutCompleted`, `RoomStatusChanged`.

### 2. Distribution Layer (Channel Manager)
- Modeller: `channel`, `channel_mapping`, `channel_sync_log`,
  `overbooking_rule`.
- Router: `channels`.
- Connector pattern: `app/services/connectors/` (Booking, Expedia, Agoda
  pluggable).
- Tüketir: `ReservationCreated` → tüm OTA'lara push.

### 3. Guest Experience (CRM, Messaging, Loyalty)
- Modeller: `crm` (Segment, Campaign, GuestNote, CommunicationLog),
  `loyalty_account`, `loyalty_transaction`, `complaint`, `feedback`,
  `chat_session`, `chat_message`.
- Router: `crm`, `loyalty`, `whatsapp`, `complaints`, `feedback`.
- Tüketir: `ReservationCreated` → welcome mesajı, `CheckOutCompleted` →
  feedback talebi.

### 4. Revenue & Pricing (AI Engine)
- Modeller: `rate_recommendation`, `occupancy_forecast`, `overbooking_rule`.
- Router: `revenue`.
- Üretir: `RateRecommended` (gelecekte).

### 5. Integration Hub
- Modeller: `integration_setting`, `payment_transaction`, `einvoice`, `gds`,
  `iot`, `voice`, `blockchain_identity`.
- Router: `integrations`, `payments`, `einvoice`, `gds`, `iot`,
  `voice_webhooks`, `blockchain`, `security`.
- Plugin marketplace'in iskeleti: tüm dış entegrasyonlar parametrik
  ayarlanır; her tipin bir connector/provider arayüzü vardır.

## Event Bus

`app/core/events.py` — in-process async pub/sub. Tek instance: `events`.

### Yayıncı (publisher)
```python
from app.core.events import events, ReservationCreated
await events.publish(ReservationCreated(reservation_id=r.id, ...), db=db)
```

### Abone (subscriber)
```python
from app.core.events import events, ReservationCreated

@events.subscribe(ReservationCreated)
async def push_to_otas(event: ReservationCreated, db):
    ...
```

### Garantiler
- **Fault isolation**: bir handler exception'ı diğerlerini kırmaz.
- **DB context**: `db` kwarg'ı çağıranın transaction'ına katılır.
- **Migration path**: Kafka/NATS'e geçişte sadece `publish` gövdesi değişir.

## Connector Pattern

`app/services/connectors/base.py` → `BaseOTAConnector` ABC.

Concrete connector'lar (`BookingConnector`, `ExpediaConnector`,
`AgodaConnector`) `register_connector('booking', BookingConnector)` ile
runtime registry'ye girer. Yeni bir OTA eklemek **core değişikliği gerektirmez**.

Aynı pattern:
- Payment provider'ları (iyzico/Stripe/PayTR — `payment_service`)
- e-Fatura entegratörleri (Foriba/Logo — `einvoice_service`)
- IoT broker'lar (MQTT — `integration_service`)

## Microservice'e geçiş kriterleri

Bu monolith **müşteri-50'ye kadar** rahatça ölçeklenir. Ayırmak gerekirse:
1. **Distribution Layer** ilk ayrılır (OTA traffic patladığında).
2. **Booking Engine** (public/komisyonsuz satış) ikinci — frontend'le birlikte ayrı deploy.
3. **AI Engine** (Revenue) üçüncü — GPU/CPU farklı profil.

Event Bus, connector pattern ve context sınırları **bugünden** kuruldu;
ayırma maliyeti bu sayede haftalardan günlere iner.
