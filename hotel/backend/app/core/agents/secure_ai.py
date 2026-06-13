"""
TASK-017 — SecureAI: Erişim log anomali taraması + olay özeti.
Mock-first: reddedilen erişimlerin tekrarına göre risk skoru.
"""
from pydantic import BaseModel
from app.core.agents.base import BaseAgent


class AccessEvent(BaseModel):
    area: str
    result: str  # granted / denied
    hour: int = 12  # 0-23


class SecureAIInput(BaseModel):
    events: list[AccessEvent] = []


class Anomaly(BaseModel):
    area: str
    denied_count: int
    risk: str
    reason: str


class SecureAIOutput(BaseModel):
    anomalies: list[Anomaly]
    total_events: int
    summary: str


class SecureAIAgent(BaseAgent):
    agent_name = "secure_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def execute(
        self, input_schema: SecureAIInput, context=None, db=None, user=None
    ) -> SecureAIOutput:
        # Bölge bazlı reddedilen erişim sayımı (gece saatleri ağırlıklı)
        denied: dict[str, int] = {}
        night_denied: dict[str, int] = {}
        for ev in input_schema.events:
            if ev.result == "denied":
                denied[ev.area] = denied.get(ev.area, 0) + 1
                if ev.hour >= 0 and ev.hour < 6:
                    night_denied[ev.area] = night_denied.get(ev.area, 0) + 1

        anomalies: list[Anomaly] = []
        for area, count in denied.items():
            is_night = night_denied.get(area, 0) > 0
            if count >= 3:
                risk = "high" if is_night else "medium"
            elif count == 2:
                risk = "medium" if is_night else "low"
            else:
                continue
            anomalies.append(Anomaly(
                area=area,
                denied_count=count,
                risk=risk,
                reason=f"{count} reddedilen erişim{' (gece saatleri)' if is_night else ''}.",
            ))

        anomalies.sort(key=lambda a: a.denied_count, reverse=True)
        summary = (
            f"{len(anomalies)} anomali tespit edildi."
            if anomalies else "Anormal erişim deseni tespit edilmedi."
        )
        return SecureAIOutput(
            anomalies=anomalies,
            total_events=len(input_schema.events),
            summary=summary,
        )
