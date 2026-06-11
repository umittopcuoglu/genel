"""Front Office tablolari: room_types, rooms, guests, reservations, stays, traces

Revision ID: 002
Revises: 001
Create Date: 2026-06-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # room_types
    op.create_table("room_types",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_guests", sa.SmallInteger(), nullable=False),
        sa.Column("default_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("amenities", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_types_code"), "room_types", ["code"], unique=True)

    # rooms
    op.create_table("rooms",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_number", sa.String(length=10), nullable=False),
        sa.Column("floor", sa.SmallInteger(), nullable=False),
        sa.Column("room_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("clean", "dirty", "inspected", "occupied", "out_of_order", "reserved", name="room_status_enum"), nullable=False),
        sa.Column("is_smoking", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.UniqueConstraint("room_number", name="uq_room_number"),
    )
    op.create_index(op.f("ix_rooms_room_number"), "rooms", ["room_number"], unique=False)
    op.create_index(op.f("ix_rooms_room_type_id"), "rooms", ["room_type_id"], unique=False)
    op.create_index(op.f("ix_rooms_status"), "rooms", ["status"], unique=False)
    op.create_index("ix_rooms_floor_status", "rooms", ["floor", "status"], unique=False)

    # guests
    op.create_table("guests",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("nationality", sa.String(length=3), nullable=True),
        sa.Column("id_document_type", sa.String(length=30), nullable=True),
        sa.Column("id_document_number", sa.String(length=50), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=3), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_blacklisted", sa.Boolean(), nullable=False),
        sa.Column("is_vip", sa.Boolean(), nullable=False),
        sa.Column("total_stays", sa.Integer(), nullable=False),
        sa.Column("total_spent", sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_guests_email"), "guests", ["email"], unique=False)
    op.create_index("ix_guests_name", "guests", ["first_name", "last_name"], unique=False)
    op.create_index("ix_guests_phone", "guests", ["phone"], unique=False)

    # reservations
    op.create_table("reservations",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reservation_number", sa.String(length=20), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("confirmed", "checked_in", "checked_out", "cancelled", "no_show", name="reservation_status_enum"), nullable=False),
        sa.Column("source", sa.Enum("direct", "walk_in", "ota", "channel", "corporate", name="reservation_source_enum"), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("adults", sa.SmallInteger(), nullable=False),
        sa.Column("children", sa.SmallInteger(), nullable=False),
        sa.Column("room_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_room_id", UUID(as_uuid=True), nullable=True),
        sa.Column("requested_room_number", sa.String(length=10), nullable=True),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_paid", sa.Boolean(), nullable=False),
        sa.Column("channel_ref", sa.String(length=100), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("no_show_marked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.ForeignKeyConstraint(["assigned_room_id"], ["rooms.id"]),
    )
    op.create_index(op.f("ix_reservations_reservation_number"), "reservations", ["reservation_number"], unique=True)
    op.create_index(op.f("ix_reservations_guest_id"), "reservations", ["guest_id"], unique=False)
    op.create_index(op.f("ix_reservations_status"), "reservations", ["status"], unique=False)
    op.create_index(op.f("ix_reservations_check_in"), "reservations", ["check_in"], unique=False)
    op.create_index("ix_reservations_dates", "reservations", ["check_in", "check_out"], unique=False)
    op.create_index("ix_reservations_status_date", "reservations", ["status", "check_in"], unique=False)

    # stays
    op.create_table("stays",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actual_check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pax_count", sa.SmallInteger(), nullable=False),
        sa.Column("folio_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_checked_in", sa.Boolean(), nullable=False),
        sa.Column("is_checked_out", sa.Boolean(), nullable=False),
        sa.Column("is_house_use", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_stays_reservation_id"), "stays", ["reservation_id"], unique=False)
    op.create_index(op.f("ix_stays_room_id"), "stays", ["room_id"], unique=False)
    op.create_index(op.f("ix_stays_guest_id"), "stays", ["guest_id"], unique=False)
    op.create_index("ix_stays_active", "stays", ["is_checked_in", "is_checked_out"], unique=False)

    # traces
    op.create_table("traces",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("stay_id", UUID(as_uuid=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=True),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Enum("low", "normal", "high", "urgent", name="trace_priority_enum"), nullable=False),
        sa.Column("status", sa.Enum("open", "in_progress", "resolved", "cancelled", name="trace_status_enum"), nullable=False),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["stay_id"], ["stays.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
    )
    op.create_index(op.f("ix_traces_reservation_id"), "traces", ["reservation_id"], unique=False)
    op.create_index(op.f("ix_traces_stay_id"), "traces", ["stay_id"], unique=False)
    op.create_index(op.f("ix_traces_guest_id"), "traces", ["guest_id"], unique=False)
    op.create_index(op.f("ix_traces_room_id"), "traces", ["room_id"], unique=False)
    op.create_index(op.f("ix_traces_department"), "traces", ["department"], unique=False)
    op.create_index(op.f("ix_traces_status"), "traces", ["status"], unique=False)
    op.create_index("ix_traces_department_status", "traces", ["department", "status"], unique=False)
    op.create_index("ix_traces_due_date", "traces", ["due_date"], unique=False)


def downgrade() -> None:
    op.drop_table("traces")
    op.drop_table("stays")
    op.drop_table("reservations")
    op.drop_table("guests")
    op.drop_table("rooms")

    # Enum'ları temizle (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS room_status_enum")
    op.execute("DROP TYPE IF EXISTS reservation_status_enum")
    op.execute("DROP TYPE IF EXISTS reservation_source_enum")
    op.execute("DROP TYPE IF EXISTS trace_priority_enum")
    op.execute("DROP TYPE IF EXISTS trace_status_enum")

    op.drop_table("room_types")
