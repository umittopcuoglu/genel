---
id: TASK-011
modül: Modül 8 Kısmi (CRM & Misafir 360 & Loyalty)
kapsam: Misafir 360 profili + Loyalty puan sistemi + Şikayet/Yorum yönetimi
durum: kuyrukta (bağımlılık: TASK-007 — AI core, TASK-004 — folios)
tur: —
bağımlılık: TASK-004 (folios, reservations), TASK-007 (AI core foundation)
---

# TASK-011 — CRM & Misafir 360 & Loyalty

> Misafir profili birleşik görünüm (stays, harcama, tercihler, şikayetler).
> Loyalty puan sistemi (tier, earn, redeem).
> Feedback & complaints yönetimi.
> AI destekli yorum cevabı (TASK-012 GuestAI hazırlığı).

---

## 1. Misafir Profili Genişletme

### 1.1 Loyalty hesabı — `backend/app/models/loyalty_account.py`
```python
class LoyaltyAccount(BaseModel):
    __tablename__ = "loyalty_accounts"
    
    id: UUID
    guest_id: UUID                    # FK: guests
    
    # Tier sistemi
    tier: str                         # 'bronze', 'silver', 'gold', 'platinum'
    tier_since: date
    
    # Puanlar
    total_points: int = 0             # Birikmiş puan
    available_points: int = 0         # Harcanamayan puan
    
    # Yaşam değeri
    lifetime_stays: int = 0           # Konaklama sayısı
    lifetime_revenue: Decimal = Decimal(0)  # Toplam harcama
    
    # Statüsü
    status: str = 'active'            # 'active', 'suspended', 'cancelled'
    suspension_reason: str | None
    
    created_at: datetime
    updated_at: datetime
```

### 1.2 Puan işlemi — `backend/app/models/loyalty_transaction.py`
```python
class LoyaltyTransaction(BaseModel):
    __tablename__ = "loyalty_transactions"
    
    id: UUID
    loyalty_account_id: UUID          # FK: loyalty_accounts
    
    transaction_type: str             # 'earn', 'redeem', 'expire', 'adjust'
    amount: int                       # Puan
    
    # Kaynağı
    source_type: str | None           # 'folio', 'promotion', 'manual'
    source_id: UUID | None            # ilgili folio ID vb.
    
    # Açıklaması
    description: str                  # "Oda 5 gecelik konaklamaya 100 puan"
    
    balance_before: int
    balance_after: int
    
    created_at: datetime
    created_by: UUID                  # FK: users (veya SYSTEM_USER_ID)
```

### 1.3 Misafir 360 view — `backend/app/services/guest_360.py` (database view + servis)
```python
-- PostgreSQL view
CREATE VIEW guest_profiles_360 AS
SELECT
    g.id,
    g.name,
    g.email,
    g.phone,
    COUNT(DISTINCT r.id) as total_stays,
    SUM(CAST(f.total_amount AS NUMERIC)) as total_revenue,
    MAX(r.checkout_date) as last_checkout,
    AVG(EXTRACT(DAY FROM r.checkout_date - r.checkin_date)) as avg_los,
    STRING_AGG(DISTINCT pr.preference_type, ', ') as preferences,
    la.tier as loyalty_tier,
    la.available_points as loyalty_points,
    COUNT(DISTINCT c.id) as complaint_count,
    COUNT(DISTINCT fb.id) as feedback_count
FROM guests g
LEFT JOIN reservations r ON g.id = r.guest_id
LEFT JOIN folios f ON r.id = f.reservation_id
LEFT JOIN guest_preferences pr ON g.id = pr.guest_id
LEFT JOIN loyalty_accounts la ON g.id = la.guest_id
LEFT JOIN complaints c ON g.id = c.guest_id
LEFT JOIN feedback fb ON g.id = fb.guest_id
GROUP BY g.id, la.id;

-- Servis
class Guest360Service:
    @staticmethod
    async def get_guest_profile(guest_id: UUID, db: AsyncSession) -> dict:
        """Misafir 360 profili al."""
        result = await db.execute("""
            SELECT * FROM guest_profiles_360 WHERE id = :id
        """, {"id": guest_id})
        
        profile = result.one_or_none()
        if not profile:
            raise HTTPException(status_code=404)
        
        return {
            "basic": {
                "id": profile.id,
                "name": profile.name,
                "email": profile.email,
                "phone": profile.phone,
            },
            "stays": {
                "total_stays": profile.total_stays,
                "total_revenue": profile.total_revenue,
                "last_checkout": profile.last_checkout,
                "avg_los_days": profile.avg_los,
            },
            "preferences": profile.preferences,
            "loyalty": {
                "tier": profile.loyalty_tier,
                "available_points": profile.loyalty_points,
            },
            "feedback": {
                "complaint_count": profile.complaint_count,
                "feedback_count": profile.feedback_count,
            },
        }
```

