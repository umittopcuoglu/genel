"""Add Computer Vision tables for TASK-021

Revision ID: 017
Revises: 016
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── cv_models ──
    op.create_table("cv_models",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("model_type", sa.String(length=30), nullable=False),
        sa.Column("framework", sa.String(length=30), nullable=False),
        sa.Column("accuracy", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("model_path", sa.String(length=500), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cv_models_type"), "cv_models", ["model_type"], unique=False)
    op.create_index(op.f("ix_cv_models_is_active"), "cv_models", ["is_active"], unique=False)

    # ── room_inspections ──
    op.create_table("room_inspections",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inspector_id", sa.String(length=36), nullable=True),
        sa.Column("cv_model_id", UUID(as_uuid=True), nullable=True),
        sa.Column("inspection_type", sa.String(length=30), nullable=False, server_default="daily"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("defects_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_result", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["cv_model_id"], ["cv_models.id"]),
    )
    op.create_index(op.f("ix_room_inspections_room_id"), "room_inspections", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_inspections_status"), "room_inspections", ["status"], unique=False)
    op.create_index(op.f("ix_room_inspections_type"), "room_inspections", ["inspection_type"], unique=False)

    # ── inspection_defects ──
    op.create_table("inspection_defects",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspection_id", UUID(as_uuid=True), nullable=False),
        sa.Column("defect_type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False, server_default="minor"),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("position", sa.JSON(), nullable=True),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("suggested_action", sa.String(length=200), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_by", sa.String(length=36), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_order_id", UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["inspection_id"], ["room_inspections.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
    )
    op.create_index(op.f("ix_inspection_defects_inspection_id"), "inspection_defects", ["inspection_id"], unique=False)
    op.create_index(op.f("ix_inspection_defects_type"), "inspection_defects", ["defect_type"], unique=False)
    op.create_index(op.f("ix_inspection_defects_severity"), "inspection_defects", ["severity"], unique=False)

    # ── inventory_snapshots ──
    op.create_table("inventory_snapshots",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inspection_id", UUID(as_uuid=True), nullable=True),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("expected_count", sa.Integer(), nullable=False),
        sa.Column("detected_count", sa.Integer(), nullable=False),
        sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("snapshot_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["inspection_id"], ["room_inspections.id"]),
    )
    op.create_index(op.f("ix_inventory_snapshots_room_id"), "inventory_snapshots", ["room_id"], unique=False)
    op.create_index(op.f("ix_inventory_snapshots_item_type"), "inventory_snapshots", ["item_type"], unique=False)


def downgrade() -> None:
    op.drop_table("inventory_snapshots")
    op.drop_table("inspection_defects")
    op.drop_table("room_inspections")
    op.drop_table("cv_models")
