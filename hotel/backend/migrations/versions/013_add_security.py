"""Add Security & Access Control & KVKK tables for TASK-017

Revision ID: 013
Revises: 012
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── door_locks ──
    op.create_table("door_locks",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("area", sa.String(length=50), nullable=False),
        sa.Column("room_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
    )
    op.create_index(op.f("ix_door_locks_area"), "door_locks", ["area"], unique=False)
    op.create_index(op.f("ix_door_locks_room_id"), "door_locks", ["room_id"], unique=False)
    op.create_index(op.f("ix_door_locks_status"), "door_locks", ["status"], unique=False)

    # ── key_cards ──
    op.create_table("key_cards",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("card_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("owner_type", sa.String(length=15), nullable=False),
        sa.Column("owner_name", sa.String(length=100), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="active"),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
    )
    op.create_index(op.f("ix_key_cards_card_number"), "key_cards", ["card_number"], unique=False)
    op.create_index(op.f("ix_key_cards_status"), "key_cards", ["status"], unique=False)
    op.create_index(op.f("ix_key_cards_reservation_id"), "key_cards", ["reservation_id"], unique=False)

    # ── access_logs ──
    op.create_table("access_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("door_lock_id", UUID(as_uuid=True), nullable=True),
        sa.Column("area", sa.String(length=50), nullable=False),
        sa.Column("card_number", sa.String(length=50), nullable=True),
        sa.Column("person_name", sa.String(length=100), nullable=True),
        sa.Column("result", sa.String(length=15), nullable=False),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["door_lock_id"], ["door_locks.id"]),
    )
    op.create_index(op.f("ix_access_logs_door_lock_id"), "access_logs", ["door_lock_id"], unique=False)
    op.create_index(op.f("ix_access_logs_area"), "access_logs", ["area"], unique=False)
    op.create_index(op.f("ix_access_logs_result"), "access_logs", ["result"], unique=False)

    # ── incidents ──
    op.create_table("incidents",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("incident_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=15), nullable=False, server_default="low"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="open"),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incidents_incident_type"), "incidents", ["incident_type"], unique=False)
    op.create_index(op.f("ix_incidents_severity"), "incidents", ["severity"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)

    # ── kvkk_consents ──
    op.create_table("kvkk_consents",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=True),
        sa.Column("guest_name", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="granted"),
        sa.Column("consent_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_kvkk_consents_guest_id"), "kvkk_consents", ["guest_id"], unique=False)
    op.create_index(op.f("ix_kvkk_consents_status"), "kvkk_consents", ["status"], unique=False)

    # ── data_access_requests ──
    op.create_table("data_access_requests",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=True),
        sa.Column("guest_name", sa.String(length=100), nullable=False),
        sa.Column("request_type", sa.String(length=15), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_data_access_requests_guest_id"), "data_access_requests", ["guest_id"], unique=False)
    op.create_index(op.f("ix_data_access_requests_request_type"), "data_access_requests", ["request_type"], unique=False)
    op.create_index(op.f("ix_data_access_requests_status"), "data_access_requests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("data_access_requests")
    op.drop_table("kvkk_consents")
    op.drop_table("incidents")
    op.drop_table("access_logs")
    op.drop_table("key_cards")
    op.drop_table("door_locks")
