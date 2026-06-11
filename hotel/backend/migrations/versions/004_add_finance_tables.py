"""Add finance tables: folios, folio_items, payments, night_audit_runs

Revision ID: 004
Revises: 003
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("folios",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="open"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("closed_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_folios_reservation_id"), "folios", ["reservation_id"], unique=False)
    op.create_index(op.f("ix_folios_guest_id"), "folios", ["guest_id"], unique=False)
    op.create_index(op.f("ix_folios_status"), "folios", ["status"], unique=False)
    op.create_index(op.f("ix_folios_closed_date"), "folios", ["closed_date"], unique=False)

    op.create_table("folio_items",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("folio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="18"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["folio_id"], ["folios.id"]),
    )
    op.create_index(op.f("ix_folio_items_folio_id"), "folio_items", ["folio_id"], unique=False)
    op.create_index(op.f("ix_folio_items_type"), "folio_items", ["type"], unique=False)
    op.create_index("ix_folio_items_folio_type", "folio_items", ["folio_id", "type"], unique=False)

    op.create_table("payments",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("folio_id", UUID(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
        sa.Column("ref", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="completed"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["folio_id"], ["folios.id"]),
    )
    op.create_index(op.f("ix_payments_folio_id"), "payments", ["folio_id"], unique=False)
    op.create_index(op.f("ix_payments_method"), "payments", ["method"], unique=False)
    op.create_index("ix_payments_folio_method", "payments", ["folio_id", "method"], unique=False)

    op.create_table("night_audit_runs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("run_by", UUID(as_uuid=True), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stats", JSONB, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["run_by"], ["users.id"]),
        sa.UniqueConstraint("business_date", name="uq_night_audit_business_date"),
    )
    op.create_index(op.f("ix_night_audit_runs_business_date"), "night_audit_runs", ["business_date"], unique=True)


def downgrade() -> None:
    op.drop_table("night_audit_runs")
    op.drop_table("payments")
    op.drop_table("folio_items")
    op.drop_table("folios")
