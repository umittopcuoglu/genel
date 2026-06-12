"""Add maintenance tables for TASK-015

Revision ID: 011
Revises: 010
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("assets",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("warranty_end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_status"), "assets", ["status"], unique=False)
    op.create_index(op.f("ix_assets_category"), "assets", ["category"], unique=False)

    op.create_table("work_orders",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=15), nullable=False, server_default="normal"),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("assigned_to", UUID(as_uuid=True), nullable=True),
        sa.Column("estimated_hours", sa.Integer(), nullable=True),
        sa.Column("actual_hours", sa.Integer(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
    )
    op.create_index(op.f("ix_work_orders_status"), "work_orders", ["status"], unique=False)
    op.create_index(op.f("ix_work_orders_priority"), "work_orders", ["priority"], unique=False)
    op.create_index(op.f("ix_work_orders_room_id"), "work_orders", ["room_id"], unique=False)
    op.create_index(op.f("ix_work_orders_assigned_to"), "work_orders", ["assigned_to"], unique=False)

    op.create_table("preventive_maintenance",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("frequency_days", sa.Integer(), nullable=False),
        sa.Column("last_maintenance_date", sa.Date(), nullable=True),
        sa.Column("next_maintenance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
    )
    op.create_index(op.f("ix_preventive_maintenance_asset_id"), "preventive_maintenance", ["asset_id"], unique=False)
    op.create_index(op.f("ix_preventive_maintenance_next_date"), "preventive_maintenance", ["next_maintenance_date"], unique=False)

    op.create_table("maintenance_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), nullable=True),
        sa.Column("performed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("parts_used", sa.String(length=200), nullable=True),
        sa.Column("hours_spent", sa.Numeric(5, 2), nullable=False),
        sa.Column("cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
    )
    op.create_index(op.f("ix_maintenance_logs_work_order_id"), "maintenance_logs", ["work_order_id"], unique=False)
    op.create_index(op.f("ix_maintenance_logs_asset_id"), "maintenance_logs", ["asset_id"], unique=False)
    op.create_index(op.f("ix_maintenance_logs_performed_by"), "maintenance_logs", ["performed_by"], unique=False)


def downgrade() -> None:
    op.drop_table("maintenance_logs")
    op.drop_table("preventive_maintenance")
    op.drop_table("work_orders")
    op.drop_table("assets")
