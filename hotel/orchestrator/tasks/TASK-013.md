---
id: TASK-013
modül: Modül 10 (Raporlama & InsightAI)
kapsam: Yönetici dashboard + standart raporlar + custom raporlar + InsightAI özeti + audit yönetimi
durum: kuyrukta (bağımlılık: TASK-007 AI core)
tur: —
bağımlılık: TASK-007 (AI core), TASK-004 (folios, audit log)
---

# TASK-013 — Raporlama & InsightAI

> Operasyonel ve finansal raporlama. Manager dashboard (KPI kartları).
> Standart raporlar (gelişler, gidişler, muhasebe).
> Custom rapor builder (JSON tanım).
> InsightAI: sabah özeti + rakip rate monitoring.

---

## 1. Manager Dashboard

### 1.1 Dashboard API — `backend/app/routers/dashboard.py`
```python
@router.get("/dashboard/manager", tags=["Dashboard"])
async def get_manager_dashboard(
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manager dashboard: KPI kartları + grafikleri.
    Varsayılan: bugün + son 30 gün.
    """
    if not has_role(current_user, ["manager", "superadmin"]):
        raise HTTPException(status_code=403)
    
    from_date = from_date or (datetime.utcnow().date() - timedelta(days=30))
    to_date = to_date or datetime.utcnow().date()
    
    # KPI'ları hesapla
    kpis = await calculate_kpis(from_date, to_date, db)
    
    # Grafik verileri
    occupancy_trend = await get_occupancy_trend(from_date, to_date, db)
    revenue_trend = await get_revenue_trend(from_date, to_date, db)
    
    return {
        "date_range": {"from": from_date, "to": to_date},
        "kpis": kpis,
        "trends": {
            "occupancy": occupancy_trend,
            "revenue": revenue_trend,
        },
    }

async def calculate_kpis(from_date: date, to_date: date, db: AsyncSession) -> dict:
    """
    Anahtar KPI'lar.
    """
    
    # 1. Doluluk (Occupancy)
    total_room_nights = await db.execute(f"""
        SELECT COUNT(*) as total FROM rooms
    """)
    total_rooms = total_room_nights.scalar() or 1
    
    occupied = await db.execute(f"""
        SELECT COUNT(DISTINCT reservation_id) as occupied
        FROM (
            SELECT DISTINCT r.id as reservation_id
            FROM reservations r
            WHERE r.checkin_date <= :to_date AND r.checkout_date > :from_date
                AND r.status NOT IN ('cancelled', 'no_show')
        ) sq
    """, {"from_date": from_date, "to_date": to_date})
    occupied_count = occupied.scalar() or 0
    
    occupancy_percent = (occupied_count / (total_rooms * (to_date - from_date).days + 1)) * 100 if total_rooms else 0
    
    # 2. ADR (Average Daily Rate)
    adr_result = await db.execute(f"""
        SELECT AVG(CAST(folio_items.amount AS NUMERIC)) as adr
        FROM folio_items
        JOIN folios ON folio_items.folio_id = folios.id
        WHERE folios.closed_date BETWEEN :from_date AND :to_date
    """, {"from_date": from_date, "to_date": to_date})
    adr = adr_result.scalar() or 0
    
    # 3. RevPAR (Revenue Per Available Room)
    total_revenue = await db.execute(f"""
        SELECT SUM(CAST(total_amount AS NUMERIC)) as total
        FROM folios
        WHERE closed_date BETWEEN :from_date AND :to_date
    """, {"from_date": from_date, "to_date": to_date})
    total_revenue = total_revenue.scalar() or 0
    
    revpar = (total_revenue / (total_rooms * (to_date - from_date).days + 1)) if total_rooms else 0
    
    # 4. Gelenler / Gidenler
    arrivals = await db.execute(f"""
        SELECT COUNT(*) FROM reservations
        WHERE checkin_date BETWEEN :from_date AND :to_date
          AND status NOT IN ('cancelled', 'no_show')
    """, {"from_date": from_date, "to_date": to_date})
    arrivals_count = arrivals.scalar() or 0
    
    departures = await db.execute(f"""
        SELECT COUNT(*) FROM reservations
        WHERE checkout_date BETWEEN :from_date AND :to_date
          AND status NOT IN ('cancelled', 'no_show')
    """, {"from_date": from_date, "to_date": to_date})
    departures_count = departures.scalar() or 0
    
    # 5. Out of Order (OOO) odalar
    ooo = await db.execute(f"""
        SELECT COUNT(*) FROM room_status_logs
        WHERE status = 'out_of_order'
          AND updated_at BETWEEN :from_date AND :to_date
    """, {"from_date": from_date, "to_date": to_date})
    ooo_count = ooo.scalar() or 0
    
    return {
        "occupancy": {
            "percent": round(occupancy_percent, 1),
            "rooms_occupied": occupied_count,
            "total_rooms": total_rooms,
        },
        "adr": {
            "value": round(float(adr), 2),
            "currency": "TL",
        },
        "revpar": {
            "value": round(float(revpar), 2),
            "currency": "TL",
        },
        "arrivals": arrivals_count,
        "departures": departures_count,
        "ooo_rooms": ooo_count,
    }
```

