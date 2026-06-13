"""Guest Experience — CRM, Messaging, Loyalty.

Models: CRM (Segment, Campaign, GuestNote, CommunicationLog),
        LoyaltyAccount, Complaint, Feedback, ChatSession.
Routers: crm, loyalty, whatsapp, complaints, feedback.
Consumes: ReservationCreated -> welcome, CheckOutCompleted -> feedback.

Facade — fiziksel kod app/{models,routers,services} altinda kalir.
"""

MODELS = [
    "app.models.crm",
]

ROUTERS = [
    "app.routers.crm",
    "app.routers.whatsapp",
]

SERVICES = [
    "app.services.crm_service",
    "app.services.whatsapp_service",
]
