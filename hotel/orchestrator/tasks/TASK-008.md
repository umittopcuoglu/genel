---
id: TASK-008
modül: Modül 2 Genişletme (Channel Manager & OTA)
kapsam: Booking.com, Expedia, Airbnb adaptörleri + ARI push + overbooking yönetimi
durum: kuyrukta (bağımlılık: TASK-007)
tur: —
bağımlılık: TASK-007 (AI core), TASK-003 (reservations)
---

# TASK-008 — Channel Manager

> OTA (Booking.com, Expedia, Airbnb vb.) entegrasyonları yönetir.
> Rezervasyonlar çoklu kanallardan oluşabilir, availability tüm kanallara push edilir,
> overbooking kuralları uygulanır, sync log'lar tutulur.

---

## 1. Veri Modelleri

### 1.1 Kanal kaydı — `backend/app/models/channel.py`
```python
class Channel(BaseModel):
    __tablename__ = "channels"
    
    id: UUID
    name: str                         # 'booking_com', 'expedia', 'airbnb'
    channel_type: str                 # Literal['ota', 'direct', 'corporate']
    credentials_encrypted: str        # Cryptography ile şifrelenmiş API key
    
    # İletişim ayarları
    api_base_url: str | None
    enabled: bool = True
    
    # Sync davranışı
    sync_interval_hours: int = 4      # her 4 saatte sync kontrol et
    last_sync_at: datetime | None
    next_sync_at: datetime | None
    
    # Pagination/ratelimit
    rate_limit_requests: int = 100    # örn. 100 req/min
    rate_limit_window_seconds: int = 60
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 1.2 Kanal-oda haritaması — `backend/app/models/channel_mapping.py`
```python
class ChannelMapping(BaseModel):
    __tablename__ = "channel_mappings"
    
    id: UUID
    channel_id: UUID                  # FK: channels
    room_id: UUID                     # FK: rooms
    external_room_id: str             # Booking.com "room_123456" vb.
    mapping_status: str               # 'active', 'paused', 'error'
    
    # Oto-eşleştirme hintleri
    auto_match_confidence: float | None  # 0.0…1.0; 0.8+ match sabit
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 1.3 Overbooking kuralları — `backend/app/models/overbooking_rule.py`
```python
class OverbookingRule(BaseModel):
    __tablename__ = "overbooking_rules"
    
    id: UUID
    room_type_id: UUID | None         # NULL = tüm oda tipleri
    channel_id: UUID | None           # NULL = tüm kanallar
    
    overbooking_percent: float        # örn. 5.0 (5% fazla booking izin ver)
    enabled: bool = True
    note: str                         # "Yaz mevsimine özel"
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 1.4 Sync günlüğü — `backend/app/models/channel_sync_log.py`
```python
class ChannelSyncLog(BaseModel):
    __tablename__ = "channel_sync_logs"
    
    id: UUID
    channel_id: UUID                  # FK: channels
    sync_type: str                    # 'availability', 'reservation', 'rate'
    status: str                       # 'pending', 'in_progress', 'success', 'error'
    
    reservations_synced: int
    rooms_updated: int
    error_message: str | None
    response_time_ms: int
    
    created_at: datetime
```

---

## 2. Kanal Adaptörleri

### 2.1 Temel adaptör — `backend/app/integrations/channels/base.py`
```python
class ChannelAdapter(ABC):
    """Tüm OTA adaptörleri bu sınıfı miras alır."""
    
    def __init__(self, channel: Channel):
        self.channel = channel
        self.credentials = decrypt_credentials(channel.credentials_encrypted)
    
    @abstractmethod
    async def get_reservations(self, from_date: date, to_date: date) -> list[ChannelReservation]:
        """OTA'dan rezervasyonları çek (pull)."""
        pass
    
    @abstractmethod
    async def push_availability(self, room_id: UUID, availabilities: list[dict]) -> bool:
        """Oda availability'sini OTA'ya gönder (push)."""
        pass
    
    @abstractmethod
    async def push_rates(self, room_id: UUID, rates: list[dict]) -> bool:
        """Ücretleri OTA'ya gönder."""
        pass
    
    @abstractmethod
    async def get_rate_restrictions(self) -> dict:
        """OTA'nın oran kontrolleri (min/max los, advance purchase vb.)."""
        pass
