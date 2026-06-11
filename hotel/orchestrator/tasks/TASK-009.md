---
id: TASK-009
modül: Modül 2 AI Genişletme (RevenueIQ Advisor)
kapsam: Ücret önerileri + Doluluk tahmini + Kanal optimizasyonu + Alerta sistemi
durum: kuyrukta (bağımlılık: TASK-007, TASK-008)
tur: —
bağımlılık: TASK-007 (AI core), TASK-008 (Channel Manager)
---

# TASK-009 — RevenueIQ AI

> Gelir yönetimi danışmanı. Ücret önerileri, doluluk tahminleri, kanal performansı analizi
> ve alarm sistemini sağlar. Geçmiş veriye dayanan istatistiksel model + LLM yorum/tavsiye.

---

## 1. Veri Modelleri

### 1.1 Ücret önerileri — `backend/app/models/rate_recommendation.py`
```python
class RateRecommendation(BaseModel):
    __tablename__ = "rate_recommendations"
    
    id: UUID
    room_type_id: UUID                # FK: room_types
    date: date                        # Hangi tarih için tavsiye
    
    recommended_rate: Decimal         # TL (örn: 450.00)
    current_rate: Decimal             # Mevcut fiyat
    price_change_percent: float       # Yüzde değişim
    
    rationale: str                    # LLM'nin açıklaması (masked)
    confidence_score: float           # 0.0…1.0 (model güveni)
    
    # İstatistiksel temel
    historical_avg_rate: Decimal
    occupancy_forecast: float         # Tahmin edilen doluluk %
    demand_trend: str                 # 'high', 'medium', 'low'
    
    # Kanal ve pazar bilgisi
    competitor_avg_rate: Decimal | None
    channel_parity_penalty: float | None  # %cinsinden ayar
    
    status: str                       # 'suggested', 'approved', 'applied', 'expired'
    applied_at: datetime | None
    
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 1.2 Doluluk tahminleri — `backend/app/models/occupancy_forecast.py`
```python
class OccupancyForecast(BaseModel):
    __tablename__ = "occupancy_forecasts"
    
    id: UUID
    room_type_id: UUID | None         # NULL = otel geneli
    forecast_date: date               # Tahmin tarihi
    
    # Tahminler
    predicted_occupancy_percent: float  # 65.0 (%)
    predicted_rooms_occupied: int       # Mutlak sayı
    confidence_interval: str            # "±5%" veya JSON
    
    # Model bilgisi
    forecast_method: str              # 'arima', 'exponential_smoothing', 'neural_net'
    forecast_horizon_days: int        # Kaç gün önceden tahmin edilen
    
    # Gerçekleşen vs tahmin
    actual_occupancy_percent: float | None  # Gerçekleşince doldurulur
    forecast_error_percent: float | None    # |tahmin - gerçek|
    
    created_at: datetime
    updated_at: datetime
```

### 1.3 Rekabet oranları — `backend/app/models/competitor_rate.py`
```python
class CompetitorRate(BaseModel):
    __tablename__ = "competitor_rates"
    
    id: UUID
    competitor_name: str              # "Otel ABC", "Competitor XYZ"
    room_type_id: UUID                # FK: room_types
    survey_date: date
    
    surveyed_rate: Decimal            # Rakip ücret
    market_segment: str               # "luxury", "business", "budget"
    source: str                       # "booking_com_scrape" (mock-first)
    
    created_at: datetime
