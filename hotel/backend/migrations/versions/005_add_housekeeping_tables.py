"""Add housekeeping tables: housekeeping_tasks, lost_found, minibar_items

Revision ID: 005
Revises: 004
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # housekeeping_tasks
    op.create_table("housekeeping_tasks",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_to", UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=15), nullable=False, server_default="stayover"),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
    )
    op.create_index(op.f("ix_housekeeping_tasks_room_id"), "housekeeping_tasks", ["room_id"], unique=False)
    op.create_index(op.f("ix_housekeeping_tasks_status"), "housekeeping_tasks", ["status"], unique=False)
    op.create_index("ix_housekeeping_room_status", "housekeeping_tasks", ["room_id", "status"], unique=False)
    op.create_index("ix_housekeeping_assigned", "housekeeping_tasks", ["assigned_to", "status"], unique=False)

    # lost_found
    op.create_table("lost_found",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), nullable=False),
        sa.Column("found_by", UUID(as_uuid=True), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="stored"),
        sa.Column("returned_to", sa.String(length=100), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["found_by"], ["users.id"]),
    )
    op.create_index(op.f("ix_lost_found_room_id"), "lost_found", ["room_id"], unique=False)
    op.create_index(op.f("ix_lost_found_status"), "lost_found", ["status"], unique=False)
    op.create_index("ix_lost_found_room_status", "lost_found", ["room_id", "status"], unique=False)

    # minibar_items
    op.create_table("minibar_items",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="18"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("minibar_items")
    op.drop_table("lost_found")
    op.drop_table("housekeeping_tasks")