---

## 2. Loyalty Sistemi

### 2.1 Puan kazanma — `backend/app/services/loyalty_service.py`
```python
class LoyaltyService:
    @staticmethod
    async def earn_points(
        guest_id: UUID,
        amount: Decimal,  # Harcama tutarı
        folio_id: UUID,
        db: AsyncSession,
    ):
        """
        Folio kapanışında otomatik: tutar → puan dönüşümü.
        Kural: 1 TL = 1 puan (yapılandırılabilir).
        Tier'e göre bonus (gold +%10, platinum +%25).
        """
        loyalty = await db.get(LoyaltyAccount, {"guest_id": guest_id})
        if not loyalty:
            # İlk konaklama → loyalty hesap oluştur
            loyalty = LoyaltyAccount(
                guest_id=guest_id,
                tier="bronze",
                total_points=0,
                available_points=0,
            )
            db.add(loyalty)
            await db.flush()
        
        # Puan hesapla
        base_points = int(amount)
        tier_bonus = {
            "bronze": 1.0,
            "silver": 1.05,
            "gold": 1.10,
            "platinum": 1.25,
        }
        multiplier = tier_bonus.get(loyalty.tier, 1.0)
        total_points = int(base_points * multiplier)
        
        # İşlem kaydı
        transaction = LoyaltyTransaction(
            loyalty_account_id=loyalty.id,
            transaction_type="earn",
            amount=total_points,
            source_type="folio",
            source_id=folio_id,
            description=f"Folio #{folio_id} konaklamaya {total_points} puan ({tier_bonus})",
            balance_before=loyalty.available_points,
            balance_after=loyalty.available_points + total_points,
            created_by=SYSTEM_USER_ID,
        )
        
        # Güncelle
        loyalty.available_points += total_points
        loyalty.total_points += total_points
        loyalty.lifetime_revenue += amount
        loyalty.lifetime_stays += 1
        
        # Tier yükseltme (yaşam değerine göre)
        new_tier = await determine_tier(loyalty.lifetime_revenue)
        if new_tier != loyalty.tier:
            loyalty.tier = new_tier
            loyalty.tier_since = datetime.utcnow().date()
        
        db.add(transaction)
        await db.commit()
    
    @staticmethod
    async def redeem_points(
        guest_id: UUID,
        points: int,
        redemption_type: str,  # 'discount', 'free_night', 'upgrade'
        db: AsyncSession,
    ) -> dict:
        """
        Puanları kullan (indirim, ücretsiz gece, vb.).
        Kontrol: yeterli puan var mı?
        """
        loyalty = await db.get(LoyaltyAccount, {"guest_id": guest_id})
        
        if not loyalty or loyalty.available_points < points:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient points. Available: {loyalty.available_points}",
            )
        
        # Puanları değere çevir
        point_value = {
            "discount": 0.1,         # 1 puan = 0.1 TL indirim
            "free_night": 500,       # Ücretsiz gece = 500 puan
            "upgrade": 250,          # Oda yükseltmesi = 250 puan
        }
        value = points * point_value.get(redemption_type, 0.1)
        
        # İşlem kaydı
        transaction = LoyaltyTransaction(
            loyalty_account_id=loyalty.id,
            transaction_type="redeem",
            amount=-points,
            source_type="manual",
            description=f"{redemption_type.title()}: {points} puan = {value} TL",
            balance_before=loyalty.available_points,
            balance_after=loyalty.available_points - points,
            created_by=SYSTEM_USER_ID,
        )
        
        # Güncelle
        loyalty.available_points -= points
        
        db.add(transaction)
        await db.commit()
        
        return {
            "redeemed_points": points,
            "value": value,
            "new_balance": loyalty.available_points,
        }

async def determine_tier(lifetime_revenue: Decimal) -> str:
    """Yaşam değerine göre tier belirle."""
    if lifetime_revenue >= 5000:
        return "platinum"
    elif lifetime_revenue >= 2500:
        return "gold"
    elif lifetime_revenue >= 1000:
        return "silver"
    else:
        return "bronze"
```

