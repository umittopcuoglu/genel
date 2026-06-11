---
id: TASK-007
modül: Altyapı & AI (Ortak AI Çekirdeği)
kapsam: BaseAgent soyutlaması + LLM sağlayıcı adaptörü + prompt versiyonlama + PII maskeleme + AI invocations tablosu
durum: kuyrukta (Faz 2 önkoşulu)
tur: —
bağımlılık: TASK-006 (tamamlandı)
---

# TASK-007 — Ortak AI Çekirdeği

> Faz 2'deki tüm AI ajanlarının (RevenueIQ, GuestAI, InsightAI, FrontDesk) temeli.
> BaseAgent sınıfı, LLM sağlayıcı soyutlaması (DeepSeek/OpenAI/Claude), prompt registry,
> PII maskeleme (KVKK uyumluluğu) ve invocation logging.

---

## 1. BaseAgent Soyutlaması

### 1.1 Ajan kaydı ve registry — `backend/app/core/agents/base.py`
```python
class BaseAgent(ABC):
    """Tüm AI ajanları bu sınıfı miras alır."""
    
    agent_name: str          # 'revenue_qa', 'guest_ai', 'insight_ai', 'frontdesk_ai'
    model_provider: str      # 'deepseek', 'openai', 'claude'
    prompt_version: str      # '1.0.0' — versiyonlanır
    
    async def execute(
        self,
        input_schema: BaseModel,    # pydantic modeli
        context: dict = None,       # misafir 360, rezilme vb.
    ) -> BaseModel:                 # output_schema
        """Ajan çağrısının entrypoint."""
        pass
    
    async def _mask_pii(self, text: str) -> str:
        """PII maskeleme."""
        pass
```

### 1.2 Ajan registry — `backend/app/core/agents/registry.py`
- `register_agent(agent_instance)` — runtime'da kaydol
- `get_agent(agent_name: str)` — lookup
- `list_agents()` → `{agent_name: agent_instance}`

### 1.3 Input/output şemaları
- Her agent'ın `InputSchema` ve `OutputSchema` BaseModel'i
- OpenAPI doc'larına otomatik entegrasyon (endpoint'lerde basit Pydantic çağrısı)

---

## 2. LLM Sağlayıcı Adaptörü

### 2.1 LLM client soyutlaması — `backend/app/core/llm/client.py`
```python
class LLMClient(ABC):
    """OpenAI uyumlu API interface."""
    
    async def chat_completion(
        self,
        messages: list[dict],     # [{"role": "user", "content": "..."}]
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> dict:                    # {"content": "...", "stop_reason": "..."}
        """DeepSeek/OpenAI/Claude'e uyumlu chat çağrısı."""
        pass

class DeepSeekClient(LLMClient):
    """api.deepseek.com adaptörü."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"

class OpenAIClient(LLMClient):
    """OpenAI adaptörü."""
    pass

class ClaudeClient(LLMClient):
    """Anthropic API adaptörü."""
    pass
```

### 2.2 Factory pattern — `backend/app/core/llm/factory.py`
```python
def get_llm_client(provider: str) -> LLMClient:
    """
    .env'den provider seç (LLM_PROVIDER=deepseek|openai|claude).
    API anahtarı .env'den (DEEPSEEK_API_KEY, OPENAI_API_KEY, CLAUDE_API_KEY).
    """
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    if provider == "deepseek":
        return DeepSeekClient(os.getenv("DEEPSEEK_API_KEY"))
    # ...
```

