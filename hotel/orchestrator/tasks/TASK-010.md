---
id: TASK-010
modül: Modül 4 Genişletme (Tam Muhasebe & GİB e-Fatura)
kapsam: Çift taraflı defter sistemi + TÜRMOB uyumlu muhasebe + e-Fatura üretimi
durum: kuyrukta (bağımlılık: TASK-004)
tur: —
bağımlılık: TASK-004 (Muhasebe MVP tamamlandı)
---

# TASK-010 — Tam Muhasebe & GİB e-Fatura

> Otel muhasebesi: çift taraflı defter (çift girişli) ile uyum.
> TÜRMOB hesap planı, GİB e-Fatura (UBL-TR) entegrasyonu,
> KDV raporlaması, konaklama vergisi, dengeleme ve mali denetim.

---

## 1. Hesap Planı (TÜRMOB Uyumlu)

### 1.1 Muhasebe hesapları — `backend/app/models/chart_of_accounts.py`
```python
class ChartOfAccount(BaseModel):
    __tablename__ = "chart_of_accounts"
    
    id: UUID
    account_code: str                 # "110", "610", "100101" (TÜRMOB standardı)
    account_name: str                 # "Kasa", "Oda Geliri", "Maliyeti Satılan Hizmetler"
    account_type: str                 # 'asset', 'liability', 'equity', 'revenue', 'expense'
    is_main_account: bool             # Esas hesap mı, alt hesap mı
    
    # Balansa katkı
    normal_balance: Literal["debit", "credit"]  # Hesabın normal bakiyesi
    
    # TÜRMOB tasnifi
    balance_sheet_order: int          # Bilançoda görünüş sırası
    income_statement_order: int | None  # Gelir tablosunda sırası
    
    # İnaktif yapma
    is_active: bool = True
    
    created_at: datetime
    updated_at: datetime
```

### 1.2 Seed data — TÜRMOB hesap planı
```
110  | Kasa | asset | debit | active
120  | Banka | asset | debit | active
130  | Dış Ticaret Finansmanı | asset | debit | active
...
610  | Oda Hizmetleri Geliri | revenue | credit | active
611  | Yer Geliri | revenue | credit | active
612  | Resepsiyonda Satılan Hizmetler | revenue | credit | active
...
500  | Maliyeti Satılan Hizmetler | expense | debit | active
520  | Personel Giderleri | expense | debit | active
530  | Yaşlı Hizmet Giderleri | expense | debit | active
...
```

---

## 2. Çift Taraflı Defter Sistemi

