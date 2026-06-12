"""
HR & Shift servisi: Employee, Shift, ShiftAssignment, Attendance, LeaveRequest iş mantığı.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.hr import Employee, Shift, ShiftAssignment, Attendance, LeaveRequest
from app.schemas.hr import (
    EmployeeCreate,
    EmployeeUpdate,
    ShiftCreate,
    ShiftUpdate,
    ShiftAssignmentCreate,
    ShiftAssignmentUpdate,
    AttendanceCreate,
    AttendanceUpdate,
    LeaveRequestCreate,
    LeaveRequestReview,
)


class HRService:
    """HR & Shift ile ilgili tüm iş mantığı."""

    # ──────────────────────────────────────────
    # Employee
    # ──────────────────────────────────────────

    @staticmethod
    async def create_employee(db: AsyncSession, data: EmployeeCreate, current_user: dict) -> Employee:
        """Yeni personel kaydı oluştur."""
        employee = Employee(
            employee_code=data.employee_code,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            department=data.department,
            position=data.position,
            salary=data.salary,
            hire_date=data.hire_date,
            emergency_contact=data.emergency_contact,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def get_employee(db: AsyncSession, employee_id: UUID) -> Optional[Employee]:
        """Personel detayını getir."""
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_employee(
        db: AsyncSession, employee_id: UUID, data: EmployeeUpdate, current_user: dict
    ) -> Optional[Employee]:
        """Personel bilgilerini güncelle."""
        employee = await HRService.get_employee(db, employee_id)
        if not employee:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        employee.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def list_employees(
        db: AsyncSession,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Employee]:
        """Personelleri listele (departman/durum filtresiyle)."""
        stmt = select(Employee)
        if department:
            stmt = stmt.where(Employee.department == department)
        if is_active is not None:
            stmt = stmt.where(Employee.is_active == is_active)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ──────────────────────────────────────────
    # Shift
    # ──────────────────────────────────────────

    @staticmethod
    async def create_shift(db: AsyncSession, data: ShiftCreate, current_user: dict) -> Shift:
        """Yeni vardiya tanımı oluştur."""
        shift = Shift(
            name=data.name,
            department=data.department,
            start_time=data.start_time,
            end_time=data.end_time,
            min_employees=data.min_employees,
            max_employees=data.max_employees,
            description=data.description,
            created_by=current_user.get("user_id"),
        )
        db.add(shift)
        await db.commit()
        await db.refresh(shift)
        return shift

    @staticmethod
    async def get_shift(db: AsyncSession, shift_id: UUID) -> Optional[Shift]:
        """Vardiya detayını getir."""
        stmt = select(Shift).where(Shift.id == shift_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_shift(
        db: AsyncSession, shift_id: UUID, data: ShiftUpdate, current_user: dict
    ) -> Optional[Shift]:
        """Vardiya tanımını güncelle."""
        shift = await HRService.get_shift(db, shift_id)
        if not shift:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(shift, field, value)
        shift.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(shift)
        return shift

    @staticmethod
    async def list_shifts(
        db: AsyncSession,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Shift]:
        """Vardiyaları listele."""
        stmt = select(Shift)
        if department:
            stmt = stmt.where(Shift.department == department)
        if is_active is not None:
            stmt = stmt.where(Shift.is_active == is_active)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ──────────────────────────────────────────
    # ShiftAssignment
    # ──────────────────────────────────────────

    @staticmethod
    async def create_shift_assignment(
        db: AsyncSession, data: ShiftAssignmentCreate, current_user: dict
    ) -> Optional[ShiftAssignment]:
        """Personele vardiya ata."""
        # Check employee exists
        employee = await HRService.get_employee(db, data.employee_id)
        if not employee:
            return None

        # Check shift exists
        shift = await HRService.get_shift(db, data.shift_id)
        if not shift:
            return None

        # Check for overlapping assignments on same date
        stmt = select(ShiftAssignment).where(
            and_(
                ShiftAssignment.employee_id == data.employee_id,
                ShiftAssignment.assignment_date == data.assignment_date,
                ShiftAssignment.status.in_(["scheduled", "confirmed"]),
            )
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise ValueError("Personelin bu tarihte zaten aktif bir vardiyası var.")

        assignment = ShiftAssignment(
            employee_id=data.employee_id,
            shift_id=data.shift_id,
            assignment_date=data.assignment_date,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def update_shift_assignment(
        db: AsyncSession, assignment_id: UUID, data: ShiftAssignmentUpdate, current_user: dict
    ) -> Optional[ShiftAssignment]:
        """Vardiya atamasını güncelle (status, check-in/out)."""
        stmt = select(ShiftAssignment).where(ShiftAssignment.id == assignment_id)
        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()
        if not assignment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)
        assignment.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def list_shift_assignments(
        db: AsyncSession,
        employee_id: Optional[UUID] = None,
        shift_id: Optional[UUID] = None,
        assignment_date: Optional[date] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[ShiftAssignment]:
        """Vardiya atamalarını listele (filtrelerle)."""
        stmt = select(ShiftAssignment)
        if employee_id:
            stmt = stmt.where(ShiftAssignment.employee_id == employee_id)
        if shift_id:
            stmt = stmt.where(ShiftAssignment.shift_id == shift_id)
        if assignment_date:
            stmt = stmt.where(ShiftAssignment.assignment_date == assignment_date)
        if status:
            stmt = stmt.where(ShiftAssignment.status == status)
        if department:
            # Join with shift to filter by department
            stmt = stmt.join(Shift, ShiftAssignment.shift_id == Shift.id).where(
                Shift.department == department
            )
        result = await db.execute(stmt)
        return result.scalars().all()

    # ──────────────────────────────────────────
    # Attendance
    # ──────────────────────────────────────────

    @staticmethod
    async def create_attendance(db: AsyncSession, data: AttendanceCreate, current_user: dict) -> Optional[Attendance]:
        """Yoklama kaydı oluştur."""
        employee = await HRService.get_employee(db, data.employee_id)
        if not employee:
            return None

        # Check for existing attendance on same date
        stmt = select(Attendance).where(
            and_(
                Attendance.employee_id == data.employee_id,
                Attendance.date == data.date,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise ValueError("Bu tarih için yoklama kaydı zaten mevcut.")

        attendance = Attendance(
            employee_id=data.employee_id,
            date=data.date,
            clock_in=data.clock_in,
            clock_out=data.clock_out,
            total_hours=data.total_hours,
            overtime_hours=data.overtime_hours,
            status=data.status,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def update_attendance(
        db: AsyncSession, attendance_id: UUID, data: AttendanceUpdate, current_user: dict
    ) -> Optional[Attendance]:
        """Yoklama kaydını güncelle."""
        stmt = select(Attendance).where(Attendance.id == attendance_id)
        result = await db.execute(stmt)
        attendance = result.scalar_one_or_none()
        if not attendance:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attendance, field, value)
        attendance.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def list_attendance(
        db: AsyncSession,
        employee_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> list[Attendance]:
        """Yoklama kayıtlarını listele."""
        stmt = select(Attendance)
        conditions = []
        if employee_id:
            conditions.append(Attendance.employee_id == employee_id)
        if start_date:
            conditions.append(Attendance.date >= start_date)
        if end_date:
            conditions.append(Attendance.date <= end_date)
        if status:
            conditions.append(Attendance.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    # ──────────────────────────────────────────
    # LeaveRequest
    # ──────────────────────────────────────────

    @staticmethod
    async def create_leave_request(
        db: AsyncSession, data: LeaveRequestCreate, current_user: dict
    ) -> Optional[LeaveRequest]:
        """İzin talebi oluştur."""
        employee = await HRService.get_employee(db, data.employee_id)
        if not employee:
            return None

        # Validate dates
        if data.end_date < data.start_date:
            raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

        # Calculate total days
        total_days = (data.end_date - data.start_date).days + 1

        # Check for overlapping leave requests
        stmt = select(LeaveRequest).where(
            and_(
                LeaveRequest.employee_id == data.employee_id,
                LeaveRequest.status.in_(["pending", "approved"]),
                LeaveRequest.start_date <= data.end_date,
                LeaveRequest.end_date >= data.start_date,
            )
        )
        result = await db.execute(stmt)
        overlapping = result.scalars().first()
        if overlapping:
            raise ValueError("Bu tarih aralığında zaten bir izin talebi bulunuyor.")

        leave = LeaveRequest(
            employee_id=data.employee_id,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            total_days=total_days,
            reason=data.reason,
            created_by=current_user.get("user_id"),
        )
        db.add(leave)
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def review_leave_request(
        db: AsyncSession, leave_id: UUID, data: LeaveRequestReview, current_user: dict
    ) -> Optional[LeaveRequest]:
        """İzin talebini onayla/reddet."""
        stmt = select(LeaveRequest).where(LeaveRequest.id == leave_id)
        result = await db.execute(stmt)
        leave = result.scalar_one_or_none()
        if not leave:
            return None

        if leave.status != "pending":
            raise ValueError("Sadece bekleyen izin talepleri değerlendirilebilir.")

        leave.status = data.status
        leave.reviewed_at = datetime.now()
        leave.review_notes = data.review_notes
        leave.approved_by = UUID(current_user.get("user_id"))
        leave.updated_by = current_user.get("user_id")

        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def list_leave_requests(
        db: AsyncSession,
        employee_id: Optional[UUID] = None,
        status: Optional[str] = None,
        leave_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[LeaveRequest]:
        """İzin taleplerini listele."""
        stmt = select(LeaveRequest)
        conditions = []
        if employee_id:
            conditions.append(LeaveRequest.employee_id == employee_id)
        if status:
            conditions.append(LeaveRequest.status == status)
        if leave_type:
            conditions.append(LeaveRequest.leave_type == leave_type)
        if start_date:
            conditions.append(LeaveRequest.start_date >= start_date)
        if end_date:
            conditions.append(LeaveRequest.end_date <= end_date)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()
