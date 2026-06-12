"""Add Multi-Property / Chain tables for TASK-023

Revision ID: 019
Revises: 018
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── chains ──
    op.create_table("chains",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("website", sa.String(length=200), nullable=True),
        sa.Column("contact_email", sa.String(length=100), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # ── properties ──
    op.create_table("properties",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chain_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("property_type", sa.String(length=30), nullable=False, server_default="hotel"),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=50), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
        sa.Column("timezone", sa.String(length=30), nullable=False, server_default="Europe/Istanbul"),
        sa.Column("star_rating", sa.Integer(), nullable=True),
        sa.Column("total_rooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.ForeignKeyConstraint(["chain_id"], ["chains.id"]),
    )
    op.create_index(op.f("ix_properties_chain_id"), "properties", ["chain_id"], unique=False)
    op.create_index(op.f("ix_properties_city"), "properties", ["city"], unique=False)

    # ── property_users ──
    op.create_table("property_users",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("property_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
    )
    op.create_index(op.f("ix_property_users_property_id"), "property_users", ["property_id"], unique=False)
    op.create_index(op.f("ix_property_users_user_id"), "property_users", ["user_id"], unique=False)

    # ── property_sync_logs ──
    op.create_table("property_sync_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("property_id", UUID(as_uuid=True), nullable=False),
        sa.Column("sync_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("data_type", sa.String(length=50), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
    )
    op.create_index(op.f("ix_property_sync_logs_property_id"), "property_sync_logs", ["property_id"], unique=False)
    op.create_index(op.f("ix_property_sync_logs_type"), "property_sync_logs", ["sync_type"], unique=False)

    # ── consolidated_reports ──
    op.create_table("consolidated_reports",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chain_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_revenue", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_occupancy", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("total_rooms_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_available_rooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_daily_rate", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("revpar", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["chain_id"], ["chains.id"]),
    )
    op.create_index(op.f("ix_consolidated_reports_chain_id"), "consolidated_reports", ["chain_id"], unique=False)
    op.create_index(op.f("ix_consolidated_reports_type"), "consolidated_reports", ["report_type"], unique=False)


def downgrade() -> None:
    op.drop_table("consolidated_reports")
    op.drop_table("property_sync_logs")
    op.drop_table("property_users")
    op.drop_table("properties")
    op.drop_table("chains")
