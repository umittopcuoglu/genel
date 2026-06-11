"""Create Faz 2 accounting and CRM tables.

Revision ID: 003
Revises: 002
Create Date: 2026-06-11 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chart_of_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False, unique=True),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("is_main_account", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("normal_balance", sa.String(10), nullable=False),
        sa.Column("balance_sheet_order", sa.Integer(), nullable=False),
        sa.Column("income_statement_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("journal_name", sa.String(100), nullable=False),
        sa.Column("entry_date", sa.String(10), nullable=False),
        sa.Column("entry_number", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("debit_account_id", sa.Uuid(), nullable=False),
        sa.Column("debit_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("credit_account_id", sa.Uuid(), nullable=False),
        sa.Column("credit_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("posted_by", sa.Uuid(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["credit_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["debit_account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["posted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "einvoices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("invoice_date", sa.String(10), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_tax_id", sa.String(20), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("kdv_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("e_invoice_uuid", sa.String(36), nullable=True),
        sa.Column("einvoice_status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("xml_content", sa.Text(), nullable=True),
        sa.Column("xml_url", sa.String(500), nullable=True),
        sa.Column("pdf_url", sa.String(500), nullable=True),
        sa.Column("pdf_content", sa.LargeBinary(), nullable=True),
        sa.Column("gib_response_code", sa.String(50), nullable=True),
        sa.Column("gib_error_message", sa.Text(), nullable=True),
        sa.Column("source_folio_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_folio_id"], ["folios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "loyalty_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False, server_default="bronze"),
        sa.Column("tier_since", sa.String(10), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_stays", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_revenue", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("suspension_reason", sa.String(255), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "loyalty_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("loyalty_account_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["loyalty_account_id"], ["loyalty_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "complaints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("reservation_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("complaint_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.Uuid(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("reservation_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("categories", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="new"),
        sa.Column("manager_response", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("complaints")
    op.drop_table("loyalty_transactions")
    op.drop_table("loyalty_accounts")
    op.drop_table("einvoices")
    op.drop_table("ledger_entries")
    op.drop_table("chart_of_accounts")