```

---

## 2. RevenueIQ AI Agent

### 2.1 Agent sınıfı — `backend/app/core/agents/revenue_qa.py`
```python
class RevenueQAAgent(BaseAgent):
    """Ücret tavsiyesi ve gelir analizi."""
    
    agent_name = "revenue_qa"
    model_provider = "deepseek"       # override edilebilir
    prompt_version = "1.0.0"
    
    async def execute(
        self,
        input_schema: RevenueQAInput,  # {room_type_id, forecast_horizon}
        context: dict = None,
        db: AsyncSession = None,
        user: User = None,
    ) -> RevenueQAOutput:
        """
        1. Geçmiş veri → istatistiksel model (ARIMA/exponential smoothing)
        2. Doluluk tahmini
        3. Rekabet oranları (mock-first: sabit rakip verileri)
        4. Prompt'a bağla: {geçmiş_avg, tahmin, rakip_oran, ...}
        5. LLM'ye gönder (PII masked)
        6. LLM yanıtı → RateRecommendation kaydı
        """
        
        # Geçmiş veri
        historical_data = await self._fetch_historical_data(
            input_schema.room_type_id,
            days_back=90,
            db=db,
        )
        
        # Doluluk tahmini
        occupancy_forecast = await self._forecast_occupancy(
            input_schema.room_type_id,
            input_schema.forecast_horizon,
            historical_data,
            db=db,
        )
        
        # Rekabet oranları (mock)
        competitor_rates = await self._get_competitor_rates(
            input_schema.room_type_id,
            db=db,
        )
        
        # Prompt oluştur
        prompt = await self._build_prompt(
            room_type_id=input_schema.room_type_id,
            historical_avg=historical_data["avg_rate"],
            std_dev=historical_data["std_dev"],
            occupancy_forecast=occupancy_forecast,
            competitor_avg=competitor_rates["avg"],
            market_trend=historical_data["trend"],
        )
        
        # LLM çağrı (PII masked)
        llm_client = get_llm_client(self.model_provider)
        masked_prompt, mask_map = await PIIMasker.mask(prompt, context=context)
        
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": masked_prompt}],
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=1500,
        )
        
        llm_output = response["content"]
        unmasked_output = await PIIMasker.unmask(llm_output, mask_map)
        
        # Parse LLM çıktısı → structured recommendation
        recommendation = await self._parse_llm_response(
            llm_output,
            historical_data["current_rate"],
            occupancy_forecast["predicted_occupancy"],
        )
        
        # Kaydet
        rate_rec = RateRecommendation(
            room_type_id=input_schema.room_type_id,
            date=datetime.utcnow().date() + timedelta(days=1),
            recommended_rate=recommendation.recommended_rate,
            current_rate=historical_data["current_rate"],
            price_change_percent=recommendation.price_change_percent,
            rationale=recommendation.rationale,
            confidence_score=recommendation.confidence,
            historical_avg_rate=historical_data["avg_rate"],
            occupancy_forecast=occupancy_forecast["predicted_occupancy"],
            demand_trend=historical_data["trend"],
            competitor_avg_rate=competitor_rates["avg"],
            status="suggested",
            created_by=user.id,
        )
        db.add(rate_rec)
        await db.commit()
        
        return RevenueQAOutput(
            recommendation_id=rate_rec.id,
            recommended_rate=rate_rec.recommended_rate,
            rationale=rate_rec.rationale,
            confidence=rate_rec.confidence_score,
        )
    
    async def _fetch_historical_data(self, room_type_id: UUID, days_back: int, db: AsyncSession) -> dict:
        """Geçmiş 90 gün: ortalama ücret, trend, StdDev."""
        from_date = datetime.utcnow().date() - timedelta(days=days_back)
        
        # Reservation'lardan ücret verisi çek
        result = await db.execute("""
            SELECT AVG(CAST(folio_items.amount AS NUMERIC)) as avg_rate,
                   STDDEV_POP(CAST(folio_items.amount AS NUMERIC)) as std_dev,
                   COUNT(*) as booking_count
            FROM reservations
            JOIN folio_items ON reservations.id = folio_items.reservation_id
            WHERE reservations.room_id IN (SELECT id FROM rooms WHERE room_type_id = :room_type_id)
              AND reservations.checkin_date >= :from_date
        """, {"room_type_id": room_type_id, "from_date": from_date})
        
        row = result.one()
        
        # Trend (son 30 gün vs önceki 30 gün)
        recent = await db.execute("""...""")  # son 30 gün ort.
        previous = await db.execute("""...""")  # önceki 30 gün ort.
        
        trend = "high" if recent > previous * 1.05 else ("low" if recent < previous * 0.95 else "medium")
        
        # Mevcut ücret (güncel rate plan)
        current_rate = await self._get_current_rate(room_type_id, db)
        
        return {
            "avg_rate": row.avg_rate or Decimal(0),
            "std_dev": row.std_dev or Decimal(0),
            "current_rate": current_rate,
            "trend": trend,
        }
    
    async def _forecast_occupancy(self, room_type_id: UUID, horizon_days: int, historical_data: dict, db: AsyncSession) -> dict:
        """
        ARIMA/exponential smoothing model (basit).
        Geçmiş doluluk → gelecek horizon_days günün tahminini yap.
        """
        # Mock-first: sabit tavsiye
        if ENABLE_MOCK:
            return {"predicted_occupancy": 68.0, "confidence": 0.75}
        
        # Gerçek: ARIMA model
        from statsmodels.tsa.arima.model import ARIMA
        
        # Geçmiş doluluk serisi al (90 gün)
        occupancy_series = await self._get_occupancy_series(room_type_id, db)
        
        # Model eğit
        model = ARIMA(occupancy_series, order=(1, 1, 1))
        fitted = model.fit()
        
        # Tahmin
        forecast = fitted.get_forecast(steps=horizon_days)
        predicted_occupancy = forecast.predicted_mean.iloc[-1]
        
        return {
            "predicted_occupancy": float(predicted_occupancy),
            "confidence": 0.85,
        }
    
    async def _get_competitor_rates(self, room_type_id: UUID, db: AsyncSession) -> dict:
        """
        Mock-first: rakip oranları tablosundan oku.
        Gerçek: Booking.com/Expedia scraping (Faz 2 sonu, şimdi mock).
        """
        # CompetitorRate tablosundan son 7 gün ort.
        result = await db.execute("""
            SELECT AVG(CAST(surveyed_rate AS NUMERIC)) as avg_rate
            FROM competitor_rates
            WHERE room_type_id = :room_type_id
              AND survey_date >= CURRENT_DATE - INTERVAL '7 days'
        """, {"room_type_id": room_type_id})
        
        row = result.one()
        return {"avg": row.avg_rate or Decimal(0)}
    
    async def _build_prompt(self, **kwargs) -> str:
        """Prompt template'i değişkenlerle doldur."""
        template = PromptLoader.load("revenue_qa", "1.0.0")
        return template.format(**kwargs)
    
    async def _parse_llm_response(self, llm_output: str, current_rate: Decimal, forecast_occupancy: float) -> dict:
        """LLM çıktısından tavsiye oranını ve gerekçeyi ayıkla."""
        # Basit regex veya JSON parsing
        # LLM yanıtı: "Önerilen ücret: 450 TL çünkü ... doluluk tahmini %68 ..."
        # Parse et → {recommended_rate, rationale, confidence}
        
        import re
        match = re.search(r"Önerilen.*?(\d+)", llm_output)
        recommended = Decimal(match.group(1)) if match else current_rate
        
        return {
            "recommended_rate": recommended,
            "price_change_percent": float((recommended - current_rate) / current_rate * 100) if current_rate else 0,
            "rationale": llm_output[:200],  # İlk 200 char
            "confidence": 0.75,
        }