### 2.1 Yevmiye kaydı — `backend/app/models/ledger_entry.py`
```python
class LedgerEntry(BaseModel):
    __tablename__ = "ledger_entries"
    
    id: UUID
    
    # Yevmiye başlığı
    journal_name: str                 # "Kasa", "Banka", "Satış", "Alış", "Genel"
    entry_date: date
    entry_number: str                 # Otomatik numara (YYYY-MM-XXXXX)
    description: str                  # "Oda A105 checkin + ek hizmetler"
    
    # Hareketler (çift girişli taraflı kaydı)
    debit_account_id: UUID            # FK: chart_of_accounts
    debit_amount: Decimal             # TL (positive)
    
    credit_account_id: UUID           # FK: chart_of_accounts
    credit_amount: Decimal            # TL (positive)
    
    # Constraint: debit_amount == credit_amount (çift taraflılık)
    
    # Doküman bağlantısı
    source_type: str | None           # 'reservation', 'folio', 'purchase', 'adjustment'
    source_id: UUID | None            # FK: ilgili tablo (reservation, folio, vb.)
    
    # Onay durumu
    status: str                       # 'draft', 'posted', 'reversed'
    posted_by: UUID | None            # FK: users
    posted_at: datetime | None
    
    created_by: UUID                  # FK: users
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 2.2 Posting engine — `backend/app/services/ledger_posting.py`
```python
class LedgerPostingService:
    """Folio → LedgerEntry otomatik dönüştürme."""
    
    @staticmethod
    async def post_folio_closure(folio_id: UUID, db: AsyncSession):
        """
        Folio kapanışında yevmiye kaydı oluştur.
        Örn: Oda A105 gecelik 350 TL + ek hizmetler 50 TL = 400 TL
        
        Debit: Kasa/Banka (110/120) — 400
        Credit: Oda Geliri (610) — 350
        Credit: Ek Hizmetler Geliri (612) — 50
        """
        folio = await db.get(Folio, folio_id)
        
        entries = []
        total_amount = Decimal(0)
        
        for folio_item in folio.items:
            # Item type'ına göre gelir hesabını belirle
            account = await determine_revenue_account(folio_item.type, db)
            
            entries.append({
                "account_id": account.id,
                "amount": folio_item.amount,
                "type": "credit",  # Gelir = credit
            })
            total_amount += folio_item.amount
        
        # Ödeme yöntemi (debit)
        payment_account = await determine_payment_account(folio.payment_method, db)  # Kasa/Banka
        
        # Yevmiye kaydı
        entry = LedgerEntry(
            journal_name="Satış",
            entry_date=datetime.utcnow().date(),
            description=f"Folio #{folio.id} kapanışı - {folio.guest_name}",
            
            debit_account_id=payment_account.id,
            debit_amount=total_amount,
            
            credit_account_id=entries[0]["account_id"],  # İlk gelir hesabı (basit)
            credit_amount=total_amount,
            
            source_type="folio",
            source_id=folio.id,
            status="draft",
            created_by=SYSTEM_USER_ID,
        )
        
        db.add(entry)
        await db.commit()
        
        # Muhasebeci onayından sonra "posted" durumuna geçer
    
    @staticmethod
    async def post_ledger_entry(entry_id: UUID, db: AsyncSession):
        """Yevmiye kaydını deftere "naklet" (posted yapır)."""
        entry = await db.get(LedgerEntry, entry_id)
        
        if entry.status != "draft":
            raise ValueError(f"Entry {entry_id} already posted")
        
        # Constraints kontrol et
        if entry.debit_amount != entry.credit_amount:
            raise ValueError(f"Debit ({entry.debit_amount}) != Credit ({entry.credit_amount})")
        
        entry.status = "posted"
        entry.posted_at = datetime.utcnow()
        await db.commit()
```

---

## 3. KDV ve Özel Vergiler

### 3.1 Vergi oranları — `backend/app/models/tax_rate.py`
```python
class TaxRate(BaseModel):
    __tablename__ = "tax_rates"
    
    id: UUID
    tax_type: str                     # 'kdv', 'konaklama_vergisi', 'turist_harcı'
    rate_percent: float               # 8.0, 18.0, vb.
    
    # Uygulama koşulları
    applies_to_room_type: str | None  # NULL = tüm tip; 'standard', 'suite', vb.
    applies_to_service_type: str | None
    
    effective_date: date
    expiration_date: date | None      # NULL = sürüyor
    
    # Muhasebeleştirme
    revenue_account_id: UUID          # FK: chart_of_accounts (Konaklama Vergisi Hesabı)
    liability_account_id: UUID        # FK: chart_of_accounts (Ödenecek Vergiler)
    
    created_at: datetime
    updated_at: datetime
