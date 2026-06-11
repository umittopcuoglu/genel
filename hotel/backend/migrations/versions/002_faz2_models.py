"""Create Faz 2 models tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-11 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("channel_type", sa.String(50), nullable=False),
        sa.Column("credentials_encrypted", sa.String(1000), nullable=False),
        sa.Column("api_base_url", sa.String(500), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sync_interval_hours", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(), nullable=True),
        sa.Column("rate_limit_requests", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("rate_limit_window_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "channel_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("external_room_id", sa.String(255), nullable=False),
        sa.Column("mapping_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("auto_match_confidence", sa.Float(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "overbooking_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_type_id", sa.Uuid(), nullable=True),
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        sa.Column("overbooking_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "channel_sync_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("reservations_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rooms_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("channel_sync_logs")
    op.drop_table("overbooking_rules")
    op.drop_table("channel_mappings")
    op.drop_table("channels")