```

### 2.2 Input/Output şemaları
```python
class RevenueQAInput(BaseModel):
    room_type_id: UUID
    forecast_horizon: int = 7         # kaç gün ilerisi için tahmin

class RevenueQAOutput(BaseModel):
    recommendation_id: UUID
    recommended_rate: Decimal
    rationale: str
    confidence: float
```

---

## 3. Endpoints

### 3.1 Ücret önerisi — `backend/app/routers/ai.py`
```python
@router.post("/ai/revenueqa/recommend-rate", tags=["AI", "Revenue"])
async def recommend_rate(
    req: RateRecommendationRequest,  # {room_type_id}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    RevenueQA agent'ı çalıştır.
    → Ücret tavsiyesi + tahmini doluluk + kanal analizi
    """
    if not has_role(current_user, ["manager", "revenue_manager", "superadmin"]):
        raise HTTPException(status_code=403)
    
    agent = registry.get_agent("revenue_qa")
    output = await agent.execute(
        RevenueQAInput(room_type_id=req.room_type_id),
        context={...},
        db=db,
        user=current_user,
    )
    
    return {
        "recommendation_id": output.recommendation_id,
        "recommended_rate": output.recommended_rate,
        "rationale": output.rationale,
        "confidence": output.confidence,
    }

@router.get("/ai/revenueqa/recommendations", tags=["AI", "Revenue"])
async def get_rate_recommendations(
    room_type_id: UUID | None = None,
    status: str = "suggested",
    limit: int = 20,
    ...
) -> list[dict]:
    """Son X ücret tavsiyesini listele."""
    pass

@router.patch("/ai/revenueqa/recommendations/{recommendation_id}/approve", tags=["AI", "Revenue"])
async def approve_recommendation(
    recommendation_id: UUID,
    apply_immediately: bool = False,
    ...
) -> dict:
    """
    Tavsiye onayla.
    apply_immediately=true → rate_plan güncellemesini tetikle.
    """
    pass
```

### 3.2 Doluluk tahmini — `backend/app/routers/ai.py`
```python
@router.get("/ai/revenueqa/forecast", tags=["AI", "Revenue"])
async def get_occupancy_forecast(
    room_type_id: UUID | None = None,
    horizon: int = 90,
    ...
) -> dict:
    """
    Doluluk tahmini.
    Yanıt: {date, predicted_occupancy, confidence, actual_occupancy (gerçekleştiyse)}
    """
    pass
```

### 3.3 Kanal optimizasyonu — `backend/app/routers/ai.py`
```python
@router.post("/ai/revenueqa/channel-optimize", tags=["AI", "Revenue"])
async def optimize_channel_rates(
    req: ChannelOptimizeRequest,  # {channel_id, room_type_id}
    ...
) -> dict:
    """
    Belirli kanal için ücret optimizasyonu.
    OTA'daki kanal-spesifik kuralları dikkate al.
    """
    pass
```

### 3.4 Alarm sistemi — `backend/app/routers/ai.py`
```python
@router.get("/ai/revenueqa/alerts", tags=["AI", "Revenue"])
async def get_revenue_alerts(
    severity: Literal["critical", "warning", "info"] | None = None,
    limit: int = 50,
    ...
) -> list[dict]:
    """
    Gelir problemleri (anomali) listele:
    - Rezervasyon sayısı beklenenden %20 az
    - Boş odalar fazla (LOS kısa rezervasyonlar)
    - Rekabet oranlarında ani düşüş (price war)
    - Channel performance degradation
    """
    pass

@router.post("/ai/revenueqa/alerts/{alert_id}/acknowledge", tags=["AI", "Revenue"])
async def acknowledge_alert(alert_id: UUID, ...) -> dict:
    """Alert'i okundu olarak işaretle."""
    pass
```

---

## 4. Alert Tablosu

### 4.1 Revenue alert — `backend/app/models/revenue_alert.py`
```python
class RevenueAlert(BaseModel):
    __tablename__ = "revenue_alerts"
    
    id: UUID
    alert_type: str               # "low_occupancy", "competition_drop", "channel_issue"
    severity: str                 # "critical", "warning", "info"
    room_type_id: UUID | None
    channel_id: UUID | None
    
    message: str                  # "Oda tipi A'da doluluk tahmine göre %20 düşük"
    detected_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: UUID | None  # FK: users
    
    context: dict                 # JSON: {"occupancy": 45.0, "expected": 68.0, ...}
    
    created_at: datetime
```

---

## 5. Testler — `backend/tests/test_revenue_qa.py`

### 5.1 Agent mock test
- Mock modu: agent çalıştırılıp recommendation döner
- Input → output schema doğrulama

### 5.2 Ücret önerisi endpoint
- POST /ai/revenueqa/recommend-rate → recommendation_id döner
- Yanıt: {recommended_rate, rationale, confidence}

### 5.3 Doluluk tahmini
- Geçmiş doluluk verisi → ARIMA/mock model
- Tahmin ±5% güven aralığında

### 5.4 Kanal optimizasyonu
- Channel-spesifik kuralları dikkate al
- OTA'daki min/max LOS vs ücret tavsiyesi uyumlu

### 5.5 Alert sistem
- Anomali tespit: doluluk %20 düşük → alert oluşturulur
- Alert acknowledge endpoint

---

## 6. Teslim dosyaları
```
### FILE: backend/app/models/rate_recommendation.py
### FILE: backend/app/models/occupancy_forecast.py
### FILE: backend/app/models/competitor_rate.py
### FILE: backend/app/models/revenue_alert.py
### FILE: backend/app/core/agents/revenue_qa.py
### FILE: backend/app/core/llm/prompts/v1.0.0/revenue_qa.txt
### FILE: backend/app/routers/ai.py                (RevenueQA endpoint'leri ekle)
### FILE: backend/tests/test_revenue_qa.py
### FILE: backend/alembic/versions/xxx_revenue_tables.py  (migration)
```

---

## 7. Kabul kriterleri
- `backend/tests/test_revenue_qa.py` yeşil (mock agent, endpoint, forecast, alert)
- RevenueQA agent BaseAgent miras alır, registry'ye kayıtlı
- POST /ai/revenueqa/recommend-rate → recommendation döner (confidence, rationale)
- Ücret tavsiyesi geçmiş veriye dayalı (avg, trend)
- Doluluk tahmini: ARIMA mock-first (gerçek model v1.1+)
- Alert sistem: anomali tespit ediliyor (low_occupancy, competition_drop)
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (RevenueQA endpoint'leri açıklanır)
