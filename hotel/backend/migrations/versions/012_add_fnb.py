"""Add F&B / POS tables for TASK-016

Revision ID: 012
Revises: 011
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── pos_outlets ──
    op.create_table("pos_outlets",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("outlet_type", sa.String(length=30), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pos_outlets_outlet_type"), "pos_outlets", ["outlet_type"], unique=False)
    op.create_index(op.f("ix_pos_outlets_status"), "pos_outlets", ["status"], unique=False)

    # ── menu_items ──
    op.create_table("menu_items",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outlet_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="10"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["outlet_id"], ["pos_outlets.id"]),
    )
    op.create_index(op.f("ix_menu_items_outlet_id"), "menu_items", ["outlet_id"], unique=False)
    op.create_index(op.f("ix_menu_items_category"), "menu_items", ["category"], unique=False)

    # ── pos_checks ──
    op.create_table("pos_checks",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outlet_id", UUID(as_uuid=True), nullable=False),
        sa.Column("table_no", sa.String(length=20), nullable=True),
        sa.Column("room_no", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="open"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("folio_id", UUID(as_uuid=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["outlet_id"], ["pos_outlets.id"]),
        sa.ForeignKeyConstraint(["folio_id"], ["folios.id"]),
    )
    op.create_index(op.f("ix_pos_checks_outlet_id"), "pos_checks", ["outlet_id"], unique=False)
    op.create_index(op.f("ix_pos_checks_status"), "pos_checks", ["status"], unique=False)
    op.create_index(op.f("ix_pos_checks_folio_id"), "pos_checks", ["folio_id"], unique=False)

    # ── pos_check_items ──
    op.create_table("pos_check_items",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_id", UUID(as_uuid=True), nullable=False),
        sa.Column("menu_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["check_id"], ["pos_checks.id"]),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
    )
    op.create_index(op.f("ix_pos_check_items_check_id"), "pos_check_items", ["check_id"], unique=False)
    op.create_index(op.f("ix_pos_check_items_menu_item_id"), "pos_check_items", ["menu_item_id"], unique=False)

    # ── stock_items ──
    op.create_table("stock_items",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_items_name"), "stock_items", ["name"], unique=False)

    # ── stock_movements ──
    op.create_table("stock_movements",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stock_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stock_item_id"], ["stock_items.id"]),
    )
    op.create_index(op.f("ix_stock_movements_stock_item_id"), "stock_movements", ["stock_item_id"], unique=False)
    op.create_index(op.f("ix_stock_movements_movement_type"), "stock_movements", ["movement_type"], unique=False)


def downgrade() -> None:
    op.drop_table("stock_movements")
    op.drop_table("stock_items")
    op.drop_table("pos_check_items")
    op.drop_table("pos_checks")
    op.drop_table("menu_items")
    op.drop_table("pos_outlets")
