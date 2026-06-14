"""Add HR & Shift tables for TASK-018 (Employee, Shift, ShiftAssignment, Attendance, LeaveRequest)

Revision ID: 014
Revises: 013
Create Date: 2026-06-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── employees ──
    op.create_table("employees",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_code", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("position", sa.String(length=50), nullable=False),
        sa.Column("salary", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("emergency_contact", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_employees_department"), "employees", ["department"], unique=False)
    op.create_index(op.f("ix_employees_is_active"), "employees", ["is_active"], unique=False)

    # ── shifts ──
    op.create_table("shifts",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("min_employees", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_employees", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shifts_department"), "shifts", ["department"], unique=False)
    op.create_index(op.f("ix_shifts_is_active"), "shifts", ["is_active"], unique=False)

    # ── shift_assignments ──
    op.create_table("shift_assignments",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("shift_id", UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="scheduled"),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"]),
    )
    op.create_index(op.f("ix_shift_assignments_employee_id"), "shift_assignments", ["employee_id"], unique=False)
    op.create_index(op.f("ix_shift_assignments_shift_id"), "shift_assignments", ["shift_id"], unique=False)
    op.create_index(op.f("ix_shift_assignments_date"), "shift_assignments", ["assignment_date"], unique=False)
    op.create_index(op.f("ix_shift_assignments_status"), "shift_assignments", ["status"], unique=False)

    # ── attendance ──
    op.create_table("attendance",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("clock_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clock_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("overtime_hours", sa.Numeric(5, 2), nullable=True, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="present"),
        sa.Column("notes", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
    )
    op.create_index(op.f("ix_attendance_employee_id"), "attendance", ["employee_id"], unique=False)
    op.create_index(op.f("ix_attendance_date"), "attendance", ["date"], unique=False)
    op.create_index(op.f("ix_attendance_status"), "attendance", ["status"], unique=False)

    # ── leave_requests ──
    op.create_table("leave_requests",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("leave_type", sa.String(length=30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("approved_by", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["employees.id"]),
    )
    op.create_index(op.f("ix_leave_requests_employee_id"), "leave_requests", ["employee_id"], unique=False)
    op.create_index(op.f("ix_leave_requests_status"), "leave_requests", ["status"], unique=False)
    op.create_index(op.f("ix_leave_requests_dates"), "leave_requests", ["start_date", "end_date"], unique=False)


def downgrade() -> None:
    op.drop_table("leave_requests")
    op.drop_table("attendance")
    op.drop_table("shift_assignments")
    op.drop_table("shifts")
    op.drop_table("employees")
