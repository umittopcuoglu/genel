"""Add groups and events tables for TASK-014 (MICE management)

Revision ID: 010
Revises: 009
Create Date: 2026-06-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("venues",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity_min", sa.Integer(), nullable=False),
        sa.Column("capacity_max", sa.Integer(), nullable=False),
        sa.Column("setup_types", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_venues_status"), "venues", ["status"], unique=False)

    op.create_table("groups",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("agency_id", UUID(as_uuid=True), nullable=True),
        sa.Column("contract_number", sa.String(length=50), unique=True, nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="inquiry"),
        sa.Column("block_start_date", sa.Date(), nullable=False),
        sa.Column("block_end_date", sa.Date(), nullable=False),
        sa.Column("pax_count", sa.Integer(), nullable=False),
        sa.Column("group_folio_id", UUID(as_uuid=True), nullable=True),
        sa.Column("discount_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["agency_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_folio_id"], ["folios.id"]),
    )
    op.create_index(op.f("ix_groups_status"), "groups", ["status"], unique=False)
    op.create_index(op.f("ix_groups_block_start_date"), "groups", ["block_start_date"], unique=False)
    op.create_index(op.f("ix_groups_agency_id"), "groups", ["agency_id"], unique=False)

    op.create_table("room_blocks",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("room_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("qty_required", sa.Integer(), nullable=False),
        sa.Column("qty_confirmed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pickup_date", sa.Date(), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="pending"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
    )
    op.create_index(op.f("ix_room_blocks_group_id"), "room_blocks", ["group_id"], unique=False)
    op.create_index(op.f("ix_room_blocks_status"), "room_blocks", ["status"], unique=False)

    op.create_table("events",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("venue_id", UUID(as_uuid=True), nullable=True),
        sa.Column("capacity_required", sa.Integer(), nullable=False),
        sa.Column("setup_type", sa.String(length=30), nullable=False),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("catering_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
    )
    op.create_index(op.f("ix_events_group_id"), "events", ["group_id"], unique=False)
    op.create_index(op.f("ix_events_venue_id"), "events", ["venue_id"], unique=False)

    op.create_table("event_resources",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_id", UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("qty_required", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="requested"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
    )
    op.create_index(op.f("ix_event_resources_event_id"), "event_resources", ["event_id"], unique=False)

    op.create_table("group_rooming_list",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_name", sa.String(length=100), nullable=False),
        sa.Column("guest_email", sa.String(length=100), nullable=True),
        sa.Column("guest_phone", sa.String(length=20), nullable=True),
        sa.Column("room_type_requested", sa.String(length=30), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("checkout_date", sa.Date(), nullable=False),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="pending"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
    )
    op.create_index(op.f("ix_group_rooming_list_group_id"), "group_rooming_list", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_rooming_list_reservation_id"), "group_rooming_list", ["reservation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("group_rooming_list")
    op.drop_table("event_resources")
    op.drop_table("events")
    op.drop_table("room_blocks")
    op.drop_table("groups")
    op.drop_table("venues")