---

## 2. Standart Raporlar

### 2.1 Gelişler raporu — `backend/app/routers/reports.py`
```python
@router.get("/reports/std/arrivals", tags=["Reports"])
async def get_arrivals_report(
    from_date: date,
    to_date: date,
    room_type_id: UUID | None = None,
    ...
) -> list[dict]:
    """
    Gelişler raporu: check-in listesi.
    Sütunlar: Ad, Email, Telefon, Oda, Check-in Saati, LOS, Rate, Status
    """
    query = """
        SELECT r.id, g.name, g.email, g.phone, ro.number, r.checkin_date,
               (r.checkout_date - r.checkin_date) as los,
               f.total_amount as rate,
               r.status
        FROM reservations r
        JOIN guests g ON r.guest_id = g.id
        JOIN rooms ro ON r.room_id = ro.id
        LEFT JOIN folios f ON r.id = f.reservation_id
        WHERE r.checkin_date BETWEEN :from_date AND :to_date
          AND r.status NOT IN ('cancelled', 'no_show')
    """
    
    if room_type_id:
        query += " AND ro.room_type_id = :room_type_id"
    
    query += " ORDER BY r.checkin_date"
    
    result = await db.execute(query, {
        "from_date": from_date,
        "to_date": to_date,
        "room_type_id": room_type_id,
    })
    
    return [
        {
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "room": row.number,
            "checkin": row.checkin_date,
            "los": row.los.days,
            "rate": row.rate,
            "status": row.status,
        }
        for row in result.all()
    ]

@router.get("/reports/std/departures", tags=["Reports"])
async def get_departures_report(
    from_date: date,
    to_date: date,
    ...
) -> list[dict]:
    """Gidişler raporu (arrivals'a benzer, checkout tarihine göre)."""
    pass

@router.get("/reports/std/cashiering", tags=["Reports"])
async def get_cashiering_report(
    from_date: date,
    to_date: date,
    ...
) -> dict:
    """
    Kasa/Muhasebe raporu:
    - Toplam gelir
    - Ödeme yöntemi bazında breakdown
    - Taksiler, iade
    """
    pass

@router.get("/reports/std/housekeeping", tags=["Reports"])
async def get_housekeeping_report(
    from_date: date,
    to_date: date,
    ...
) -> dict:
    """
    Housekeeping raporu:
    - Görev sayıları (tamamlanan, beklemede)
    - Oda durumları (temiz, kirli, denetim)
    - Personel performansı
    """
    pass
```

---

## 3. Custom Raporlar

### 3.1 Custom rapor modeli — `backend/app/models/custom_report.py`
```python
class CustomReport(BaseModel):
    __tablename__ = "custom_reports"
    
    id: UUID
    name: str                         # "Aylık Gelir Raporu"
    description: str | None
    
    # Rapor tanımı (JSON)
    definition: dict                  # {
                                      #   "source": "reservations|folios|audit_log",
                                      #   "filters": [
                                      #     {"field": "checkin_date", "op": ">=", "value": "..."}
                                      #   ],
                                      #   "groupby": ["status"],
                                      #   "aggregations": [
                                      #     {"field": "total_amount", "agg": "sum"}
                                      #   ],
                                      #   "order_by": [{"field": "checkin_date", "desc": true}]
                                      # }
    
    created_by: UUID                  # FK: users
    created_at: datetime
    updated_at: datetime
```

### 3.2 Custom rapor endpoint — `backend/app/routers/reports.py`
```python
@router.post("/reports/custom", tags=["Reports"])
async def create_custom_report(
    req: CustomReportCreateRequest,  # {name, definition}
    ...
) -> dict:
    """Custom rapor tanımı oluştur."""
    pass

@router.post("/reports/custom/{report_id}/execute", tags=["Reports"])
async def execute_custom_report(
    report_id: UUID,
    params: dict | None = None,  # Filtre overrides
    ...
) -> dict:
    """
    Custom rapor çalıştır.
    JSON definition → SQL sorgusu → sonuç.
    """
    report = await db.get(CustomReport, report_id)
    
    # JSON definition → SQL builder
    query_builder = QueryBuilder(report.definition)
    query = query_builder.build_sql()
    
    # Parametreleri apply et
    if params:
        query_builder.apply_overrides(params)
    
    result = await db.execute(query)
    return {
        "report_name": report.name,
        "definition": report.definition,
        "data": result.all(),
        "generated_at": datetime.utcnow(),
    }
```

