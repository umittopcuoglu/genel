---
id: TASK-012
modül: Modül 8 AI (GuestAI Chatbot — WhatsApp)
kapsam: WhatsApp entegrasyonu + konuşma oturumu + AI yanıt + paket önerisi + yorum cevabı
durum: kuyrukta (bağımlılık: TASK-007 AI core, TASK-011 CRM)
tur: —
bağımlılık: TASK-007 (AI core), TASK-011 (guest 360, feedback)
---

# TASK-012 — GuestAI Chatbot (WhatsApp)

> Misafirlerle WhatsApp üzerinden sohbet. Misafir 360 bağlamında AI yardımı.
> Ek hizmet önerileri, şikayet takibi, yorum yanıtı taslağı.
> PII maskelemesi (KVKK) tüm LLM çağrılarında.
> Mock-first: WhatsApp API test, gerçek integrasyonu Faz 2 sonu.

---

## 1. WhatsApp Entegrasyonu

### 1.1 Webhook alıcı — `backend/app/routers/integrations.py`
```python
@router.post("/integrations/whatsapp/webhook", tags=["Integrations"])
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    WhatsApp'tan gelen mesajları al (Meta Messenger API).
    İmza doğrulama (HMAC-SHA256) → oturum oluştur/güncelle → AI yanıt ver.
    """
    payload = await request.json()
    
    # İmza doğrulama
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_whatsapp_signature(payload, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Meta webhook challenge (kurulum sırasında)
    if "hub.challenge" in payload:
        return {"challenge": payload["hub.challenge"]}
    
    # Gelen mesaj
    entry = payload.get("entry", [{}])[0]
    messaging = entry.get("messaging", [])
    
    for event in messaging:
        sender_id = event.get("sender", {}).get("id")  # WhatsApp phone number ID
        message = event.get("message", {})
        text = message.get("text", {}).get("body", "")
        
        if not text or not sender_id:
            continue
        
        # Misafiri bul (WhatsApp number → guest)
        guest = await db.execute("""
            SELECT g.* FROM guests g
            WHERE g.phone = :phone
        """, {"phone": sender_id})
        guest = guest.scalars().first()
        
        if not guest:
            # Bilinmeyen misafir
            response_text = "Merhaba! HotelOps'e hoşgeldiniz. Sizin hakkınızda bilgimiz yok; lütfen resepsiyon ile iletişime geçin."
            await send_whatsapp_message(sender_id, response_text)
            continue
        
        # Oturum oluştur/güncelle
        session = await db.execute("""
            SELECT * FROM chat_sessions
            WHERE guest_id = :guest_id AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """, {"guest_id": guest.id})
        session = session.scalars().first()
        
        if not session or (datetime.utcnow() - session.updated_at).seconds > 3600:
            # Yeni oturum (1 saatlik inaktivite sonrası)
            session = ChatSession(
                guest_id=guest.id,
                status="active",
                context={},  # Guest 360 bilgisi eklenir
                created_at=datetime.utcnow(),
            )
            db.add(session)
            await db.flush()
        
        # Mesaj kaydı
        user_message = ChatMessage(
            chat_session_id=session.id,
            role="user",
            content=text,
            created_at=datetime.utcnow(),
        )
        db.add(user_message)
        await db.flush()
        
        # AI yanıt oluştur (async background task)
        asyncio.create_task(process_chat_message(session.id, guest.id, text, db))
        
        # Hızlı cevap gönder ("yazıyor..." göstergesi)
        await send_whatsapp_message(sender_id, "⏳ İşleniyor, lütfen bekleyin...")
        
        await db.commit()
    
    return {"status": "ok"}

def verify_whatsapp_signature(payload: dict, signature: str) -> bool:
    """HMAC-SHA256 imza doğrulama."""
    import hmac
    import hashlib
    import json
    
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    body = json.dumps(payload, separators=(',', ':'))
    expected_signature = "sha256=" + hmac.new(
        app_secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

async def send_whatsapp_message(phone_number_id: str, text: str) -> bool:
    """WhatsApp'a mesaj gönder (mock-first)."""
    if ENABLE_MOCK:
        # Mock: log ve başarı dönüş
        return True
    
    # Gerçek: Meta Messenger API
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number_id,
        "type": "text",
        "text": {"body": text},
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            return resp.status == 200
```

