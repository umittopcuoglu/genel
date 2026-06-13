"""
FrontDesk AI (temel) — Check-in asistanı.
Mock-first: misafir profili (sadakat/VIP/konaklama) → kişiselleştirilmiş karşılama,
oda/upgrade önerisi, upsell fırsatları ve öncelik sınıfı üretir (deterministik).
"""
from typing import Optional
from pydantic import BaseModel
from app.core.agents.base import BaseAgent


class FrontDeskInput(BaseModel):
    guest_name: str
    loyalty_tier: str = "none"          # none / silver / gold / platinum
    is_vip: bool = False
    nights: int = 1
    requested_room_type: str = "standard"
    available_upgrade: Optional[str] = None   # örn. "deluxe", "suite"
    special_requests: list[str] = []


class FrontDeskOutput(BaseModel):
    greeting: str
    priority: str                        # vip / high / normal
    room_recommendation: str
    upsell_suggestions: list[str]
    notes: list[str]


_TIER_RANK = {"none": 0, "silver": 1, "gold": 2, "platinum": 3}


class FrontDeskAIAgent(BaseAgent):
    agent_name = "frontdesk_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self, input_schema: FrontDeskInput, context=None, db=None, user=None
    ) -> FrontDeskOutput:
        tier = input_schema.loyalty_tier.lower()
        rank = _TIER_RANK.get(tier, 0)

        # ── Öncelik sınıfı ──
        if input_schema.is_vip or rank >= 3:
            priority = "vip"
        elif rank == 2:
            priority = "high"
        else:
            priority = "normal"

        # ── Kişiselleştirilmiş karşılama ──
        if priority == "vip":
            greeting = (
                f"Sayın {input_schema.guest_name}, tekrar hoş geldiniz! "
                f"VIP misafirimiz olarak konaklamanız özenle hazırlandı."
            )
        elif priority == "high":
            greeting = (
                f"Sayın {input_schema.guest_name}, hoş geldiniz! "
                f"Gold üyeliğiniz için teşekkür ederiz."
            )
        else:
            greeting = f"Sayın {input_schema.guest_name}, otelimize hoş geldiniz!"

        # ── Oda / upgrade önerisi ──
        notes: list[str] = []
        if input_schema.available_upgrade and priority in ("vip", "high"):
            kind = "ücretsiz" if priority == "vip" else "indirimli"
            room_recommendation = (
                f"{input_schema.available_upgrade.title()} odaya {kind} yükseltme önerin "
                f"(istenen: {input_schema.requested_room_type})."
            )
            notes.append(f"Upgrade uygun: {input_schema.available_upgrade} ({kind}).")
        elif input_schema.available_upgrade:
            room_recommendation = (
                f"{input_schema.requested_room_type.title()} oda atanır; "
                f"{input_schema.available_upgrade} için ücretli yükseltme teklif edilebilir."
            )
        else:
            room_recommendation = f"{input_schema.requested_room_type.title()} oda ataması uygun."

        # ── Upsell fırsatları ──
        upsell: list[str] = []
        if input_schema.requested_room_type.lower() == "standard":
            upsell.append("Kahvaltı paketi ekleme")
        if input_schema.nights >= 3:
            upsell.append("Spa/wellness paketi (3+ gece)")
        if rank >= 2:
            upsell.append("Geç check-out (sadakat ayrıcalığı)")
        if input_schema.nights >= 5:
            upsell.append("Havalimanı transferi")
        if not upsell:
            upsell.append("Oda servisi / minibar tanıtımı")

        # ── Özel istek notları ──
        for req in input_schema.special_requests:
            notes.append(f"Özel istek: {req}")

        return FrontDeskOutput(
            greeting=greeting,
            priority=priority,
            room_recommendation=room_recommendation,
            upsell_suggestions=upsell,
            notes=notes,
        )