---

## 4. Bütçe Varyans Analizi

### 4.1 Bütçe modeli — `backend/app/models/budget.py`
```python
class Budget(BaseModel):
    __tablename__ = "budgets"
    
    id: UUID
    department: str                   # "rooms", "fb", "operations"
    budget_year: int
    budget_month: int
    
    budgeted_revenue: Decimal
    budgeted_expense: Decimal
    
    actual_revenue: Decimal | None
    actual_expense: Decimal | None
    
    variance_percent: float | None    # |(actual-budget)/budget| × 100
    status: str                       # 'draft', 'approved', 'actual_calculated'
    
    created_at: datetime
    updated_at: datetime
```

### 4.2 Bütçe varyans — `backend/app/routers/reports.py`
```python
@router.get("/reports/budget/variance", tags=["Reports"])
async def get_budget_variance(
    year: int,
    month: int | None = None,
    ...
) -> dict:
    """
    Bütçe vs Gerçekleşen karşılaştırması.
    Varyans > %10 → warning flag.
    """
    pass
```

---

## 5. Audit Log Raporlama

### 5.1 Audit raporu — `backend/app/routers/audit.py`
```python
@router.get("/audit/user-activity", tags=["Audit"])
async def get_user_activity_report(
    from_date: date,
    to_date: date,
    user_id: UUID | None = None,
    operation: str | None = None,  # 'CREATE', 'UPDATE', 'DELETE'
    resource_type: str | None = None,  # 'Reservation', 'Folio'
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Zorunlu audit raporu: kim ne yaptı.
    Sütunlar: Tarih, Kullanıcı, Operation, Resource, IP, Status
    """
    if not has_role(current_user, ["manager", "superadmin"]):
        raise HTTPException(status_code=403)
    
    query = """
        SELECT
            id,
            timestamp,
            user_id,
            operation,
            resource_type,
            resource_id,
            ip_address,
            status,
            error_message
        FROM audit_logs
        WHERE timestamp BETWEEN :from_date AND :to_date
    """
    
    params = {"from_date": from_date, "to_date": to_date}
    
    if user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id
    
    if operation:
        query += " AND operation = :operation"
        params["operation"] = operation
    
    if resource_type:
        query += " AND resource_type = :resource_type"
        params["resource_type"] = resource_type
    
    query += " ORDER BY timestamp DESC LIMIT 1000"
    
    result = await db.execute(query, params)
    
    return [
        {
            "timestamp": row.timestamp,
            "user": row.user_id,
            "operation": row.operation,
            "resource": f"{row.resource_type}#{row.resource_id}",
            "ip": row.ip_address,
            "status": row.status,
            "error": row.error_message,
        }
        for row in result.all()
    ]
```

---

## 6. InsightAI

### 6.1 InsightAI Agent — `backend/app/core/agents/insight_ai.py`
```python
class InsightAIAgent(BaseAgent):
    """Operasyonel insights ve öneriler."""
    
    agent_name = "insight_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"
    
    async def execute(
        self,
        input_schema: InsightAIInput,
        context: dict = None,
        db: AsyncSession = None,
        user: User = None,
    ) -> InsightAIOutput:
        """
        1. KPI'ları, bütçe varyansını, anomalileri al
        2. Prompt'ı oluştur
        3. LLM: "Bugün neler dikkat çekici? Ne önerirsin?"
        4. Yanıt: insights + recommendations
        """
        
        # KPI'lar (son 7 gün vs önceki ay)
        kpis_recent = await calculate_kpis(
            datetime.utcnow().date() - timedelta(days=7),
            datetime.utcnow().date(),
            db,
        )
        
        kpis_previous = await calculate_kpis(
            datetime.utcnow().date() - timedelta(days=37),
            datetime.utcnow().date() - timedelta(days=7),
            db,
        )
        
        # Bütçe varyansı
        budget_variance = await db.execute("""
            SELECT
                department,
                AVG(CAST(variance_percent AS NUMERIC)) as avg_variance
            FROM budgets
            WHERE budget_year = EXTRACT(YEAR FROM CURRENT_DATE)
              AND budget_month = EXTRACT(MONTH FROM CURRENT_DATE)
            GROUP BY department
        """)
        
        # Prompt oluştur
        template = PromptLoader.load("insight_ai", "1.0.0")
        
        prompt = template.format(
            occupancy_recent=kpis_recent["occupancy"]["percent"],
            occupancy_previous=kpis_previous["occupancy"]["percent"],
            revpar_recent=kpis_recent["revpar"]["value"],
            revpar_previous=kpis_previous["revpar"]["value"],
            budget_variance="\n".join([
                f"- {row.department}: {row.avg_variance}%"
                for row in budget_variance.all()
            ]),
        )
        
        # LLM çağrı
        llm_client = get_llm_client(self.model_provider)
        masked_prompt, _ = await PIIMasker.mask(prompt)
        
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": masked_prompt}],
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=800,
        )
        
        return InsightAIOutput(
            brief=response["content"],
        )
```