### 2.3 Mock modu test için — `backend/app/core/llm/mock.py`
- `MockLLMClient`: deterministic yanıtlar (test sabit çıktılar)
- `ENABLE_LLM_MOCK=true` → mock kullanır (CI/CD'de)

---

## 3. Prompt Versiyonlama

### 3.1 Prompt deposu — `backend/app/core/llm/prompts/`
```
prompts/
├── v1.0.0/
│   ├── revenue_qa.txt      # RevenueIQ prompt
│   ├── guest_ai.txt        # GuestAI prompt
│   ├── insight_ai.txt      # InsightAI prompt
│   └── frontdesk_ai.txt    # FrontDesk AI prompt (TASK-002 güncelle)
├── v1.1.0/                 # Gelecek iterasyon
└── current -> v1.0.0       # Sembolik bağlantı
```

### 3.2 Prompt loader — `backend/app/core/llm/prompt_loader.py`
```python
class PromptLoader:
    @staticmethod
    def load(agent_name: str, version: str = "current") -> str:
        """prompts/ deposundan agent'ın prompt template'i yükle."""
        path = f"core/llm/prompts/{version}/{agent_name}.txt"
        with open(path) as f:
            return f.read()
```

### 3.3 Prompt template değişkenleri
```
# prompts/v1.0.0/revenue_qa.txt
Siz HotelOps sisteminin gelir danışmanısınız.
Misafir: {guest_name}
Oda: {room_number}
Konaklama tarihleri: {checkin} — {checkout}
Mevcut ücret: {current_rate} TL
Ortalama iştgal: {avg_occupancy}%

Tavsiye: (yaklaşık {max_tokens} kelime)
```

---

## 4. PII Maskeleme (KVKK)

### 4.1 Maskeleme engine — `backend/app/core/security/pii_masker.py`
```python
class PIIMasker:
    """Misafir adı, TC kimlik, telefon, e-mail vb. LLM'e gönderilmeden maskelenir."""
    
    MASK_PATTERNS = {
        "ad": r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b",
        "telefon": r"\b(?:\+90|0)[0-9]{10}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "tc": r"\b[0-9]{11}\b",
    }
    
    @staticmethod
    async def mask(text: str, context: dict = None) -> tuple[str, dict]:
        """
        PII'yi [MASKED_GUEST_NAME], [MASKED_PHONE] vb. değiştirir.
        context: {"guest_name": "Ahmet Yılmaz", ...} → maskeleme haritasını döndür
        """
        masked_text = text
        mask_map = {}
        for pii_type, pattern in PIIMasker.MASK_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                placeholder = f"[MASKED_{pii_type.upper()}_{len(mask_map)}]"
                masked_text = masked_text.replace(match, placeholder, 1)
                mask_map[placeholder] = match
        
        return masked_text, mask_map
    
    @staticmethod
    async def unmask(llm_response: str, mask_map: dict) -> str:
        """LLM yanıtındaki placeholders'ı gerçek değerlerle değiştir."""
        result = llm_response
        for placeholder, original in mask_map.items():
            result = result.replace(placeholder, original)
        return result
```

### 4.2 Ajan entegrasyonu
- `BaseAgent.execute()` çağrıldığında: input → `PIIMasker.mask()` → LLM → `PIIMasker.unmask()`

---

## 5. AI Invocations Tablosu & Logging

### 5.1 Model — `backend/app/models/ai_invocation.py`
```python
class AIInvocation(BaseModel):
    __tablename__ = "ai_invocations"
    
    id: UUID
    agent_name: str              # 'revenue_qa', 'guest_ai', ...
    input_tokens: int            # prompt token sayısı
    output_tokens: int           # completion token sayısı
    total_cost: Decimal          # token fiyatı × token sayısı
    latency_ms: int              # LLM çağrısı süresi (ms)
    status: str                  # 'success', 'error', 'timeout'
    error_message: str | None    # hata varsa
    llm_response: str            # LLM çıktısı (masked)
    model_provider: str          # 'deepseek', 'openai', 'claude'
    prompt_version: str          # '1.0.0'
    
    created_by: UUID             # çağrı yapan user
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 5.2 Logging wrapper — `backend/app/core/llm/client.py`
```python
class LLMClient(ABC):
    async def chat_completion(self, ...):
        start = time.time()
        try:
            response = await self._call_api(...)  # DeepSeek/OpenAI çağrısı
            latency_ms = int((time.time() - start) * 1000)
            
            # Invocation kaydı
            invocation = AIInvocation(
                agent_name=context.get("agent_name"),
                input_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=response.get("usage", {}).get("completion_tokens", 0),
                total_cost=self._calc_cost(...),
                latency_ms=latency_ms,
                status="success",
                llm_response=response["content"],
                model_provider=self.provider,
                prompt_version=context.get("prompt_version", "1.0.0"),
                created_by=current_user.id,
            )
            db.add(invocation)
            await db.commit()
            
            return response
        except Exception as e:
            # Error invocation kaydı
            ...
```

### 5.3 Maliyet hesaplaması — `backend/app/core/llm/pricing.py`
```python
PRICING = {
    "deepseek": {
        "input": 0.14 / 1_000_000,    # $ per token
        "output": 0.28 / 1_000_000,
    },
    "openai": {
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-3.5": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
    },
}

def calc_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Tokena göre maliyeti hesapla."""
    rates = PRICING.get(provider, {})
    input_cost = input_tokens * rates.get("input", 0)
    output_cost = output_tokens * rates.get("output", 0)
    return input_cost + output_cost
```

---

## 6. FrontDesk AI (TASK-002) Taşınması

### 6.1 Mevcut endpoint'i güncelleştir — `backend/app/routers/ai.py`
```python
@router.post("/ai/frontdesk/auto-checkin")
async def frontdesk_auto_checkin(
    req: FrontDeskAIInput,  # {reservation_id, override_room_assignment}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    FrontDesk AI agent'ı çalıştır.
    1. Rezervasyon + misafir 360 context'i al
    2. BaseAgent.execute() → LLM → oda önerisi
    3. AIInvocation kaydet
    """
    agent = registry.get_agent("frontdesk_ai")
    output = await agent.execute(req, context={...}, db=db, user=current_user)
    return output.dict()
```

---

## 7. Testler — `backend/tests/test_ai_core.py`

### 7.1 BaseAgent test
- MockAgent (test amaçlı) kaydı
- `registry.get_agent()` dönüş değerini kontrol et
- Agent input/output schema'sı doğrulama

### 7.2 LLM client test
- Mock modu: `ENABLE_LLM_MOCK=true` → MockLLMClient döner
- Real modu (optional): DeepSeekClient → API çağrısı (test key ile)
- Token sayma doğruluğu
- Maliyet hesaplaması

### 7.3 PII maskeleme test
- Giriş: "Ahmet Yılmaz +90500123456 ahmet@example.com"
- Beklenen: "[MASKED_AD_0] [MASKED_TELEFON_1] [MASKED_EMAIL_2]"
- Unmask: ters dönüşüm

### 7.4 AIInvocation logging
- LLM çağrısı → `ai_invocations` tablosunda kayıt
- Hata senaryosu: timeout/API hatası → status='error', error_message kaydedilir

### 7.5 PromptLoader
- Prompt dosyası yüklenir
- Template değişkenleri değiştirilir (f-string veya Jinja2)

---

## 8. Teslim dosyaları
```
### FILE: backend/app/core/agents/__init__.py
### FILE: backend/app/core/agents/base.py
### FILE: backend/app/core/agents/registry.py
### FILE: backend/app/core/llm/__init__.py
### FILE: backend/app/core/llm/client.py
### FILE: backend/app/core/llm/factory.py
### FILE: backend/app/core/llm/mock.py
### FILE: backend/app/core/llm/prompt_loader.py
### FILE: backend/app/core/llm/pricing.py
### FILE: backend/app/core/llm/prompts/v1.0.0/revenue_qa.txt
### FILE: backend/app/core/llm/prompts/v1.0.0/guest_ai.txt
### FILE: backend/app/core/llm/prompts/v1.0.0/insight_ai.txt
### FILE: backend/app/core/llm/prompts/v1.0.0/frontdesk_ai.txt
### FILE: backend/app/core/security/pii_masker.py
### FILE: backend/app/models/ai_invocation.py
### FILE: backend/app/routers/ai.py                (FrontDesk AI endpoint'i taşı, BaseAgent'a çevir)
### FILE: backend/tests/test_ai_core.py
### FILE: backend/alembic/versions/xxx_ai_invocations.py  (migration)
### FILE: backend/.env.example                      (LLM_PROVIDER, DEEPSEEK_API_KEY, OPENAI_API_KEY, CLAUDE_API_KEY, ENABLE_LLM_MOCK)
```

---

## 9. Kabul kriterleri
- `backend/tests/test_ai_core.py` yeşil (mock modu)
- `BaseAgent` miras alan MockAgent yazılıp registry'ye kaydedilir
- `PIIMasker.mask()` test: giriş maskelenir, unmask() ters çevirme doğru
- `LLMClient` interface'i 3 sağlayıcı (DeepSeek, OpenAI, Claude) tarafından implemente edilir
- `PromptLoader` prompts/ dosyalarından template yükler ve değişken değiştirir
- `ai_invocations` tablosu migration ile oluşturulur; LLM çağrılarında otomatik log
- FrontDesk AI endpoint (`/ai/frontdesk/auto-checkin`) BaseAgent üzerinde çalışır
- review.py PASS (model/audit/error-format/RBAC/soft-delete — all green)
- OpenAPI Türkçe (AI agent endpoint'leri açıklanır)
