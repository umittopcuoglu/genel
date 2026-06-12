"""
HR & Shift router: Employee, Shift, ShiftAssignment, Attendance, LeaveRequest endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.hr import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    ShiftCreate,
    ShiftResponse,
    ShiftUpdate,
    ShiftAssignmentCreate,
    ShiftAssignmentResponse,
    ShiftAssignmentUpdate,
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestReview,
)
from app.services.hr_service import HRService
from typing import List

router = APIRouter(prefix="/api/v1/hr", tags=["HR & Shift"])


# ──────────────────────────────────────────
# Employee Endpoints
# ──────────────────────────────────────────

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Yeni personel kaydı oluştur."""
    employee = await HRService.create_employee(db, employee_data, {"user_id": str(current_user.id)})
    return employee


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Personel detaylarını getir."""
    employee = await HRService.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı")
    return employee


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Personel bilgilerini güncelle."""
    employee = await HRService.update_employee(db, employee_id, employee_data, {"user_id": str(current_user.id)})
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı")
    return employee


@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(
    department: str = Query(None, description="Departman filtresi"),
    is_active: bool = Query(None, description="Aktiflik filtresi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Personelleri listele (departman/durum filtresiyle)."""
    employees = await HRService.list_employees(db, department=department, is_active=is_active)
    return employees


# ──────────────────────────────────────────
# Shift Endpoints
# ──────────────────────────────────────────

@router.post("/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift_data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Yeni vardiya tanımı oluştur."""
    shift = await HRService.create_shift(db, shift_data, {"user_id": str(current_user.id)})
    return shift


@router.get("/shifts/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Vardiya detayını getir."""
    shift = await HRService.get_shift(db, shift_id)
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vardiya bulunamadı")
    return shift


@router.patch("/shifts/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    shift_data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Vardiya tanımını güncelle."""
    shift = await HRService.update_shift(db, shift_id, shift_data, {"user_id": str(current_user.id)})
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vardiya bulunamadı")
    return shift


@router.get("/shifts", response_model=List[ShiftResponse])
async def list_shifts(
    department: str = Query(None, description="Departman filtresi"),
    is_active: bool = Query(None, description="Aktiflik filtresi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Vardiyaları listele."""
    shifts = await HRService.list_shifts(db, department=department, is_active=is_active)
    return shifts


# ──────────────────────────────────────────
# ShiftAssignment Endpoints
# ──────────────────────────────────────────

@router.post("/shift-assignments", response_model=ShiftAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shift_assignment(
    assignment_data: ShiftAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Personele vardiya ata."""
    try:
        assignment = await HRService.create_shift_assignment(
            db, assignment_data, {"user_id": str(current_user.id)}
        )
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel veya vardiya bulunamadı")
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/shift-assignments/{assignment_id}", response_model=ShiftAssignmentResponse)
async def update_shift_assignment(
    assignment_id: UUID,
    assignment_data: ShiftAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Vardiya atamasını güncelle (check-in/out, status)."""
    assignment = await HRService.update_shift_assignment(
        db, assignment_id, assignment_data, {"user_id": str(current_user.id)}
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vardiya ataması bulunamadı")
    return assignment


@router.get("/shift-assignments", response_model=List[ShiftAssignmentResponse])
async def list_shift_assignments(
    employee_id: UUID = Query(None, description="Personel filtresi"),
    shift_id: UUID = Query(None, description="Vardiya filtresi"),
    assignment_date: date = Query(None, description="Tarih filtresi (YYYY-MM-DD)"),
    department: str = Query(None, description="Departman filtresi"),
    status: str = Query(None, description="Durum filtresi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Vardiya atamalarını listele."""
    assignments = await HRService.list_shift_assignments(
        db,
        employee_id=employee_id,
        shift_id=shift_id,
        assignment_date=assignment_date,
        department=department,
        status=status,
    )
    return assignments


# ──────────────────────────────────────────
# Attendance Endpoints
# ──────────────────────────────────────────

@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Yoklama kaydı oluştur."""
    try:
        attendance = await HRService.create_attendance(
            db, attendance_data, {"user_id": str(current_user.id)}
        )
        if not attendance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı")
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/attendance/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Yoklama kaydını güncelle."""
    attendance = await HRService.update_attendance(
        db, attendance_id, attendance_data, {"user_id": str(current_user.id)}
    )
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yoklama kaydı bulunamadı")
    return attendance


@router.get("/attendance", response_model=List[AttendanceResponse])
async def list_attendance(
    employee_id: UUID = Query(None, description="Personel filtresi"),
    start_date: date = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date: date = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
    status: str = Query(None, description="Durum filtresi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """Yoklama kayıtlarını listele."""
    records = await HRService.list_attendance(
        db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    return records


# ──────────────────────────────────────────
# LeaveRequest Endpoints
# ──────────────────────────────────────────

@router.post("/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """İzin talebi oluştur."""
    try:
        leave = await HRService.create_leave_request(
            db, leave_data, {"user_id": str(current_user.id)}
        )
        if not leave:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personel bulunamadı")
        return leave
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/leave-requests/{leave_id}/review", response_model=LeaveRequestResponse)
async def review_leave_request(
    leave_id: UUID,
    review_data: LeaveRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """İzin talebini onayla/reddet."""
    try:
        leave = await HRService.review_leave_request(
            db, leave_id, review_data, {"user_id": str(current_user.id)}
        )
        if not leave:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İzin talebi bulunamadı")
        return leave
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/leave-requests", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    employee_id: UUID = Query(None, description="Personel filtresi"),
    status: str = Query(None, description="Durum filtresi (pending, approved, rejected, cancelled)"),
    leave_type: str = Query(None, description="İzin türü filtresi"),
    start_date: date = Query(None, description="Başlangıç tarihi"),
    end_date: date = Query(None, description="Bitiş tarihi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "hr"])),
):
    """İzin taleplerini listele."""
    leaves = await HRService.list_leave_requests(
        db,
        employee_id=employee_id,
        status=status,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
    )
    return leaves