---

## 3. Feedback & Complaints

### 3.1 Şikayet — `backend/app/models/complaint.py`
```python
class Complaint(BaseModel):
    __tablename__ = "complaints"
    
    id: UUID
    guest_id: UUID                    # FK: guests
    reservation_id: UUID              # FK: reservations
    
    # Şikayet bilgisi
    title: str
    description: str
    complaint_type: str               # 'room', 'service', 'cleanliness', 'noise', 'other'
    severity: str                     # 'low', 'medium', 'high', 'critical'
    
    # Durum makinesi
    status: str                       # 'open', 'assigned', 'in_progress', 'resolved', 'closed'
    assigned_to: UUID | None          # FK: users (manager)
    resolution_notes: str | None
    
    resolved_at: datetime | None
    closed_at: datetime | None
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 3.2 Yorum — `backend/app/models/feedback.py`
```python
class Feedback(BaseModel):
    __tablename__ = "feedback"
    
    id: UUID
    guest_id: UUID                    # FK: guests
    reservation_id: UUID              # FK: reservations
    
    # Yorum
    rating: int                       # 1-5 yıldız
    comment: str
    categories: list[str]             # ["cleanliness", "staff", "value_for_money"]
    
    # Durum
    status: str                       # 'new', 'viewed', 'responded'
    manager_response: str | None      # Yönetici yanıtı (oto-draft GuestAI ile)
    
    created_at: datetime
    updated_at: datetime
