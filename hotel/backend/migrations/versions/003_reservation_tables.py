"""Add rate_plans and availability tables for reservation module

Revision ID: 003
Revises: 002
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # rate_plans
    op.create_table("rate_plans",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("room_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("base_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("restrictions", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
    )
    op.create_index(op.f("ix_rate_plans_code"), "rate_plans", ["code"], unique=True)
    op.create_index(op.f("ix_rate_plans_room_type_id"), "rate_plans", ["room_type_id"], unique=False)

    # availability
    op.create_table("availability",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("available_count", sa.Integer(), nullable=False),
        sa.Column("sold_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.UniqueConstraint("room_type_id", "date", name="uq_avail_roomtype_date"),
    )
    op.create_index("ix_availability_roomtype_date", "availability", ["room_type_id", "date"], unique=False)

    # Reservations tablosuna yeni kolonlar (TASK-003)
    op.add_column("reservations", sa.Column("rate_plan_id", UUID(as_uuid=True), nullable=True))
    op.add_column("reservations", sa.Column("total_amount", sa.Numeric(12, 2), server_default="0", nullable=False))
    op.add_column("reservations", sa.Column("balance", sa.Numeric(12, 2), server_default="0", nullable=False))
    op.create_foreign_key("fk_reservations_rate_plan", "reservations", "rate_plans", ["rate_plan_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_reservations_rate_plan", "reservations", type_="foreignkey")
    op.drop_column("reservations", "balance")
    op.drop_column("reservations", "total_amount")
    op.drop_column("reservations", "rate_plan_id")
    op.drop_table("availability")
    op.drop_table("rate_plans")