```

### 2.2 Booking.com adaptörü — `backend/app/integrations/channels/booking_com.py`
```python
class BookingComAdapter(ChannelAdapter):
    """Booking.com (Property Management API — mock-first)."""
    
    async def get_reservations(self, from_date, to_date):
        """
        GET /hotel/{hotelId}/reservations?from_date=...&to_date=...
        Yeni/değiştirilmiş rezervasyonları döndür.
        """
        # Mock-first: static JSON döndür (TASK-006'da Playwright mock'u gibi)
        if ENABLE_MOCK:
            return self._mock_reservations(from_date, to_date)
        
        # Real API (Faz 2 sonu)
        response = await self._http_get(...)
        return [ChannelReservation.from_booking_com(r) for r in response["reservations"]]
    
    async def push_availability(self, room_id, availabilities):
        """
        PUT /availability/{roomId}
        availability = {"date": "2026-06-11", "available": 5, "min_los": 1}
        """
        # Overbooking kuralı uygula
        rule = await get_overbooking_rule(room_type_id, channel_id=self.channel.id)
        if rule and rule.overbooking_percent:
            availabilities = self._apply_overbooking(availabilities, rule.overbooking_percent)
        
        if ENABLE_MOCK:
            return True
        
        response = await self._http_put(...)
        return response.status_code == 200
```

### 2.3 Expedia adaptörü — `backend/app/integrations/channels/expedia.py`
```python
class ExpediaAdapter(ChannelAdapter):
    """Expedia (EQC API — mock-first)."""
    # Booking.com'a benzer impl.
```

### 2.4 Airbnb adaptörü — `backend/app/integrations/channels/airbnb.py`
```python
class AirbnbAdapter(ChannelAdapter):
    """Airbnb (mock-first)."""
    # Benzer pattern
```

### 2.5 Adaptör factory — `backend/app/integrations/channels/factory.py`
```python
async def get_channel_adapter(channel_id: UUID, db: AsyncSession) -> ChannelAdapter:
    """Kanal tipine göre doğru adaptörü döndür."""
    channel = await db.get(Channel, channel_id)
    if channel.name == "booking_com":
        return BookingComAdapter(channel)
    elif channel.name == "expedia":
        return ExpediaAdapter(channel)
    # ...
```

---

## 3. Availability & Sync Orchestration

### 3.1 Availability push — `backend/app/services/channel_sync.py`
```python
class ChannelSyncService:
    @staticmethod
    async def push_availability_to_channels(
        room_id: UUID,
        db: AsyncSession,
    ):
        """
        Oda availability değişince (TASK-003 endpoint'ten) tüm aktif kanallara push.
        Kuyruk (BackgroundTasks veya Celery): veri tutarlılığı için async çalış.
        """
        room = await db.get(Room, room_id)
        availabilities = await calculate_availabilities(room, db)  # 90 gün
        
        # Tüm aktif kanallar
        channels = await db.execute(
            select(Channel).where(Channel.enabled == True, Channel.deleted_at == None)
        )
        
        for channel in channels.scalars():
            try:
                adapter = get_channel_adapter(channel.id, db)
                success = await adapter.push_availability(room_id, availabilities)
                
                # Sync log
                log = ChannelSyncLog(
                    channel_id=channel.id,
                    sync_type="availability",
                    status="success" if success else "error",
                    rooms_updated=1 if success else 0,
                    created_at=datetime.utcnow(),
                )
                db.add(log)
            except Exception as e:
                log = ChannelSyncLog(
                    channel_id=channel.id,
                    sync_type="availability",
                    status="error",
                    error_message=str(e),
                    created_at=datetime.utcnow(),
                )
                db.add(log)
        
        await db.commit()
