"""Integration Hub — Payment, e-Invoice, GDS, IoT, Voice, Blockchain.

Models: PaymentTransaction, EInvoice, IntegrationSetting, GDS, IoT,
        Voice, BlockchainIdentity.
Routers: payments, einvoice, gds, iot, voice_webhooks, blockchain, security.
Connectors: iyzico, stripe, paytr, craftgate, foriba, logo, uyumsoft, izibiz.

Facade — fiziksel kod app/{models,routers,services} altinda kalir.
"""

MODELS = [
    "app.models.payment_transaction",
    "app.models.integration_setting",
]

ROUTERS = [
    "app.routers.payments",
    "app.routers.einvoice",
    "app.routers.gds",
    "app.routers.integrations",
    "app.routers.security",
]

SERVICES = [
    "app.services.payment_service",
    "app.services.einvoice_service",
    "app.services.integration_service",
]

CONNECTORS = [
    "app.services.payment_connectors",
    "app.services.einvoice_connectors",
]
