"""TASK-018 HR & Shift tests."""
import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from httpx import AsyncClient


@pytest.fixture
async def hr_employee_fixture(async_client, manager_headers):
    """Test personeli oluştur."""
    response = await async_client.post(
        "/api/v1/hr/employees",
        json={
            "employee_code": "EMP001",
            "first_name": "Ahmet",
            "last_name": "Yılmaz",
            "email": "ahmet@hotel.com",
            "phone": "+905551234567",
            "department": "frontdesk",
            "position": "Resepsiyonist",
            "salary": 25000.00,
            "hire_date": "2025-01-15",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def hr_shift_fixture(async_client, manager_headers):
    """Test vardiyası oluştur."""
    response = await async_client.post(
        "/api/v1/hr/shifts",
        json={
            "name": "Morning",
            "department": "frontdesk",
            "start_time": "07:00:00",
            "end_time": "15:00:00",
            "min_employees": 2,
            "max_employees": 4,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Employee Tests ──

@pytest.mark.asyncio
async def test_create_employee(client: AsyncClient, manager_headers: dict):
    """Yeni personel oluşturma."""
    response = await client.post(
        "/api/v1/hr/employees",
        json={
            "employee_code": "EMP002",
            "first_name": "Ayşe",
            "last_name": "Demir",
            "email": "ayse@hotel.com",
            "department": "housekeeping",
            "position": "Kat Görevlisi",
            "salary": 18000.00,
            "hire_date": "2025-03-01",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employee_code"] == "EMP002"
    assert data["department"] == "housekeeping"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_employee(client: AsyncClient, manager_headers: dict, hr_employee_fixture):
    """Personel detayını getir."""
    emp_id = hr_employee_fixture["id"]
    response = await client.get(
        f"/api/v1/hr/employees/{emp_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == emp_id
    assert data["first_name"] == "Ahmet"


@pytest.mark.asyncio
async def test_update_employee(client: AsyncClient, manager_headers: dict, hr_employee_fixture):
    """Personel bilgilerini güncelle."""
    emp_id = hr_employee_fixture["id"]
    response = await client.patch(
        f"/api/v1/hr/employees/{emp_id}",
        json={
            "position": "Kıdemli Resepsiyonist",
            "salary": 30000.00,
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["position"] == "Kıdemli Resepsiyonist"
    assert data["salary"] == "30000.00"


@pytest.mark.asyncio
async def test_list_employees(client: AsyncClient, manager_headers: dict, hr_employee_fixture):
    """Personelleri listele."""
    response = await client.get(
        "/api/v1/hr/employees",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_list_employees_by_department(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """Personelleri departmana göre filtrele."""
    response = await client.get(
        "/api/v1/hr/employees?department=frontdesk",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert all(emp["department"] == "frontdesk" for emp in data)


# ── Shift Tests ──

@pytest.mark.asyncio
async def test_create_shift(client: AsyncClient, manager_headers: dict):
    """Yeni vardiya oluşturma."""
    response = await client.post(
        "/api/v1/hr/shifts",
        json={
            "name": "Evening",
            "department": "frontdesk",
            "start_time": "15:00:00",
            "end_time": "23:00:00",
            "min_employees": 2,
            "max_employees": 3,
            "description": "Akşam vardiyası",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Evening"
    assert data["department"] == "frontdesk"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_shift(client: AsyncClient, manager_headers: dict, hr_shift_fixture):
    """Vardiya detayını getir."""
    shift_id = hr_shift_fixture["id"]
    response = await client.get(
        f"/api/v1/hr/shifts/{shift_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shift_id
    assert data["name"] == "Morning"


@pytest.mark.asyncio
async def test_update_shift(client: AsyncClient, manager_headers: dict, hr_shift_fixture):
    """Vardiya bilgilerini güncelle."""
    shift_id = hr_shift_fixture["id"]
    response = await client.patch(
        f"/api/v1/hr/shifts/{shift_id}",
        json={
            "max_employees": 5,
            "description": "Güncellenmiş sabah vardiyası",
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["max_employees"] == 5


@pytest.mark.asyncio
async def test_list_shifts(client: AsyncClient, manager_headers: dict, hr_shift_fixture):
    """Vardiyaları listele."""
    response = await client.get(
        "/api/v1/hr/shifts",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ── ShiftAssignment Tests ──

@pytest.mark.asyncio
async def test_create_shift_assignment(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture, hr_shift_fixture
):
    """Personele vardiya ata."""
    response = await client.post(
        "/api/v1/hr/shift-assignments",
        json={
            "employee_id": hr_employee_fixture["id"],
            "shift_id": hr_shift_fixture["id"],
            "assignment_date": "2026-07-01",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["assignment_date"] == "2026-07-01"


@pytest.mark.asyncio
async def test_create_duplicate_shift_assignment(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture, hr_shift_fixture
):
    """Aynı tarihte çift vardiya ataması engellenmeli."""
    # First assignment
    await client.post(
        "/api/v1/hr/shift-assignments",
        json={
            "employee_id": hr_employee_fixture["id"],
            "shift_id": hr_shift_fixture["id"],
            "assignment_date": "2026-07-01",
        },
        headers=manager_headers,
    )
    # Duplicate assignment
    response = await client.post(
        "/api/v1/hr/shift-assignments",
        json={
            "employee_id": hr_employee_fixture["id"],
            "shift_id": hr_shift_fixture["id"],
            "assignment_date": "2026-07-01",
        },
        headers=manager_headers,
    )
    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_update_shift_assignment_checkin(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture, hr_shift_fixture
):
    """Vardiya giriş/çıkış güncellemesi."""
    # Create assignment
    create_resp = await client.post(
        "/api/v1/hr/shift-assignments",
        json={
            "employee_id": hr_employee_fixture["id"],
            "shift_id": hr_shift_fixture["id"],
            "assignment_date": "2026-07-01",
        },
        headers=manager_headers,
    )
    assignment_id = create_resp.json()["id"]

    # Check-in
    response = await client.patch(
        f"/api/v1/hr/shift-assignments/{assignment_id}",
        json={
            "status": "confirmed",
            "checked_in_at": "2026-07-01T07:00:00+03:00",
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["checked_in_at"] is not None


# ── Attendance Tests ──

@pytest.mark.asyncio
async def test_create_attendance(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """Yoklama kaydı oluştur."""
    response = await client.post(
        "/api/v1/hr/attendance",
        json={
            "employee_id": hr_employee_fixture["id"],
            "date": "2026-07-01",
            "clock_in": "2026-07-01T07:05:00+03:00",
            "clock_out": "2026-07-01T15:10:00+03:00",
            "total_hours": 8.00,
            "overtime_hours": 0.08,
            "status": "present",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "present"
    assert data["date"] == "2026-07-01"


@pytest.mark.asyncio
async def test_update_attendance(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """Yoklama kaydını güncelle."""
    # Create
    create_resp = await client.post(
        "/api/v1/hr/attendance",
        json={
            "employee_id": hr_employee_fixture["id"],
            "date": "2026-07-02",
            "status": "present",
        },
        headers=manager_headers,
    )
    att_id = create_resp.json()["id"]

    # Update
    response = await client.patch(
        f"/api/v1/hr/attendance/{att_id}",
        json={
            "status": "late",
            "notes": "15 dakika geç geldi",
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "late"


# ── LeaveRequest Tests ──

@pytest.mark.asyncio
async def test_create_leave_request(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """İzin talebi oluştur."""
    response = await client.post(
        "/api/v1/hr/leave-requests",
        json={
            "employee_id": hr_employee_fixture["id"],
            "leave_type": "annual",
            "start_date": "2026-08-01",
            "end_date": "2026-08-07",
            "reason": "Yıllık izin",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["leave_type"] == "annual"
    assert data["total_days"] == 7
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_review_leave_request_approve(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """İzin talebini onayla."""
    # Create leave request
    create_resp = await client.post(
        "/api/v1/hr/leave-requests",
        json={
            "employee_id": hr_employee_fixture["id"],
            "leave_type": "annual",
            "start_date": "2026-08-10",
            "end_date": "2026-08-14",
            "reason": "Yıllık izin",
        },
        headers=manager_headers,
    )
    leave_id = create_resp.json()["id"]

    # Approve
    response = await client.post(
        f"/api/v1/hr/leave-requests/{leave_id}/review",
        json={
            "status": "approved",
            "review_notes": "İzin onaylandı",
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


@pytest.mark.asyncio
async def test_review_leave_request_reject(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """İzin talebini reddet."""
    # Create leave request
    create_resp = await client.post(
        "/api/v1/hr/leave-requests",
        json={
            "employee_id": hr_employee_fixture["id"],
            "leave_type": "personal",
            "start_date": "2026-08-20",
            "end_date": "2026-08-21",
            "reason": "Şahsi işler",
        },
        headers=manager_headers,
    )
    leave_id = create_resp.json()["id"]

    # Reject
    response = await client.post(
        f"/api/v1/hr/leave-requests/{leave_id}/review",
        json={
            "status": "rejected",
            "review_notes": "Dönem yoğunluğu nedeniyle reddedildi",
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_overlapping_leave_request(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """Çakışan izin talebi engellenmeli."""
    # First leave
    await client.post(
        "/api/v1/hr/leave-requests",
        json={
            "employee_id": hr_employee_fixture["id"],
            "leave_type": "annual",
            "start_date": "2026-09-01",
            "end_date": "2026-09-05",
            "reason": "Tatil",
        },
        headers=manager_headers,
    )
    # Overlapping leave
    response = await client.post(
        "/api/v1/hr/leave-requests",
        json={
            "employee_id": hr_employee_fixture["id"],
            "leave_type": "sick",
            "start_date": "2026-09-03",
            "end_date": "2026-09-04",
            "reason": "Hastalık",
        },
        headers=manager_headers,
    )
    assert response.status_code == 400  # Bad request due to overlap


@pytest.mark.asyncio
async def test_list_leave_requests(
    client: AsyncClient, manager_headers: dict, hr_employee_fixture
):
    """İzin taleplerini listele."""
    response = await client.get(
        "/api/v1/hr/leave-requests",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
