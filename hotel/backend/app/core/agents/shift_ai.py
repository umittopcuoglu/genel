"""
Shift AI Agent: Vardiya planlaması optimizasyonu için AI asistanı.
Personel sayısı, departman ihtiyaçları ve geçmiş verilere göre
akıllı vardiya önerileri üretir.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.agents.base import BaseAgent
from app.core.llm import get_llm_client
from app.models.hr import Employee, Shift, ShiftAssignment, Attendance
from app.models.user import User


class ShiftAIContext(BaseModel):
    """Shift AI'ın ihtiyaç duyduğu bağlam bilgileri."""
    department: str = Field(..., description="Hedef departman")
    target_date: date = Field(..., description="Planlanacak tarih")
    current_employee_count: int = Field(0, description="Departmandaki aktif personel sayısı")
    available_employees: int = Field(0, description="Müsait personel sayısı")
    expected_occupancy: Optional[float] = Field(None, description="Beklenen doluluk oranı (%)")
    special_events: Optional[list[str]] = Field(None, description="Özel gün/etkinlikler")


class ShiftAIInput(BaseModel):
    """Shift AI girdisi."""
    department: str
    target_date: date
    occupancy_rate: Optional[float] = None
    special_events: Optional[list[str]] = None


class ShiftRecommendation(BaseModel):
    """Vardiya önerisi."""
    shift_name: str
    start_time: str
    end_time: str
    recommended_count: int
    min_count: int
    max_count: int
    reasoning: str


class ShiftAIOutput(BaseModel):
    """Shift AI çıktısı."""
    department: str
    target_date: date
    recommendations: list[ShiftRecommendation]
    total_employees_needed: int
    available_employees: int
    summary: str


