"""Revenue & Pricing — AI Engine.

Models: RateRecommendation, OccupancyForecast, OverbookingRule.
Router: revenue.
Produces: RateRecommended (future).

Facade — fiziksel kod app/{models,routers,services} altinda kalir.
"""

MODELS = [
    "app.models.reservation",  # RatePlan, Availability
]

ROUTERS = [
    "app.routers.revenue",
]

SERVICES = [
    "app.services.revenue_service",
]
