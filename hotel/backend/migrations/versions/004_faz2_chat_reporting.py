"""Create Faz 2 chat and reporting tables.

Revision ID: 004
Revises: 003
Create Date: 2026-06-11 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chat_session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(50), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["chat_session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "custom_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("budget_year", sa.Integer(), nullable=False),
        sa.Column("budget_month", sa.Integer(), nullable=False),
        sa.Column("budgeted_revenue", sa.Numeric(15, 2), nullable=False),
        sa.Column("budgeted_expense", sa.Numeric(15, 2), nullable=False),
        sa.Column("actual_revenue", sa.Numeric(15, 2), nullable=True),
        sa.Column("actual_expense", sa.Numeric(15, 2), nullable=True),
        sa.Column("variance_percent", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rate_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_type_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("recommended_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("current_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_change_percent", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("historical_avg_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("occupancy_forecast", sa.Float(), nullable=False),
        sa.Column("demand_trend", sa.String(50), nullable=False),
        sa.Column("competitor_avg_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="suggested"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "occupancy_forecasts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_type_id", sa.Uuid(), nullable=True),
        sa.Column("forecast_date", sa.String(10), nullable=False),
        sa.Column("predicted_occupancy_percent", sa.Float(), nullable=False),
        sa.Column("predicted_rooms_occupied", sa.Integer(), nullable=False),
        sa.Column("confidence_interval", sa.String(100), nullable=False),
        sa.Column("forecast_method", sa.String(100), nullable=False),
        sa.Column("forecast_horizon_days", sa.Integer(), nullable=False),
        sa.Column("actual_occupancy_percent", sa.Float(), nullable=True),
        sa.Column("forecast_error_percent", sa.Float(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("occupancy_forecasts")
    op.drop_table("rate_recommendations")
    op.drop_table("budgets")
    op.drop_table("custom_reports")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
