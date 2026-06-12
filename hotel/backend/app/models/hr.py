"""
HR & Shift modelleri: Employee, Shift, ShiftAssignment, Attendance, LeaveRequest.
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, Time, ForeignKey, JSON, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Employee(BaseModel):
    """Personel/çalışan kaydı."""
    __tablename__ = "employees"

    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    department: Mapped[str] = mapped_column(String(50), nullable=False)  # frontdesk, housekeeping, kitchen, maintenance, management, security, hr
    position: Mapped[str] = mapped_column(String(50), nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"name": "...", "phone": "...", "relationship": "..."}
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Employee {self.employee_code}: {self.first_name} {self.last_name}>"


class Shift(BaseModel):
    """Vardiya tanımı (şablon)."""
    __tablename__ = "shifts"

    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Morning", "Evening", "Night"
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    min_employees: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_employees: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<Shift {self.name} ({self.department}): {self.start_time}-{self.end_time}>"


class ShiftAssignment(BaseModel):
    """Personelin belirli bir tarihteki vardiya ataması."""
    __tablename__ = "shift_assignments"

    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    shift_id: Mapped[str] = mapped_column(ForeignKey("shifts.id"), nullable=False)
    assignment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)  # scheduled, confirmed, completed, cancelled, no_show
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<ShiftAssignment emp={self.employee_id} shift={self.shift_id} date={self.assignment_date}>"


class Attendance(BaseModel):
    """Personel yoklama/puantaj kaydı."""
    __tablename__ = "attendance"

    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    clock_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    overtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, default=0)
    status: Mapped[str] = mapped_column(String(20), default="present", nullable=False)  # present, absent, late, half_day, excused
    notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<Attendance emp={self.employee_id} date={self.date} status={self.status}>"


class LeaveRequest(BaseModel):
    """İzin/izin talebi."""
    __tablename__ = "leave_requests"

    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)  # annual, sick, personal, maternity, paternity, unpaid
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(ForeignKey("employees.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, approved, rejected, cancelled
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<LeaveRequest emp={self.employee_id} type={self.leave_type} {self.start_date}-{self.end_date}>"
