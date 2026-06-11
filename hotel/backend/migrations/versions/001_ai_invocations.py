"""Create AI invocations table.

Revision ID: 001
Revises:
Create Date: 2026-06-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_invocations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("llm_response", sa.Text(), nullable=True),
        sa.Column("model_provider", sa.String(50), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_invocations")