```

---

## 4. Endpoints

### 4.1 Misafir 360 — `backend/app/routers/guests.py`
```python
@router.get("/guests/{guest_id}/360", tags=["Guests"])
async def get_guest_360_profile(
    guest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Misafir 360 profili: temel bilgiler, stays, tercihler, loyalty, şikayetler, yorum.
    Roller: manager, frontdesk, housekeeping (kısıtlı alan).
    """
    if not has_role(current_user, ["manager", "frontdesk", "housekeeping", "superadmin"]):
        raise HTTPException(status_code=403)
    
    profile = await Guest360Service.get_guest_profile(guest_id, db)
    return profile

@router.get("/guests/{guest_id}/stays", tags=["Guests"])
async def get_guest_stays(
    guest_id: UUID,
    limit: int = 10,
    ...
) -> list[dict]:
    """Misafir konaklamaları listele."""
    pass
```

### 4.2 Loyalty — `backend/app/routers/loyalty.py`
```python
@router.get("/loyalty/accounts/{guest_id}", tags=["Loyalty"])
async def get_loyalty_account(
    guest_id: UUID,
    ...
) -> dict:
    """Loyalty hesabını al."""
    pass

@router.post("/loyalty/earn", tags=["Loyalty"])
async def earn_points(
    req: EarnPointsRequest,  # {guest_id, amount, folio_id}
    ...
) -> dict:
    """Puan kazandır (folio kapanışından otomatik çağrılır)."""
    pass

@router.post("/loyalty/redeem", tags=["Loyalty"])
async def redeem_points(
    req: RedeemPointsRequest,  # {guest_id, points, redemption_type}
    ...
) -> dict:
    """Puan kullan (indirim, ücretsiz gece, vb.)."""
    pass

@router.get("/loyalty/accounts/{guest_id}/transactions", tags=["Loyalty"])
async def get_loyalty_transactions(
    guest_id: UUID,
    limit: int = 50,
    ...
) -> list[dict]:
    """Puan işlemlerinin tarihçesi."""
    pass
```

### 4.3 Şikayet — `backend/app/routers/complaints.py`
```python
@router.post("/complaints", tags=["Complaints"])
async def create_complaint(
    req: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    ...
) -> dict:
    """Yeni şikayet açı."""
    pass

@router.get("/complaints", tags=["Complaints"])
async def list_complaints(
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    ...
) -> list[dict]:
    """Şikayet listesi (manager)."""
    if not has_role(current_user, ["manager", "superadmin"]):
        raise HTTPException(status_code=403)
    pass

@router.patch("/complaints/{complaint_id}/assign", tags=["Complaints"])
async def assign_complaint(
    complaint_id: UUID,
    req: AssignComplaintRequest,  # {assigned_to}
    ...
) -> dict:
    """Şikayeti personele ata."""
    pass

@router.patch("/complaints/{complaint_id}/resolve", tags=["Complaints"])
async def resolve_complaint(
    complaint_id: UUID,
    req: ResolveComplaintRequest,  # {resolution_notes}
    ...
) -> dict:
    """Şikayet çözüldü olarak işaretle."""
    pass

@router.patch("/complaints/{complaint_id}/close", tags=["Complaints"])
async def close_complaint(
    complaint_id: UUID,
    ...
) -> dict:
    """Şikayet kapatıldı olarak işaretle."""
    pass
```

### 4.4 Yorum — `backend/app/routers/feedback.py`
```python
@router.post("/feedback/survey/send", tags=["Feedback"])
async def send_survey(
    req: SendSurveyRequest,  # {reservation_id}
    ...
) -> dict:
    """
    Checkout sonrası misafirere e-posta ile survey gönder (mock mail).
    """
    pass

@router.post("/feedback/submit", tags=["Feedback"])
async def submit_feedback(
    req: FeedbackSubmitRequest,  # {reservation_id, rating, comment, categories}
    ...
) -> dict:
    """Yorum/rating gönder."""
    pass

@router.get("/feedback", tags=["Feedback"])
async def list_feedback(
    status: str | None = None,
    rating_min: int | None = None,
    limit: int = 50,
    ...
) -> list[dict]:
    """Yorum listesi (manager/QA)."""
    pass

@router.post("/feedback/{feedback_id}/respond", tags=["Feedback"])
async def respond_to_feedback(
    feedback_id: UUID,
    req: RespondFeedbackRequest,  # {manager_response}
    ...
) -> dict:
    """Yorum'a yanıt (manager)."""
    pass
```

---

## 5. Testler — `backend/tests/test_crm.py`

### 5.1 Misafir 360
- Guest profile döner (stays, loyalty, complaints, feedback)
- Kısıtlı roller: housekeeping sadece temel bilgi görüyor

### 5.2 Loyalty earn
- Folio kapanışında puan kazanılır
- Tier yükseltme: lifetime_revenue >= 2500 → silver

### 5.3 Loyalty redeem
- Yeterli puan: redeem başarılı
- Yetersiz puan: 422 hatası

### 5.4 Şikayet
- Create → status='open'
- Assign → status='assigned', assigned_to doldurulur
- Resolve → status='resolved', resolution_notes
- Close → status='closed', closed_at doldurulur

### 5.5 Yorum
- Submit feedback → döner
- List feedback → filtreleme (status, rating)
- Respond → manager_response, status='responded'

---

## 6. Teslim dosyaları
```
### FILE: backend/app/models/loyalty_account.py
### FILE: backend/app/models/loyalty_transaction.py
### FILE: backend/app/models/complaint.py
### FILE: backend/app/models/feedback.py
### FILE: backend/app/services/guest_360.py
### FILE: backend/app/services/loyalty_service.py
### FILE: backend/app/routers/guests.py
### FILE: backend/app/routers/loyalty.py
### FILE: backend/app/routers/complaints.py
### FILE: backend/app/routers/feedback.py
### FILE: backend/tests/test_crm.py
### FILE: backend/alembic/versions/xxx_crm_tables.py  (migration: loyalty, complaint, feedback)
### FILE: backend/alembic/versions/xxx_guest_360_view.py  (view creation)
```

---

## 7. Kabul kriterleri
- `backend/tests/test_crm.py` yeşil (360, loyalty earn/redeem, complaints, feedback)
- Guest 360 profili: stays, revenue, preferences, loyalty tier, complaints/feedback sayıları
- Loyalty earn: folio kapanışında otomatik, tier bonus uygulanır
- Loyalty redeem: puan kontrolü, yetersizse 422
- Şikayet durum makinesi: open → assigned → resolved → closed
- Yorum: rating (1-5), categories, manager response
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (CRM endpoint'leri açıklanır)