### 1.2 Mesaj işleme (background) — `backend/app/services/chat_service.py`
```python
async def process_chat_message(
    session_id: UUID,
    guest_id: UUID,
    user_text: str,
    db: AsyncSession,
):
    """
    1. Guest 360 context al
    2. GuestAI agent'ı çalıştır (LLM → yanıt)
    3. Yanıt veritabanına kaydet
    4. WhatsApp'a gönder
    """
    try:
        # Guest 360 bağlamı
        guest_profile = await Guest360Service.get_guest_profile(guest_id, db)
        
        # GuestAI agent'ı çalıştır
        agent = registry.get_agent("guest_ai")
        
        chat_input = GuestAIChatInput(
            user_message=user_text,
            guest_context=guest_profile,
        )
        
        response = await agent.execute(
            chat_input,
            context={"guest_360": guest_profile},
            db=db,
            user=None,  # Sistem tarafından
        )
        
        # Yanıt kaydı
        ai_message = ChatMessage(
            chat_session_id=session_id,
            role="assistant",
            content=response.message,
            created_at=datetime.utcnow(),
        )
        db.add(ai_message)
        
        # Session context güncelle
        session = await db.get(ChatSession, session_id)
        session.updated_at = datetime.utcnow()
        session.context["last_ai_response"] = response.message
        
        await db.commit()
        
        # WhatsApp'a gönder
        guest = await db.get(Guest, guest_id)
        await send_whatsapp_message(guest.phone, response.message)
        
    except Exception as e:
        # Error handling: log + user'a error mesajı
        error_message = "Üzgünüz, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        guest = await db.get(Guest, guest_id)
        await send_whatsapp_message(guest.phone, error_message)
```

---

## 2. GuestAI Agent

### 2.1 Agent sınıfı — `backend/app/core/agents/guest_ai.py`
```python
class GuestAIAgent(BaseAgent):
    """Misafir sohbet danışmanı."""
    
    agent_name = "guest_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"
    
    async def execute(
        self,
        input_schema: GuestAIChatInput,
        context: dict = None,
        db: AsyncSession = None,
        user: User = None,
    ) -> GuestAIChatOutput:
        """
        1. Misafir 360 bağlamını kur
        2. Konuşma tarihçesini al
        3. Prompt'ı oluştur (bağlam + geçmiş)
        4. LLM'ye gönder (PII masked)
        5. Yanıt geri dön
        """
        
        guest_profile = context.get("guest_360", {})
        
        # Konuşma tarihçesi (son 10 mesaj)
        conversation_history = await db.execute("""
            SELECT role, content FROM chat_messages
            WHERE chat_session_id IN (
                SELECT id FROM chat_sessions WHERE guest_id = :guest_id
            )
            ORDER BY created_at DESC LIMIT 10
        """, {"guest_id": guest_profile["basic"]["id"]})
        
        messages = [
            {
                "role": row.role,
                "content": row.content,
            }
            for row in conversation_history.all()
        ]
        
        # İlk mesajı başa ekle (sistemi koşullandır)
        system_message = await self._build_system_prompt(guest_profile)
        
        # Prompt oluştur
        template = PromptLoader.load("guest_ai", "1.0.0")
        full_prompt = template.format(
            guest_name=guest_profile["basic"]["name"],
            loyalty_tier=guest_profile["loyalty"]["tier"],
            last_stay_date=guest_profile["stays"]["last_checkout"],
            complaint_count=guest_profile["feedback"]["complaint_count"],
            current_message=input_schema.user_message,
        )
        
        # PII maskele
        masked_prompt, mask_map = await PIIMasker.mask(full_prompt, context=guest_profile)
        
        # LLM çağrı
        llm_client = get_llm_client(self.model_provider)
        
        llm_messages = [
            {"role": "system", "content": system_message},
            *[
                {"role": m["role"], "content": m["content"]}
                for m in reversed(messages[-10:])  # Son 10 mesaj
            ],
            {"role": "user", "content": masked_prompt},
        ]
        
        response = await llm_client.chat_completion(
            messages=llm_messages,
            model="deepseek-chat",
            temperature=0.8,  # Biraz creative
            max_tokens=500,
        )
        
        llm_output = response["content"]
        unmasked_output = await PIIMasker.unmask(llm_output, mask_map)
        
        # Yanıt analiz et (paket önerisi, şikayet tespit, vb.)
        suggestions = await self._extract_suggestions(unmasked_output)
        
        return GuestAIChatOutput(
            message=unmasked_output,
            suggestions=suggestions,
        )
    
    async def _build_system_prompt(self, guest_profile: dict) -> str:
        """Sistem koşullandırması."""
        return f"""
        Sen HotelOps misafir asistanısın.
        Misafirin adı: {guest_profile['basic']['name']}
        Loyalty seviyesi: {guest_profile['loyalty']['tier']}
        Önceki konaklamalar: {guest_profile['stays']['total_stays']}
        
        Kurallar:
        - Samimi ve yardımcı ol
        - Oda numarası gibi hassas bilgiler iste (check-in'de doğrulamak için)
        - Teknik sorunlar için resepsiyon'a yönlendir
        - Şikayet varsa empati göster ve manager'a aktar
        """
    
    async def _extract_suggestions(self, response: str) -> dict:
        """Yanıttan önerileri ayıkla (paket, upgrade, vb.)."""
        # Basit NLP: response'ta "upgrade", "paket", "indirim" varsa flag et
        suggestions = {
            "has_upsell_opportunity": "upgrade" in response.lower() or "paket" in response.lower(),
            "has_complaint": "şikayet" in response.lower() or "sorun" in response.lower(),
            "requires_manager_attention": False,
        }
        
        return suggestions
```

