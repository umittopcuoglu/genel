from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ──────────────────────────────────────────
# Employee Schemas
# ──────────────────────────────────────────

class EmployeeResponse(BaseModel):
    id: UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: str
    position: str
    salary: Decimal
    hire_date: date
    termination_date: Optional[date] = None
    is_active: bool
    emergency_contact: Optional[dict] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreate(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: str = Field(..., max_length=50)
    position: str = Field(..., max_length=50)
    salary: Decimal = Field(..., ge=0)
    hire_date: date
    emergency_contact: Optional[dict] = None
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    phone: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[Decimal] = None
    emergency_contact: Optional[dict] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# ──────────────────────────────────────────
# Shift Schemas
# ──────────────────────────────────────────

class ShiftResponse(BaseModel):
    id: UUID
    name: str
    department: str
    start_time: time
    end_time: time
    min_employees: int
    max_employees: int
    is_active: bool
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    department: str = Field(..., max_length=50)
    start_time: time
    end_time: time
    min_employees: int = Field(1, ge=1)
    max_employees: int = Field(5, ge=1)
    description: Optional[str] = Field(None, max_length=200)


class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


# ──────────────────────────────────────────
# ShiftAssignment Schemas
# ──────────────────────────────────────────

class ShiftAssignmentResponse(BaseModel):
    id: UUID
    employee_id: UUID
    shift_id: UUID
    assignment_date: date
    status: str
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftAssignmentCreate(BaseModel):
    employee_id: UUID
    shift_id: UUID
    assignment_date: date
    notes: Optional[str] = None


class ShiftAssignmentUpdate(BaseModel):
    status: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────
# Attendance Schemas
# ──────────────────────────────────────────

class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    total_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    total_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    status: str = "present"
    notes: Optional[str] = None


class AttendanceUpdate(BaseModel):
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    total_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────
# LeaveRequest Schemas
# ──────────────────────────────────────────

class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    total_days: int
    reason: Optional[str] = None
    approved_by: Optional[UUID] = None
    status: str
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestCreate(BaseModel):
    employee_id: UUID
    leave_type: str = Field(..., max_length=30)
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestReview(BaseModel):
    status: str  # approved, rejected
    review_notes: Optional[str] = None