```

### 3.2 KDV hesaplama — `backend/app/services/tax_calculation.py`
```python
class TaxCalculationService:
    @staticmethod
    async def calculate_kdv(amount: Decimal, kdv_rate: float = 18.0) -> dict:
        """
        Brüt tutar → KDV hesapla.
        Örn: 100 TL + %18 KDV = 118 TL
        """
        net_amount = amount / (1 + kdv_rate / 100)
        kdv_amount = amount - net_amount
        return {
            "net": net_amount,
            "kdv": kdv_amount,
            "gross": amount,
        }
    
    @staticmethod
    async def calculate_konaklama_vergisi(
        room_rate: Decimal,
        num_nights: int,
        city: str,  # Şehir (İstanbul %15, Ankara %5 vb.)
    ) -> dict:
        """
        Konaklama vergisi: belediyelere göre değişir.
        İstanbul: %15, diğer: %0 (örn).
        """
        if city.lower() in ["istanbul", "i̇stanbul"]:
            rate = 0.15
        else:
            rate = 0.0
        
        base = room_rate * num_nights
        tax_amount = base * rate
        
        return {
            "base": base,
            "tax_amount": tax_amount,
            "rate": rate,
        }
```

---

## 4. e-Fatura (GİB Entegrasyonu)

### 4.1 Fatura modeli — `backend/app/models/einvoice.py`
```python
class EInvoice(BaseModel):
    __tablename__ = "einvoices"
    
    id: UUID
    
    # Fatura temel bilgiler
    invoice_number: str               # "2026000001" (GİB format)
    invoice_date: date
    
    # Müşteri
    customer_name: str
    customer_tax_id: str | None       # VKN (11 hane) veya TCKN (11 hane)
    customer_email: str
    
    # Tutar
    subtotal: Decimal                 # Vergi öncesi
    kdv_amount: Decimal
    total_amount: Decimal
    
    # GİB bilgileri
    e_invoice_uuid: str | None        # GİB tarafından verilen UUID
    einvoice_status: str              # 'draft', 'generated', 'sent', 'accepted', 'error'
    xml_content: str | None           # UBL-TR XML
    xml_url: str | None               # GİB'de hosted URL
    pdf_url: str | None               # PDF indirme URL
    pdf_content: bytes | None         # PDF binary
    
    # GİB cevapları
    gib_response_code: str | None     # "UVTSSVSSZVFF" vb.
    gib_error_message: str | None
    
    # Belgeler
    source_folio_id: UUID | None      # FK: folios
    
    created_at: datetime
    updated_at: datetime
```

### 4.2 e-Fatura generator — `backend/app/integrations/einvoice/generator.py`
```python
class EInvoiceGenerator:
    """UBL-TR XML → e-Fatura üretim."""
    
    @staticmethod
    async def generate_invoice_xml(
        folio_id: UUID,
        db: AsyncSession,
    ) -> str:
        """
        Folio'dan UBL-TR uyumlu XML oluştur.
        Struktur:
        <Invoice>
          <cbc:ID>2026000001</cbc:ID>
          <cbc:IssueDate>2026-06-11</cbc:IssueDate>
          <cac:AccountingSupplier...>  <!-- Otel -->
          <cac:AccountingCustomer...>  <!-- Misafir -->
          <cac:InvoiceLine>            <!-- Her satır (oda, ek hizmetler) -->
            <cbc:LineExtensionAmount>350.00</cbc:LineExtensionAmount>
            <cac:Item><cbc:Name>Oda Yüksek Kat - 1 Gece</cbc:Name>
          <cac:Price><cbc:PriceAmount>350.00</cbc:PriceAmount>
        </Invoice>
        """
        folio = await db.get(Folio, folio_id)
        
        # Şablon yükle (Jinja2 veya hardcode)
        xml = await EInvoiceGenerator._build_ubl_xml(folio)
        
        return xml
    
    @staticmethod
    async def _build_ubl_xml(folio: Folio) -> str:
        """Basit UBL-TR builder."""
        # Mock-first: template.xml'i değişkenlerle doldur
        template = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:ID>{invoice_number}</cbc:ID>
  <cbc:IssueDate>{issue_date}</cbc:IssueDate>
  ...