### 2.2 Input/Output şemaları
```python
class GuestAIChatInput(BaseModel):
    user_message: str
    guest_context: dict  # Guest 360 profile

class GuestAIChatOutput(BaseModel):
    message: str
    suggestions: dict  # upsell, complaint, manager_attention flags
```

---

## 3. Konuşma Saklama

### 3.1 Chat session — `backend/app/models/chat_session.py`
```python
class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"
    
    id: UUID
    guest_id: UUID                    # FK: guests
    
    status: str                       # 'active', 'closed'
    context: dict                     # JSON: last_ai_response, detected_sentiment, etc.
    
    created_at: datetime
    updated_at: datetime
```

### 3.2 Chat mesajı — `backend/app/models/chat_message.py`
```python
class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"
    
    id: UUID
    chat_session_id: UUID             # FK: chat_sessions
    
    role: str                         # 'user', 'assistant'
    content: str
    
    # Sentiment analizi (optional)
    sentiment: str | None             # 'positive', 'negative', 'neutral'
    
    created_at: datetime
```

---

## 4. Özel Özellikler

### 4.1 Paket önerisi — `backend/app/routers/ai.py`
```python
@router.post("/ai/guestai/personalize", tags=["AI", "Guest"])
async def personalize_package_recommendation(
    req: PersonalizeRequest,  # {reservation_id}
    ...
) -> dict:
    """
    Misafirin profili/tercihlerine göre ek paket önerisi.
    Örn: şehir turu, spa, resepsiyon'da sarı kırtasiye vb.
    """
    pass
```

### 4.2 Yorum yanıt taslağı — `backend/app/routers/ai.py`
```python
@router.post("/ai/guestai/review-respond", tags=["AI", "Guest"])
async def generate_review_response(
    req: ReviewResponseRequest,  # {feedback_id}
    ...
) -> dict:
    """
    Olumsuz yorum'a yapılacak response taslağı oluştur.
    Manager onay sonrası yayınla.
    """
    pass
```

### 4.3 Sentiment tespiti — `backend/app/services/sentiment_analysis.py`
```python
async def analyze_sentiment(text: str) -> str:
    """Mesajın duyarlılığını tespit et (basit regex veya LLM)."""
    # Basit: negative keyword arayışı
    negative_words = ["kötü", "sorun", "çok kötü", "berbat", "şikayet"]
    if any(word in text.lower() for word in negative_words):
        return "negative"
    
    positive_words = ["harika", "çok iyi", "mükemmel", "beğendim", "teşekkür"]
    if any(word in text.lower() for word in positive_words):
        return "positive"
    
    return "neutral"
```