### 6.2 Sabah özeti — `backend/app/routers/ai.py`
```python
@router.post("/ai/insight/daily-brief", tags=["AI", "Reporting"])
async def generate_daily_brief(
    send_email: bool = True,
    ...
) -> dict:
    """
    Sabah özeti: KPI özeti + bugün neler bekleniyor + tavsiyeler.
    send_email=true → manager'a e-posta gönder (mock-first).
    """
    agent = registry.get_agent("insight_ai")
    output = await agent.execute(
        InsightAIInput(),
        db=db,
        user=None,
    )
    
    if send_email:
        # Mock: email log'lanır
        await send_email_to_managers(
            subject="HotelOps Sabah Özeti",
            body=output.brief,
        )
    
    return {
        "brief": output.brief,
        "generated_at": datetime.utcnow(),
    }
```

### 6.3 Rakip rate scanning — `backend/app/routers/ai.py`
```python
@router.post("/ai/insight/competitor-scan", tags=["AI", "Reporting"])
async def scan_competitor_rates(
    ...
) -> dict:
    """
    Rakip otel oranlarını taray (mock-first).
    Faz 2 sonunda: real web scraping + comparison.
    """
    # Mock: sabit rakip oranları döndür
    competitor_data = {
        "timestamp": datetime.utcnow(),
        "competitors": [
            {
                "name": "Otel ABC",
                "rate": 420,
                "vs_ours": -2,  # % farkı
            },
            {
                "name": "Otel XYZ",
                "rate": 450,
                "vs_ours": 5,
            },
        ],
    }
    
    return competitor_data
```

---

## 7. Testler — `backend/tests/test_reporting.py`

### 7.1 Manager dashboard
- KPI'lar hesaplanır (occupancy, ADR, RevPAR)
- Tarih aralığı filtreleme

### 7.2 Standart raporlar
- Gelenler raporu: checkin tarihine göre sırala
- Gidişler raporu: checkout tarihine göre
- Muhasebe raporu: totalleri doğru

### 7.3 Custom raporlar
- Tanım kaydedilir (JSON)
- Execute: SQL oluşturulup çalışır
- Filtre override'ları uygulanır

### 7.4 Bütçe varyans
- Varyans hesaplanır: |(actual-budget)/budget|
- Yüksek varyans flaglenir

### 7.5 Audit raporu
- User activity: operation/resource filtrelenir
- Zorunlu rapor, manager only

### 7.6 InsightAI
- Agent çalıştırılıp özet döner
- Sabah özeti üretilir (mock email)
- Rakip oranlar taranır

---

## 8. Teslim dosyaları
```
### FILE: backend/app/models/custom_report.py
### FILE: backend/app/models/budget.py
### FILE: backend/app/core/agents/insight_ai.py
### FILE: backend/app/core/llm/prompts/v1.0.0/insight_ai.txt
### FILE: backend/app/services/query_builder.py        (JSON def → SQL)
### FILE: backend/app/routers/dashboard.py
### FILE: backend/app/routers/reports.py
### FILE: backend/app/routers/audit.py                 (audit report endpoint'i)
### FILE: backend/app/routers/ai.py                    (InsightAI endpoint'leri ekle)
### FILE: backend/tests/test_reporting.py
### FILE: backend/alembic/versions/xxx_reporting_tables.py  (migration: custom_reports, budgets)
```

---

## 9. Kabul kriterleri
- `backend/tests/test_reporting.py` yeşil (dashboard, std raporlar, custom raporlar, audit, InsightAI)
- Dashboard KPI'ları hesaplanır (occupancy, ADR, RevPAR, arrivals, departures, OOO)
- Standart raporlar: Gelenler, Gidişler, Muhasebe, Housekeeping (data doğru)
- Custom raporlar: JSON tanım → SQL çalışır
- Bütçe varyansı: |(actual-budget)/budget| × 100
- Audit raporu: zorunlu, user/operation/resource filtrelenir
- InsightAI agent: registry'de kayıtlı, özet üretir
- Mock email: sabah özeti "gönderiliyor" (test'te verify edilir)
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (Reporting endpoint'leri açıklanır)
