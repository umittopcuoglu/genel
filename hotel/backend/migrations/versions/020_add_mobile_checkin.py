"""Add Mobile Check-in tables for TASK-024

Revision ID: 020
Revises: 019
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ocr_document_scans ──
    op.create_table("ocr_document_scans",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("scan_type", sa.String(length=20), nullable=False),
        sa.Column("document_number", sa.String(length=50), nullable=False),
        sa.Column("issuing_country", sa.String(length=50), nullable=True),
        sa.Column("nationality", sa.String(length=50), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        sa.Column("document_expiry", sa.Date(), nullable=True),
        sa.Column("mrz_text", sa.Text(), nullable=True),
        sa.Column("scan_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("raw_ocr_result", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_by", sa.String(length=36), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_ocr_document_scans_guest_id"), "ocr_document_scans", ["guest_id"], unique=False)

    # ── checkin_sessions ──
    op.create_table("checkin_sessions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reservation_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_token", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="started"),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_checkin_sessions_reservation_id"), "checkin_sessions", ["reservation_id"], unique=False)
    op.create_index(op.f("ix_checkin_sessions_status"), "checkin_sessions", ["status"], unique=False)

    # ── facial_recognition_scans ──
    op.create_table("facial_recognition_scans",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("scan_type", sa.String(length=20), nullable=False, server_default="selfie"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("is_match", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("raw_result", sa.JSON(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["checkin_sessions.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_facial_recognition_scans_session_id"), "facial_recognition_scans", ["session_id"], unique=False)

    # ── egm_submissions ──
    op.create_table("egm_submissions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stay_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("property_id", sa.String(length=36), nullable=True),
        sa.Column("submission_type", sa.String(length=20), nullable=False, server_default="checkin"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("xml_payload", sa.Text(), nullable=True),
        sa.Column("response_code", sa.String(length=10), nullable=True),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.Column("reference_number", sa.String(length=50), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_request", sa.JSON(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stay_id"], ["stays.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_egm_submissions_stay_id"), "egm_submissions", ["stay_id"], unique=False)
    op.create_index(op.f("ix_egm_submissions_status"), "egm_submissions", ["status"], unique=False)

    # ── nfc_room_keys ──
    op.create_table("nfc_room_keys",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stay_id", UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("guest_id", UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.ForeignKeyConstraint(["stay_id"], ["stays.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
    )
    op.create_index(op.f("ix_nfc_room_keys_stay_id"), "nfc_room_keys", ["stay_id"], unique=False)
    op.create_index(op.f("ix_nfc_room_keys_status"), "nfc_room_keys", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("nfc_room_keys")
    op.drop_table("egm_submissions")
    op.drop_table("facial_recognition_scans")
    op.drop_table("checkin_sessions")
    op.drop_table("ocr_document_scans")
