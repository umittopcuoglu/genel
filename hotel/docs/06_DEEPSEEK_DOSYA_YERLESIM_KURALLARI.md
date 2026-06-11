# DeepSeek — Dosya Yerleşim ve Şema Sözleşmesi (ZORUNLU)

> Bu dosyayı her görevin başında DeepSeek'e ver. Üç farklı bilgisayardan
> çalışıldığı için dosyaların **yanlış dizine/yanlış adla** eklenmesi en sık
> hatadır. Aşağıdaki kurallar bunu önler.

---

## 0. Depo ve Dal (her zaman aynı)

- **Repo:** `umittopcuoglu/genel`
- **Çalışma dalı:** `claude/ecstatic-gates-paa35d`
- **Backend kök dizini:** `hotel/backend/`  ← TÜM kod buraya
- **Dosya yolları HER ZAMAN `hotel/backend/` ile başlar.** Asla repo köküne,
  asla `~/Desktop/...` gibi mutlak yola, asla başka uygulamaya (openclaw, claudex…) yazma.

---

## 1. Dizin Haritası — Ne Nereye

| İçerik | Dizin | Örnek |
|---|---|---|
| SQLAlchemy modelleri | `hotel/backend/app/models/` | `maintenance.py` |
| API router'ları (endpoint) | `hotel/backend/app/routers/` | `maintenance.py` |
| İş mantığı servisleri | `hotel/backend/app/services/` | `maintenance_service.py` |
| AI ajanları | `hotel/backend/app/core/agents/` | `techcare_ai.py` |
| Pydantic şemaları | `hotel/backend/app/schemas/` | `maintenance.py` |
| Dış entegrasyon adaptörleri | `hotel/backend/integrations/<tip>/` | `integrations/pos/simphony.py` |
| Alembic migration | `hotel/backend/migrations/versions/` | `010_add_maintenance.py` |
| Testler | `hotel/backend/tests/test_modules/` | `test_maintenance.py` |

---

## 2. MEVCUT Dosyalar — ÜZERİNE YAZMA, YENİDEN ADLANDIRMA

Bu dosyalar zaten var ve çalışıyor. Yeni modül eklerken bunlara **dokunma**,
sadece gerekiyorsa import et:

**Modeller** (`app/models/`):
`base.py` (BaseModel + GUIDString), `user.py`, `audit.py`,
`front_office.py` (RoomType, Room, Guest, Reservation, Stay, Trace),
`reservation_ext.py` (RatePlan, Availability),
`finance.py` (Folio, FolioItem, Payment, NightAuditRun),
`housekeeping.py` (HousekeepingTask, LostFound, MinibarItem),
`channel*.py`, `chart_of_accounts.py`, `ledger_entry.py`, `einvoice.py`,
`budget.py`, `loyalty_*.py`, `complaint.py`, `feedback.py`, `chat_*.py`,
`custom_report.py`, `occupancy_forecast.py`, `overbooking_rule.py`,
`rate_recommendation.py`, `ai_invocation.py`

**Önemli:** Oda/misafir/rezervasyon/folio modelleri ZATEN `front_office.py` ve
`finance.py` içinde. `room.py`, `guest.py`, `reservation.py`, `folio.py` diye
**YENİ dosya AÇMA** — import et:
```python
from app.models.front_office import Room, Guest, Reservation, RoomType, Stay
from app.models.finance import Folio, FolioItem, Payment
from app.models.housekeeping import HousekeepingTask
```

---

## 3. ŞEMA SÖZLEŞMESİ — Alan Adları (KESİN)

Bu adları aynen kullan (paralel teslimatlarda en çok burada hata oldu):

| Model | Doğru alanlar | YANLIŞ (kullanma) |
|---|---|---|
| `Guest` | `first_name`, `last_name`, `email`, `phone` | ~~name~~ |
| `Reservation` | `check_in`, `check_out`, `guest_id`, `status` | ~~checkin_date/checkout_date~~ |
| `Folio` | `total`, `balance`, `status`, `closed_date` | ~~total_amount~~ |
| `Room` | `room_number`, `floor`, `room_type_id`, `status` | ~~room_no~~ |

---

## 4. MODEL YAZIM KURALLARI (SQLAlchemy 2.0 — zorunlu)

1. **Her model `BaseModel`'den türer** (`from app.models.base import BaseModel`).
   BaseModel otomatik sağlar: `id` (Uuid), `created_at`, `updated_at`,
   `created_by`, `updated_by`, `deleted_at` (soft-delete). Bunları TEKRAR tanımlama.

