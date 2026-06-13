"""Distribution Layer — Channel Manager.

Models: Channel, ChannelMapping, ChannelSyncLog, OverbookingRule.
Connectors: BookingConnector, ExpediaConnector, AgodaConnector.
Consumes: ReservationCreated -> push to all OTAs.

Facade — fiziksel kod app/{models,routers,services} altinda kalir.
"""

MODELS = [
    "app.models.channel",
]

ROUTERS = [
    "app.routers.channels",
]

SERVICES = [
    "app.services.channel_sync_service",
    "app.services.connectors",
]

CONNECTORS = [
    "app.services.connectors.booking",
    "app.services.connectors.expedia",
    "app.services.connectors.agoda",
]
