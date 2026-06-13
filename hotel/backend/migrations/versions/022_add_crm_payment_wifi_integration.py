"""Add merge-gap tables: integration_settings, guest_wifi_sessions, CRM (segment/
campaign/guest_note/communication_log), payment_transactions.

Bu tablolar iki geliştirme kolunun birleştirilmesinden sonra modellerde mevcuttu
ama migration zincirinde eksikti (testler create_all kullandığı için gizli kalmıştı).
Migration 014 ayrıca 010 yerine 013'e relink edildi (çoklu-head onarımı).

Revision ID: 022
Revises: 021
Create Date: 2026-06-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_columns():
    """BaseModel ortak sütunları (id + timestamps + audit + soft-delete)."""
    return [
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # ── integration_settings (payment_transactions bunu referans alır) ──
    op.create_table(
        "integration_settings",
        *_base_columns(),
        sa.Column("integration_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("params_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_ok", sa.Boolean(), nullable=True),
        sa.Column("last_test_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_integration_settings_integration_type"),
        "integration_settings", ["integration_type"], unique=False,
    )

    # ── guest_wifi_sessions ──
    op.create_table(
        "guest_wifi_sessions",
        *_base_columns(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("guest_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("wifi_password", sa.String(length=255), nullable=False),
        sa.Column("ssid", sa.String(length=255), nullable=False, server_default="HotelOps-Guest"),
        sa.Column("mac_address", sa.String(length=17), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="active"),
        sa.Column("terms_accepted", sa.Boolean(), nullable=True, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guest_wifi_sessions_email"),
        "guest_wifi_sessions", ["email"], unique=False,
    )

    # ── crm_segments ──
    op.create_table(
        "crm_segments",
        *_base_columns(),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ── crm_campaigns (FK → crm_segments) ──
    op.create_table(
        "crm_campaigns",
        *_base_columns(),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="email"),
        sa.Column("subject", sa.String(length=200), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("segment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delivered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["segment_id"], ["crm_segments.id"]),
    )

    # ── crm_guest_notes (FK → guests) ──
    op.create_table(
        "crm_guest_notes",
        *_base_columns(),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="general"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(
        op.f("ix_crm_guest_notes_guest_id"),
        "crm_guest_notes", ["guest_id"], unique=False,
    )

    # ── crm_communication_logs (FK → guests, crm_campaigns) ──
    op.create_table(
        "crm_communication_logs",
        *_base_columns(),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False, server_default="outbound"),
        sa.Column("subject", sa.String(length=200), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="sent"),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["crm_campaigns.id"]),
    )
    op.create_index(
        op.f("ix_crm_communication_logs_guest_id"),
        "crm_communication_logs", ["guest_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crm_communication_logs_campaign_id"),
        "crm_communication_logs", ["campaign_id"], unique=False,
    )

    # ── payment_transactions (FK → folios, reservations, integration_settings, self) ──
    op.create_table(
        "payment_transactions",
        *_base_columns(),
        sa.Column("folio_id", UUID(as_uuid=True), nullable=True),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("integration_id", UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="charge"),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="pending"),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
        sa.Column("provider_ref", sa.String(length=120), nullable=True),
        sa.Column("parent_txn_id", UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("card_brand", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["folio_id"], ["folios.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["integration_id"], ["integration_settings.id"]),
        sa.ForeignKeyConstraint(["parent_txn_id"], ["payment_transactions.id"]),
    )
    op.create_index(op.f("ix_payment_transactions_folio_id"), "payment_transactions", ["folio_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_reservation_id"), "payment_transactions", ["reservation_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_integration_id"), "payment_transactions", ["integration_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_provider"), "payment_transactions", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_transactions_status"), "payment_transactions", ["status"], unique=False)
    op.create_index(op.f("ix_payment_transactions_provider_ref"), "payment_transactions", ["provider_ref"], unique=False)
    op.create_index("ix_payment_txn_provider_ref", "payment_transactions", ["provider", "provider_ref"], unique=False)


def downgrade() -> None:
    op.drop_table("payment_transactions")
    op.drop_table("crm_communication_logs")
    op.drop_table("crm_guest_notes")
    op.drop_table("crm_campaigns")
    op.drop_table("crm_segments")
    op.drop_table("guest_wifi_sessions")
    op.drop_table("integration_settings")