</Invoice>"""
        
        # Replace placeholders
        return template.format(
            invoice_number=folio.folio_number,
            issue_date=datetime.utcnow().date(),
        )
```

### 4.3 GİB entegrasyonu (mock) — `backend/app/integrations/einvoice/gib_client.py`
```python
class GIBClient:
    """GİB e-Fatura webservice (mock-first)."""
    
    async def send_invoice(self, xml_content: str) -> dict:
        """
        XML'i GİB'e gönder.
        Mock: {"gib_uuid": "...", "status": "accepted"}
        Gerçek: SOAP call to e-fatura.gib.gov.tr (Faz 2 sonu)
        """
        if ENABLE_MOCK:
            import uuid
            return {
                "gib_uuid": str(uuid.uuid4()),
                "status": "accepted",
                "response_code": "UVTSSVSSZVFF",
            }
        
        # Gerçek SOAP client (python-zeep)
        # client = zeep.Client(wsdl="https://efatura.gib.gov.tr/...")
        # response = client.service.sendInvoice(xml_content)
        ...
    
    async def get_invoice_status(self, gib_uuid: str) -> dict:
        """GİB'de fatura durumunu sor."""
        pass
    
    async def cancel_invoice(self, gib_uuid: str) -> bool:
        """Faturayı iptal et."""
        pass
```

---

## 5. Endpoints

### 5.1 Hesap planı — `backend/app/routers/accounting.py`
```python
@router.get("/accounting/chart-of-accounts", tags=["Accounting"])
async def get_chart_of_accounts(
    active_only: bool = True,
    ...
) -> list[dict]:
    """Hesap planını listele."""
    pass

@router.post("/accounting/chart-of-accounts", tags=["Accounting"])
async def create_account(
    req: ChartOfAccountCreateRequest,
    current_user: User = Depends(get_current_user),
    ...
) -> dict:
    """Yeni muhasebe hesabı ekle (admin)."""
    if not has_role(current_user, ["superadmin"]):
        raise HTTPException(status_code=403)
    pass
```

### 5.2 Yevmiye kaydı — `backend/app/routers/accounting.py`
```python
@router.post("/accounting/ledger-entries", tags=["Accounting"])
async def create_ledger_entry(
    req: LedgerEntryCreateRequest,
    ...
) -> dict:
    """Yevmiye kaydı oluştur (muhasebeci)."""
    if not has_role(current_user, ["accounting", "manager", "superadmin"]):
        raise HTTPException(status_code=403)
    pass

@router.get("/accounting/ledger", tags=["Accounting"])
async def get_ledger(
    from_date: date,
    to_date: date,
    account_id: UUID | None = None,
    ...
) -> list[dict]:
    """Defteri listele (filtrelenmiş)."""
    pass

@router.patch("/accounting/ledger-entries/{entry_id}/post", tags=["Accounting"])
async def post_ledger_entry(
    entry_id: UUID,
    ...
) -> dict:
    """Yevmiye kaydını deftera naklet."""
    pass

@router.get("/accounting/trial-balance", tags=["Accounting"])
async def get_trial_balance(
    as_of_date: date,
    ...
) -> dict:
    """Mizan: her hesabın debit/credit bakiyesi."""
    pass
```

### 5.3 e-Fatura — `backend/app/routers/einvoice.py`
```python
@router.post("/einvoice/generate", tags=["eInvoice"])
async def generate_invoice(
    req: GenerateInvoiceRequest,  # {folio_id}
    ...
) -> dict:
    """
    Folio'dan e-Fatura üret ve GİB'e gönder.
    Yanıt: {invoice_id, gib_uuid, status, pdf_url}
    """
    pass

@router.get("/einvoice/{invoice_id}", tags=["eInvoice"])
async def get_invoice(invoice_id: UUID, ...) -> dict:
    """Fatura detayları ve indirme URL'ları."""
    pass

@router.post("/einvoice/{invoice_id}/cancel", tags=["eInvoice"])
async def cancel_invoice(invoice_id: UUID, ...) -> dict:
    """Faturayı GİB'de iptal et."""
    pass

