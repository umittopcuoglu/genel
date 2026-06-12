"""Add IoT / Smart Room tables for TASK-020

Revision ID: 016
Revises: 015
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── iot_devices ──
    op.create_table("iot_devices",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("vendor", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="online"),
        sa.Column("state", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
    )
    op.create_index(op.f("ix_iot_devices_room_id"), "iot_devices", ["room_id"], unique=False)
    op.create_index(op.f("ix_iot_devices_device_type"), "iot_devices", ["device_type"], unique=False)
    op.create_index(op.f("ix_iot_devices_status"), "iot_devices", ["status"], unique=False)

    # ── iot_device_logs ──
    op.create_table("iot_device_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="device"),
        sa.Column("performed_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["device_id"], ["iot_devices.id"]),
    )
    op.create_index(op.f("ix_iot_device_logs_device_id"), "iot_device_logs", ["device_id"], unique=False)
    op.create_index(op.f("ix_iot_device_logs_event_type"), "iot_device_logs", ["event_type"], unique=False)

    # ── iot_scenarios ──
    op.create_table("iot_scenarios",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=30), nullable=False),
        sa.Column("trigger_config", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applies_to_room_types", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_iot_scenarios_trigger_type"), "iot_scenarios", ["trigger_type"], unique=False)
    op.create_index(op.f("ix_iot_scenarios_is_active"), "iot_scenarios", ["is_active"], unique=False)

    # ── iot_energy_readings ──
    op.create_table("iot_energy_readings",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", UUID(as_uuid=True), nullable=True),
        sa.Column("reading_type", sa.String(length=20), nullable=False, server_default="electricity"),
        sa.Column("value", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=False, server_default="kWh"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["iot_devices.id"]),
    )
    op.create_index(op.f("ix_iot_energy_readings_room_id"), "iot_energy_readings", ["room_id"], unique=False)
    op.create_index(op.f("ix_iot_energy_readings_type"), "iot_energy_readings", ["reading_type"], unique=False)

    # ── iot_alerts ──
    op.create_table("iot_alerts",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_id", UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False, server_default="info"),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["device_id"], ["iot_devices.id"]),
    )
    op.create_index(op.f("ix_iot_alerts_device_id"), "iot_alerts", ["device_id"], unique=False)
    op.create_index(op.f("ix_iot_alerts_severity"), "iot_alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_iot_alerts_resolved"), "iot_alerts", ["is_resolved"], unique=False)


def downgrade() -> None:
    op.drop_table("iot_alerts")
    op.drop_table("iot_energy_readings")
    op.drop_table("iot_scenarios")
    op.drop_table("iot_device_logs")
    op.drop_table("iot_devices")