```

### 3.2 Reservation pull — `backend/app/services/channel_sync.py`
```python
@staticmethod
async def pull_reservations_from_channels(db: AsyncSession):
    """
    Periyodik görev (cron benzeri). Her aktif kanal için:
    1. Son sync zamanından yeni rezilme çek
    2. Mapping'i kullanarak iç oda ID'ye çevir
    3. Overbooking kontrol et
    4. Yeni rez oluştur (source=ota, channel_id=...)
    """
    channels = await db.execute(select(Channel).where(...))
    
    for channel in channels.scalars():
        adapter = get_channel_adapter(channel.id, db)
        from_date = channel.last_sync_at or (datetime.utcnow().date() - timedelta(days=90))
        to_date = datetime.utcnow().date() + timedelta(days=365)
        
        try:
            ext_reservations = await adapter.get_reservations(from_date, to_date)
            
            for ext_rez in ext_reservations:
                # Harici oda ID → iç oda ID
                mapping = await db.execute(
                    select(ChannelMapping).where(
                        ChannelMapping.channel_id == channel.id,
                        ChannelMapping.external_room_id == ext_rez.room_id,
                    )
                )
                mapping = mapping.scalar_one_or_none()
                
                if not mapping:
                    # Oto-eşleştirme denemesi (TASK-008 v1.1'de; şimdilik skip)
                    continue
                
                # Overbooking kontrolü
                total_booked = await count_reservations(mapping.room_id, ext_rez.checkin, ext_rez.checkout, db)
                max_allowed = await get_overbooking_limit(mapping.room_id, channel.id, db)
                
                if total_booked >= max_allowed:
                    # OTA'ya bildir: SOLD OUT
                    await adapter.push_availability(mapping.room_id, [{"date": ..., "available": 0}])
                    continue
                
                # Yeni rezervasyon oluştur
                new_rez = Reservation(
                    room_id=mapping.room_id,
                    guest_name=ext_rez.guest_name,
                    email=ext_rez.email,
                    phone=ext_rez.phone,
                    checkin_date=ext_rez.checkin,
                    checkout_date=ext_rez.checkout,
                    rate_plan_id=...,  # Default bulunur
                    source="ota",
                    channel_id=channel.id,
                    external_reservation_id=ext_rez.external_id,
                    status="confirmed",
                    created_by=SYSTEM_USER_ID,
                )
                db.add(new_rez)
            
            # Sync log + update last_sync_at
            channel.last_sync_at = datetime.utcnow()
            channel.next_sync_at = channel.last_sync_at + timedelta(hours=channel.sync_interval_hours)
            log = ChannelSyncLog(
                channel_id=channel.id,
                sync_type="reservation",
                status="success",
                reservations_synced=len(ext_reservations),
                created_at=datetime.utcnow(),
            )
            db.add(log)
        
        except Exception as e:
            log = ChannelSyncLog(
                channel_id=channel.id,
                sync_type="reservation",
                status="error",
                error_message=str(e),
                created_at=datetime.utcnow(),
            )
            db.add(log)
        
        await db.commit()