class ShiftAIAgent(BaseAgent):
    """Vardiya planlaması ve optimizasyonu için AI ajanı."""
    
    agent_name = "shift_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self,
        input_schema: ShiftAIInput,
        context: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
        user: Optional[User] = None,
    ) -> ShiftAIOutput:
        # Veritabanından gerçek verileri topla
        context_data = await self._gather_context(db, input_schema)
        
        # AI prompt'unu oluştur
        prompt = self._build_prompt(context_data)
        
        # LLM'den yanıt al
        llm_client = get_llm_client(self.model_provider)
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=1000,
        )
        
        llm_output = response["content"]
        
        # LLM çıktısını parse et ve yapılandırılmış çıktıya dönüştür
        return self._parse_output(llm_output, context_data)

    async def _gather_context(
        self, db: AsyncSession, input_data: ShiftAIInput
    ) -> ShiftAIContext:
        """Veritabanından bağlam bilgilerini topla."""
        if db is None:
            return ShiftAIContext(
                department=input_data.department,
                target_date=input_data.target_date,
            )

        # Departmandaki aktif personel sayısı
        emp_stmt = select(func.count(Employee.id)).where(
            and_(
                Employee.department == input_data.department,
                Employee.is_active == True,
            )
        )
        result = await db.execute(emp_stmt)
        total_employees = result.scalar() or 0

        # O tarihte müsait personel (izinli/atamasız olmayanlar)
        # Bu basit bir tahmin; gerçek uygulamada daha karmaşık olabilir
        avail_stmt = select(func.count(Employee.id)).where(
            and_(
                Employee.department == input_data.department,
                Employee.is_active == True,
            )
        )
        result = await db.execute(avail_stmt)
        available = result.scalar() or 0

        return ShiftAIContext(
            department=input_data.department,
            target_date=input_data.target_date,
            current_employee_count=total_employees,
            available_employees=available,
            expected_occupancy=input_data.occupancy_rate,
            special_events=input_data.special_events,
        )

    def _build_prompt(self, ctx: ShiftAIContext) -> str:
        """AI prompt'unu oluştur."""
        events_str = ", ".join(ctx.special_events) if ctx.special_events else "Yok"
        occupancy_str = f"%{ctx.expected_occupancy:.0f}" if ctx.expected_occupancy else "Bilinmiyor"

        return f"""
        Sen HotelOps Shift AI asistanısın. Görevin en uygun vardiya planlamasını yapmaktır.

        **Departman:** {ctx.department}
        **Tarih:** {ctx.target_date}
        **Aktif Personel:** {ctx.current_employee_count}
        **Tahmini Müsait Personel:** {ctx.available_employees}
        **Beklenen Doluluk:** {occupancy_str}
        **Özel Günler/Etkinlikler:** {events_str}

        **Kurallar:**
        1. Otel departmanları için standart vardiya saatlerini kullan:
           - Sabah (Morning): 07:00-15:00
           - Akşam (Evening): 15:00-23:00
           - Gece (Night): 23:00-07:00
        2. Doluluk arttıkça personel ihtiyacı artar.
        3. Her vardiya için minimum 1 personel olmalı.
        4. Özel etkinlikler varsa personel sayısı artırılmalı.
        5. Hafta sonu ve resmi tatillerde akşam vardiyası daha kalabalık olabilir.

        **Yanıt Formatı (JSON):**
        {{
            "recommendations": [
                {{
                    "shift_name": "Morning",
                    "recommended_count": 3,
                    "min_count": 2,
                    "max_count": 5,
                    "reasoning": "Açıklama..."
                }}
            ],
            "total_employees_needed": 10,
            "summary": "Genel değerlendirme..."
        }}

        Sadece JSON yanıtı ver, başka metin ekleme.
        """

    def _parse_output(self, llm_output: str, ctx: ShiftAIContext) -> ShiftAIOutput:
        """LLM çıktısını parse et ve yapılandırılmış yanıt oluştur."""
        import json
        import re

        try:
            # JSON'u temizle ve parse et
            json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(llm_output)

            recommendations = []
            for rec in data.get("recommendations", []):
                recommendations.append(
                    ShiftRecommendation(
                        shift_name=rec.get("shift_name", "Unknown"),
                        start_time=self._get_shift_time(rec.get("shift_name", "Morning"))[0],
                        end_time=self._get_shift_time(rec.get("shift_name", "Morning"))[1],
                        recommended_count=rec.get("recommended_count", 1),
                        min_count=rec.get("min_count", 1),
                        max_count=rec.get("max_count", 3),
                        reasoning=rec.get("reasoning", ""),
                    )
                )

            return ShiftAIOutput(
                department=ctx.department,
                target_date=ctx.target_date,
                recommendations=recommendations,
                total_employees_needed=data.get("total_employees_needed", 0),
                available_employees=ctx.available_employees,
                summary=data.get("summary", "Vardiya planlaması oluşturuldu."),
            )
        except (json.JSONDecodeError, KeyError, AttributeError):
            # Fallback: AI yanıt vermezse varsayılan öneri
            return self._default_output(ctx)

    @staticmethod
    def _get_shift_time(shift_name: str) -> tuple[str, str]:
        """Vardiya adına göre başlangıç ve bitiş saatini döndür."""
        times = {
            "Morning": ("07:00", "15:00"),
            "Evening": ("15:00", "23:00"),
            "Night": ("23:00", "07:00"),
        }
        return times.get(shift_name, ("09:00", "18:00"))

    @staticmethod
    def _default_output(ctx: ShiftAIContext) -> ShiftAIOutput:
        """AI yanıt vermezse kullanılacak varsayılan çıktı."""
        base_count = max(1, ctx.available_employees // 3)
        
        return ShiftAIOutput(
            department=ctx.department,
            target_date=ctx.target_date,
            recommendations=[
                ShiftRecommendation(
                    shift_name="Morning",
                    start_time="07:00",
                    end_time="15:00",
                    recommended_count=base_count,
                    min_count=1,
                    max_count=base_count + 1,
                    reasoning="Varsayılan sabah vardiyası planlaması.",
                ),
                ShiftRecommendation(
                    shift_name="Evening",
                    start_time="15:00",
                    end_time="23:00",
                    recommended_count=base_count,
                    min_count=1,
                    max_count=base_count + 1,
                    reasoning="Varsayılan akşam vardiyası planlaması.",
                ),
                ShiftRecommendation(
                    shift_name="Night",
                    start_time="23:00",
                    end_time="07:00",
                    recommended_count=max(1, base_count // 2),
                    min_count=1,
                    max_count=base_count,
                    reasoning="Varsayılan gece vardiyası planlaması.",
                ),
            ],
            total_employees_needed=base_count * 2 + max(1, base_count // 2),
            available_employees=ctx.available_employees,
            summary="AI yanıtı alınamadı, varsayılan vardiya planlaması kullanıldı.",
        )