2. **Tip anotasyonu HER ZAMAN `Mapped[...]`** içinde olmalı:
   ```python
   name: Mapped[str] = mapped_column(String(100))          # DOĞRU
   name: str = mapped_column(String(100))                   # YANLIŞ (hata verir)
   ```

3. **UUID Foreign Key kolonlarında AÇIK `Uuid` tipi** kullan (SQLite testleri için şart):
   ```python
   from sqlalchemy import Uuid, ForeignKey
   guest_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("guests.id"))   # DOĞRU
   guest_id: Mapped[UUID] = mapped_column(ForeignKey("guests.id"))          # YANLIŞ (UUID binding hatası)
   ```

4. **Para/ondalık için `Numeric`** (sqlalchemy'de `Decimal` YOKTUR):
   ```python
   from sqlalchemy import Numeric
   price: Mapped[Decimal] = mapped_column(Numeric(12, 2))   # from decimal import Decimal (Python tarafı)
   ```

5. **JSON için dialect-bağımsız variant** (Postgres + SQLite test uyumu):
   ```python
   from sqlalchemy import JSON
   from sqlalchemy.dialects.postgresql import JSONB
   JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")
   data: Mapped[dict] = mapped_column(JSON_VARIANT, nullable=True)
   ```
   Saf `JSONB` KULLANMA (SQLite testte patlar).

6. **`created_by`/`updated_by`'a UUID atanacaksa** BaseModel'deki `GUIDString`
   zaten UUID veya str kabul eder — ekstra bir şey yapma.

7. Yeni modeli **`app/models/__init__.py`'ye import satırı olarak ekle**
   (create_all'ın tabloyu görmesi için).

---

## 5. ROUTER / SERVİS / AI KURALLARI

- **Router:** `APIRouter(prefix="/<modul>", tags=["..."])`, async fonksiyonlar,
  `get_db` + `get_current_user` bağımlılıkları, RBAC: `require_roles([...])`.
  Yeni router'ı `app/main.py`'ye `app.include_router(..., prefix="/api/v1")` ile ekle.
- **Hata zarfı:** `{"error": {"code": "...", "message": "...", "details": {...}}}`.
- **Servis:** statik async metotlar, `db: AsyncSession` parametresi, iş mantığı burada.
- **AI ajanı:** `BaseAgent`'tan türer (`app/core/agents/base.py`), `registry`'ye
  `init_agents.py` içinde kaydedilir, LLM çağrısı `get_llm_client()` ile,
  PII `PIIMasker.mask()` ile maskelenir. Test ortamı `ENABLE_LLM_MOCK=true` ile mock'a düşer.
- **Dış servisler (POS/GDS/IoT/kilit) mock-first:** `integrations/<tip>/base.py`
  soyut adaptör + `<saglayici>.py` mock implementasyon. Gerçek anahtar `.env`'den.

---

## 6. MIGRATION KURALLARI

- Dosya adı sıradaki numarayla: **bir sonraki numara `010`** (mevcut zincir 001→009 dolu).
- `revision` ve `down_revision` ZİNCİRİ kopmamalı:
  ```python
  revision = "010"
  down_revision = "009"   # bir önceki migration
  ```
- Aynı numarayı/revision'ı İKİ kez kullanma (alembic "multiple heads" hatası verir).

---

## 7. ÇIKTI FORMATI (run_task.py bunu bekler)

Her dosyayı şu başlıkla ver — yol `hotel/backend/` ile başlamalı:

```
### FILE: hotel/backend/app/models/maintenance.py
\`\`\`python
<dosyanın tam içeriği>
\`\`\`

### FILE: hotel/backend/app/routers/maintenance.py
\`\`\`python
...
\`\`\`
```

> Not: `run_task.py` yalnızca `backend/` ve `docs/api/` altına yazmaya izin verir.
> Başka yol reddedilir.

---

## 8. KABUL KRİTERLERİ (her görev)

- [ ] Dosyalar doğru dizinde, doğru adla (Bölüm 1-2)
- [ ] Modeller §4 kurallarına uygun (Mapped, açık Uuid, Numeric, JSON variant)
- [ ] Yeni model `__init__.py`'ye eklendi
- [ ] Router `main.py`'ye bağlandı, RBAC + hata zarfı var
- [ ] Migration zinciri kopuk değil (010, down_revision=009)
- [ ] Min. test sayısı yazıldı, `pytest backend/tests` yeşil
- [ ] OpenAPI açıklamaları Türkçe