@router.get("/einvoice/{invoice_id}/status", tags=["eInvoice"])
async def check_invoice_status(invoice_id: UUID, ...) -> dict:
    """GİB'deki mevcut durumu kontrol et."""
    pass
```

### 5.4 Raporlar — `backend/app/routers/accounting.py`
```python
@router.get("/reports/gop", tags=["Accounting", "Reports"])
async def get_income_statement(
    from_date: date,
    to_date: date,
    ...
) -> dict:
    """Gelir Tablosu (Gider ve Olmayan Gelir)."""
    pass

@router.get("/reports/balance-sheet", tags=["Accounting", "Reports"])
async def get_balance_sheet(
    as_of_date: date,
    ...
) -> dict:
    """Bilanço: Aktif, Pasif, Öz Kaynaklar."""
    pass

@router.get("/reports/kdv-summary", tags=["Accounting", "Reports"])
async def get_kdv_summary(
    from_date: date,
    to_date: date,
    ...
) -> dict:
    """KDV özeti: toplam giriş KDV'si, çıkış KDV'si, net."""
    pass
```

---

## 6. Testler — `backend/tests/test_accounting.py`

### 6.1 Hesap planı
- TÜRMOB hesapları seedlenir
- Account lookup'ları doğru

### 6.2 Yevmiye kaydı
- Folio kapanışı → yevmiye kaydı otomatik oluşturulur
- debit_amount == credit_amount constraint
- Status: draft → posted

### 6.3 KDV hesaplaması
- %18 KDV: 100 TL → 118 TL
- %8 KDV: 100 TL → 108 TL

### 6.4 Konaklama vergisi
- İstanbul %15: 350 TL × 1 gece → 52.5 TL vergi
- İstanbul dışı %0

### 6.5 e-Fatura
- Mock: XML üretilir, gib_uuid atanır
- EInvoice durumu "generated" → "sent" → "accepted"
- PDF URL doldurulur

### 6.6 Raporlar
- Trial Balance: debit toplamı = credit toplamı
- İncome Statement: gelirleri vs giderleri topla
- KDV Summary: özet doğru

---

## 7. Teslim dosyaları
```
### FILE: backend/app/models/chart_of_accounts.py
### FILE: backend/app/models/ledger_entry.py
### FILE: backend/app/models/tax_rate.py
### FILE: backend/app/models/einvoice.py
### FILE: backend/app/services/ledger_posting.py
### FILE: backend/app/services/tax_calculation.py
### FILE: backend/app/integrations/__init__.py
### FILE: backend/app/integrations/einvoice/__init__.py
### FILE: backend/app/integrations/einvoice/generator.py
### FILE: backend/app/integrations/einvoice/gib_client.py
### FILE: backend/app/routers/accounting.py
### FILE: backend/app/routers/einvoice.py
### FILE: backend/tests/test_accounting.py
### FILE: backend/alembic/versions/xxx_accounting_tables.py  (migration: chart_of_accounts, ledger_entries, tax_rates, einvoices)
### FILE: backend/alembic/versions/xxx_seed_chart_of_accounts.py  (data migration: TÜRMOB hesap planı)
### FILE: backend/.env.example                      (ENABLE_MOCK, GIB_WSDL_URL, GIB_USERNAME, GIB_PASSWORD)
```

---

## 8. Kabul kriterleri
- `backend/tests/test_accounting.py` yeşil (CRUD, yevmiye, KDV, konaklama vergisi, e-Fatura, raporlar)
- Folio kapanışında otomatik yevmiye kaydı oluşturulur
- Trial Balance: debit = credit
- e-Fatura: mock modu XML → gib_uuid döner
- KDV ve konaklama vergisi hesaplamalarıı doğru
- Raporlar (GOP, Bilanço, KDV özeti) üretilir
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (Accounting endpoint'leri açıklanır)