```

---

## 4. Endpoints

### 4.1 Kanal CRUD — `backend/app/routers/channels.py`
```python
@router.post("/channels", tags=["Channels"])
async def create_channel(
    req: ChannelCreateRequest,  # {name, channel_type, credentials, ...}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Yeni OTA kanalı ekle. Credentials şifreli kaydedilir."""
    if not has_role(current_user, ["manager", "superadmin"]):
        raise HTTPException(status_code=403)
    
    channel = Channel(
        name=req.name,
        channel_type=req.channel_type,
        credentials_encrypted=encrypt_credentials(req.credentials),
        enabled=True,
        created_by=current_user.id,
    )
    db.add(channel)
    await db.commit()
    return {"id": channel.id, "name": channel.name, "enabled": channel.enabled}

@router.get("/channels", tags=["Channels"])
async def list_channels(...) -> list[dict]:
    """Aktif kanalları listele."""
    pass

@router.patch("/channels/{channel_id}", tags=["Channels"])
async def update_channel(
    channel_id: UUID,
    req: ChannelUpdateRequest,
    ...
) -> dict:
    """Kanal ayarlarını güncelle (credentials hariç)."""
    pass

@router.delete("/channels/{channel_id}", tags=["Channels"])
async def delete_channel(channel_id: UUID, ...) -> dict:
    """Soft delete."""
    pass
```

### 4.2 Mapping CRUD — `backend/app/routers/channels.py`
```python
@router.post("/channels/{channel_id}/mappings", tags=["Channels"])
async def create_mapping(
    channel_id: UUID,
    req: MappingCreateRequest,  # {room_id, external_room_id}
    ...
) -> dict:
    """Harici oda ID'sini iç oda ID'sine eşle."""
    pass

@router.get("/channels/{channel_id}/mappings", tags=["Channels"])
async def list_mappings(channel_id: UUID, ...) -> list[dict]:
    """Kanal için eşleştirmeleri listele."""
    pass

@router.delete("/channels/{channel_id}/mappings/{mapping_id}", tags=["Channels"])
async def delete_mapping(...) -> dict:
    """Eşleştirmeyi kaldır."""
    pass
```

### 4.3 Overbooking kuralları — `backend/app/routers/channels.py`
```python
@router.post("/overbooking-rules", tags=["Channels"])
async def create_overbooking_rule(
    req: OverbookingRuleCreateRequest,
    ...
) -> dict:
    """Yeni overbooking kuralı tanımla."""
    pass

@router.get("/overbooking-rules", tags=["Channels"])
async def list_overbooking_rules(...) -> list[dict]:
    pass

@router.patch("/overbooking-rules/{rule_id}", tags=["Channels"])
async def update_overbooking_rule(...) -> dict:
    pass
```

### 4.4 Sync kontrol — `backend/app/routers/channels.py`
```python
@router.post("/channels/{channel_id}/sync", tags=["Channels"])
async def trigger_sync(
    channel_id: UUID,
    sync_type: Literal["availability", "reservation"] = "availability",
    ...
) -> dict:
    """
    Manual senkronizasyon tetikle.
    availability: HotelOps → OTA
    reservation: OTA → HotelOps
    """
    if sync_type == "availability":
        # push_availability_to_channels(channel_id, ...)
        pass
    else:
        # pull_reservations_from_channels(channel_id, ...)
        pass
    
    return {"status": "sync_started", "channel_id": channel_id}

@router.get("/channels/{channel_id}/sync-logs", tags=["Channels"])
async def get_sync_logs(
    channel_id: UUID,
    limit: int = 50,
    ...
) -> list[dict]:
    """Son senkronizasyon günlüklerini göster."""
    pass
```

### 4.5 Webhook alıcı — `backend/app/routers/channels.py`
```python
@router.post("/channels/webhooks/booking-com", tags=["Channels"])
async def webhook_booking_com(
    payload: dict,  # OTA'dan gelen veri
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Booking.com webhook: yeni/iptal rez bildirimi.
    İmza doğrulama (HMAC-SHA256).
    """
    # Imza doğrula
    if not verify_webhook_signature(payload, BOOKING_COM_SECRET):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Rez oluştur/güncelle
    channel = await db.execute(
        select(Channel).where(Channel.name == "booking_com")
    )
    channel = channel.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Booking.com channel not configured")
    
    # Gelen rez'i işle (pull_reservations_from_channels'ın bir parçası)
    ...
    
    return {"status": "received"}
```

---

## 5. Testler — `backend/tests/test_channels.py`

### 5.1 Temel channel CRUD
- POST /channels → kanal oluşturulur
- GET /channels → liste döner
- PATCH /channels/{id} → güncelleme

### 5.2 Mapping test
- Harici oda → iç oda eşleştirme
- Mapping'i kullanarak rez oluştur

### 5.3 Overbooking test
- Rule %5 overbooking izin ver
- 10 oda var; 10 rez + 1 overbooking rez başarılı
- 11'inci rez reddedilir (overbooking limit aşıldı)

### 5.4 Adapter mock test
- `ENABLE_MOCK=true` → BookingComAdapter mock rez döner
- `push_availability()` başarılı

### 5.5 Sync service test
- Kanal availability push → log oluşturulur
- Reservation pull → yeni rez kaydedilir

### 5.6 Webhook test (Booking.com)
- Geçerli imza → webhook işlenir
- Geçersiz imza → 403 hatası

---

## 6. Teslim dosyaları
```
### FILE: backend/app/models/channel.py
### FILE: backend/app/models/channel_mapping.py
### FILE: backend/app/models/overbooking_rule.py
### FILE: backend/app/models/channel_sync_log.py
### FILE: backend/app/integrations/__init__.py
### FILE: backend/app/integrations/channels/__init__.py
### FILE: backend/app/integrations/channels/base.py
### FILE: backend/app/integrations/channels/booking_com.py
### FILE: backend/app/integrations/channels/expedia.py
### FILE: backend/app/integrations/channels/airbnb.py
### FILE: backend/app/integrations/channels/factory.py
### FILE: backend/app/services/channel_sync.py
### FILE: backend/app/routers/channels.py
### FILE: backend/tests/test_channels.py
### FILE: backend/alembic/versions/xxx_channel_tables.py  (migration)
### FILE: backend/.env.example                      (ENABLE_MOCK, BOOKING_COM_SECRET, EXPEDIA_KEY, etc.)
```

---

## 7. Kabul kriterleri
- `backend/tests/test_channels.py` yeşil (CRUD, mapping, overbooking, sync, webhook)
- Channel adaptörler (Booking.com, Expedia, Airbnb) mock modda çalışır
- Availability push: HotelOps oda availability değişince → `push_availability_to_channels()` tetiklenir
- Reservation pull: OTA'dan çekilen rezler → iç oda ID'ye eşleştirilerek HotelOps'a eklenir
- Overbooking kuralı uygulanır: rule %5 izin verse, 11. rez reddedilir
- Webhook (Booking.com): imza doğrulaması başarılı, yeni rez kaydedilir
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (Channel endpoint'leri açıklanır)
