"""Add GDS Integration tables for TASK-019

Revision ID: 015
Revises: 014
Create Date: 2026-06-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── gds_channels ──
    op.create_table("gds_channels",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("supported_actions", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_gds_channels_provider"), "gds_channels", ["provider"], unique=False)
    op.create_index(op.f("ix_gds_channels_is_active"), "gds_channels", ["is_active"], unique=False)

    # ── gds_reservations ──
    op.create_table("gds_reservations",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gds_reservation_id", sa.String(length=100), nullable=False),
        sa.Column("hotel_reservation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("guest_name", sa.String(length=100), nullable=False),
        sa.Column("guest_email", sa.String(length=100), nullable=True),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("adults", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("children", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("room_type_code", sa.String(length=20), nullable=False),
        sa.Column("rate_plan_code", sa.String(length=20), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("sync_message", sa.String(length=500), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["gds_channels.id"]),
        sa.ForeignKeyConstraint(["hotel_reservation_id"], ["reservations.id"]),
    )
    op.create_index(op.f("ix_gds_reservations_channel_id"), "gds_reservations", ["channel_id"], unique=False)
    op.create_index(op.f("ix_gds_reservations_status"), "gds_reservations", ["status"], unique=False)
    op.create_index(op.f("ix_gds_reservations_dates"), "gds_reservations", ["check_in", "check_out"], unique=False)

    # ── gds_rate_mappings ──
    op.create_table("gds_rate_mappings",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gds_room_type_code", sa.String(length=30), nullable=False),
        sa.Column("gds_rate_plan_code", sa.String(length=30), nullable=False),
        sa.Column("hotel_room_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("hotel_rate_plan_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("markup_percentage", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["gds_channels.id"]),
        sa.ForeignKeyConstraint(["hotel_room_type_id"], ["room_types.id"]),
        sa.ForeignKeyConstraint(["hotel_rate_plan_id"], ["rate_plans.id"]),
    )
    op.create_index(op.f("ix_gds_rate_mappings_channel_id"), "gds_rate_mappings", ["channel_id"], unique=False)

    # ── gds_sync_logs ──
    op.create_table("gds_sync_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("request_data", sa.JSON(), nullable=True),
        sa.Column("response_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("performed_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["gds_channels.id"]),
    )
    op.create_index(op.f("ix_gds_sync_logs_channel_id"), "gds_sync_logs", ["channel_id"], unique=False)
    op.create_index(op.f("ix_gds_sync_logs_action"), "gds_sync_logs", ["action"], unique=False)
    op.create_index(op.f("ix_gds_sync_logs_status"), "gds_sync_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("gds_sync_logs")
    op.drop_table("gds_rate_mappings")
    op.drop_table("gds_reservations")
    op.drop_table("gds_channels")
