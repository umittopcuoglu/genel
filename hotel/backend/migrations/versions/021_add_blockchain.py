"""Add Blockchain Identity / SSI tables for TASK-025

Revision ID: 021
Revises: 020
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── blockchain_identities ──
    op.create_table("blockchain_identities",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("did", sa.String(length=200), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False, server_default="polygon"),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("private_key_encrypted", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("chain_tx_hash", sa.String(length=200), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("did"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_blockchain_identities_guest_id"), "blockchain_identities", ["guest_id"], unique=True)

    # ── verifiable_credentials ──
    op.create_table("verifiable_credentials",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("identity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("credential_type", sa.String(length=50), nullable=False),
        sa.Column("credential_data", sa.JSON(), nullable=False),
        sa.Column("issuer_did", sa.String(length=200), nullable=False),
        sa.Column("subject_did", sa.String(length=200), nullable=False),
        sa.Column("issuance_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof_type", sa.String(length=30), nullable=False, server_default="Ed25519Signature2020"),
        sa.Column("proof_value", sa.Text(), nullable=False),
        sa.Column("chain_tx_hash", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["identity_id"], ["blockchain_identities.id"]),
    )
    op.create_index(op.f("ix_verifiable_credentials_identity_id"), "verifiable_credentials", ["identity_id"], unique=False)
    op.create_index(op.f("ix_verifiable_credentials_type"), "verifiable_credentials", ["credential_type"], unique=False)

    # ── identity_verification_proofs ──
    op.create_table("identity_verification_proofs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("identity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("verifier_id", sa.String(length=36), nullable=False),
        sa.Column("verification_type", sa.String(length=30), nullable=False),
        sa.Column("disclosed_fields", sa.JSON(), nullable=False),
        sa.Column("proof_data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["identity_id"], ["blockchain_identities.id"]),
    )
    op.create_index(op.f("ix_identity_verification_proofs_identity_id"), "identity_verification_proofs", ["identity_id"], unique=False)

    # ── blockchain_sync_events ──
    op.create_table("blockchain_sync_events",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("chain_tx_hash", sa.String(length=200), nullable=False),
        sa.Column("chain_id", sa.String(length=20), nullable=False, server_default="polygon-mumbai"),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="confirmed"),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blockchain_sync_events_type"), "blockchain_sync_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_blockchain_sync_events_status"), "blockchain_sync_events", ["status"], unique=False)

    # ── guest_consent_logs ──
    op.create_table("guest_consent_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("consent_type", sa.String(length=30), nullable=False),
        sa.Column("is_granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_version", sa.String(length=10), nullable=False, server_default="1.0"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_guest_consent_logs_guest_id"), "guest_consent_logs", ["guest_id"], unique=False)
    op.create_index(op.f("ix_guest_consent_logs_type"), "guest_consent_logs", ["consent_type"], unique=False)


def downgrade() -> None:
    op.drop_table("guest_consent_logs")
    op.drop_table("blockchain_sync_events")
    op.drop_table("identity_verification_proofs")
    op.drop_table("verifiable_credentials")
    op.drop_table("blockchain_identities")