### 4.4 Manager bildirimi (WS) — `backend/app/services/chat_service.py`
```python
async def process_chat_message(...):
    # ... AI yanıt ...
    
    # Negative sentiment veya complaint → manager'a WS bildir
    sentiment = await analyze_sentiment(user_text)
    
    if sentiment == "negative" or response.suggestions["has_complaint"]:
        await emit_guest_ai_alert(
            event={
                "type": "guestai.negative_sentiment",
                "guest_name": guest.name,
                "message": user_text,
                "sentiment": sentiment,
                "session_id": session_id,
            }
        )
```

---

## 5. Endpoints

### 5.1 Chat — `backend/app/routers/chat.py`
```python
@router.post("/ai/guestai/chat", tags=["AI", "Guest"])
async def chat(
    req: ChatRequest,  # {reservation_id, message}
    ...
) -> dict:
    """Misafir sohbeti (WhatsApp'tan yönlendirilir)."""
    # process_chat_message() çalışır → yanıt döner
    pass

@router.get("/chat/sessions/{guest_id}", tags=["Chat"])
async def get_chat_sessions(
    guest_id: UUID,
    ...
) -> list[dict]:
    """Misafirin chat oturumları."""
    pass

@router.get("/chat/sessions/{session_id}/messages", tags=["Chat"])
async def get_chat_messages(
    session_id: UUID,
    ...
) -> list[dict]:
    """Oturumdaki mesajlar."""
    pass
```

---

## 6. Testler — `backend/tests/test_guest_ai.py`

### 6.1 WhatsApp webhook
- İmza doğrulaması: geçerli imza → mesaj işlenir
- İmza geçersiz → 403 hatası
- Unknown guest → "resepsiyon ile iletişime geçin" mesajı

### 6.2 GuestAI agent
- Agent çalıştırılıp yanıt döner
- PII masked → LLM → unmasked
- Sentiment tespiti çalışır

### 6.3 Chat session
- Yeni mesaj → yeni session oluşturulur
- 1 saatlik inaktivite sonrası yeni session
- Konuşma tarihçesi kaydedilir

### 6.4 Sentiment analizi
- Negatif mesaj → "negative"
- Olumlu mesaj → "positive"
- Tarafsız → "neutral"

### 6.5 Manager bildirimi
- Negatif sentiment → WS event yayınlanır
- Manager dashboard'da görünür

---

## 7. Teslim dosyaları
```
### FILE: backend/app/models/chat_session.py
### FILE: backend/app/models/chat_message.py
### FILE: backend/app/core/agents/guest_ai.py
### FILE: backend/app/core/llm/prompts/v1.0.0/guest_ai.txt
### FILE: backend/app/services/chat_service.py
### FILE: backend/app/services/sentiment_analysis.py
### FILE: backend/app/routers/integrations.py            (WhatsApp webhook)
### FILE: backend/app/routers/chat.py
### FILE: backend/app/routers/ai.py                      (paket önerisi, yorum yanıtı)
### FILE: backend/tests/test_guest_ai.py
### FILE: backend/alembic/versions/xxx_chat_tables.py  (migration: chat_sessions, chat_messages)
### FILE: backend/.env.example                          (WHATSAPP_API_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_BUSINESS_ACCOUNT_ID)
```

---

## 8. Kabul kriterleri
- `backend/tests/test_guest_ai.py` yeşil (webhook, agent, session, sentiment)
- WhatsApp webhook: imza doğrulama çalışır
- GuestAI agent BaseAgent miras alır, registry kayıtlı
- Chat session: aktif session yeniden kullanılır (1 saat ön koşulu)
- Konuşma tarihçesi kaydedilir (son 10 mesaj)
- PII maskeleme: LLM'ye gönderilmeden mask edilir
- Sentiment analizi: negatif → manager bildirimi (WS)
- Mock modu: WhatsApp API mock dönüş verir
- review.py PASS (model/audit/error-format/RBAC/soft-delete)
- OpenAPI Türkçe (GuestAI endpoint'leri açıklanır)
