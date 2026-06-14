"""PMS Core — System of Record.

Models: Room, Reservation, Guest, Stay, RatePlan, Availability,
        Housekeeping, Folio, Payment, Groups, Maintenance.
Routers: front_office, reservations, rate_plans, availability,
         folios, night_audit, housekeeping, groups, maintenance.
Events produced: ReservationCreated, ReservationCancelled,
                 CheckInCompleted, CheckOutCompleted, RoomStatusChanged.

Facade — fiziksel kod app/{models,routers,services} altinda kalir.
Import: from app.contexts.pms_core import models, routers
"""

MODELS = [
    "app.models.front_office",
    "app.models.housekeeping",
    "app.models.reservation",
    "app.models.groups",
    "app.models.maintenance",
]

ROUTERS = [
    "app.routers.front_office",
    "app.routers.reservations",
    "app.routers.rate_plans",
    "app.routers.availability",
    "app.routers.folios",
    "app.routers.night_audit",
    "app.routers.housekeeping",
    "app.routers.groups",
    "app.routers.maintenance",
]

SERVICES = [
    "app.services.night_audit_service",
]
