"""Add Voice Control tables for TASK-022

Revision ID: 018
Revises: 017
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── voice_integrations ──
    op.create_table("voice_integrations",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="tr-TR"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
    )
    op.create_index(op.f("ix_voice_integrations_room_id"), "voice_integrations", ["room_id"], unique=False)
    op.create_index(op.f("ix_voice_integrations_provider"), "voice_integrations", ["provider"], unique=False)

    # ── voice_sessions ──
    op.create_table("voice_sessions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("integration_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("command_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["integration_id"], ["voice_integrations.id"]),
    )
    op.create_index(op.f("ix_voice_sessions_integration_id"), "voice_sessions", ["integration_id"], unique=False)
    op.create_index(op.f("ix_voice_sessions_session_id"), "voice_sessions", ["session_id"], unique=False)

    # ── voice_commands ──
    op.create_table("voice_commands",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("integration_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("intent", sa.String(length=50), nullable=False),
        sa.Column("raw_text", sa.String(length=500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("result", sa.String(length=50), nullable=True),
        sa.Column("response_text", sa.String(length=500), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("performed_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["integration_id"], ["voice_integrations.id"]),
    )
    op.create_index(op.f("ix_voice_commands_integration_id"), "voice_commands", ["integration_id"], unique=False)
    op.create_index(op.f("ix_voice_commands_intent"), "voice_commands", ["intent"], unique=False)

    # ── voice_interactions ──
    op.create_table("voice_interactions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("integration_id", UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("request_type", sa.String(length=30), nullable=False),
        sa.Column("raw_request", sa.JSON(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["integration_id"], ["voice_integrations.id"]),
    )
    op.create_index(op.f("ix_voice_interactions_integration_id"), "voice_interactions", ["integration_id"], unique=False)

    # ── voice_intents_mappings ──
    op.create_table("voice_intents_mappings",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("intent_name", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("action_params_template", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_voice_intents_mappings_provider"), "voice_intents_mappings", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_table("voice_intents_mappings")
    op.drop_table("voice_interactions")
    op.drop_table("voice_commands")
    op.drop_table("voice_sessions")
    op.drop_table("voice_integrations")
