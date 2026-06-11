---
id: TASK-018
modül: HR & Vardiya (Cross-module)
kapsam: çalışan yönetimi + vardiya tanımı + atama + puantaj + izin talepleri + izin bakiyesi + ShiftAI
durum: kuyrukta (TASK-001, TASK-007 KABUL olunca gönderilir)
tur: —
bağımlılık: TASK-001 (users, auth), TASK-007 (BaseAgent, registry, PII mask)
---

# TASK-018 — HR & Vardiya Modülü + ShiftAI

> Referans: docs/02_DEEPSEEK_TALIMATLARI.md §8. ShiftAI tahminleri — bu görevde sadece çekirdek akış.

## 1. Veri Modeli

### `employees`
- id (UUID, PK) [BaseModel]
- user_id (UUID FK → users.id, unique)
- department (VARCHAR 50) — housekeeping / food_beverage / maintenance / front_office / accounting / management
- position (VARCHAR 50) — manager / supervisor / staff / other
- hire_date (DATE)
- employment_status (VARCHAR 15, default="active") — active / inactive / suspended / terminated
- annual_leave_balance (DECIMAL 5,2, default=20) — yıllık izin gün sayısı
- sick_leave_balance (DECIMAL 5,2, default=10)
- other_leave_balance (DECIMAL 5,2, default=3)
- manager_id (UUID FK → employees.id, nullable raporlama chain)
- notes (TEXT nullable)
- Index: department, employment_status, hire_date

### `shifts`
- id (UUID, PK) [BaseModel]
- name (VARCHAR 50) — "Morning", "Evening", "Night", "Full Day"
- department (VARCHAR 50) — department bazlı vardiya tarifesi
- start_time (TIME) — HH:MM
- end_time (TIME)
- min_staff_required (INT) — minimum personel sayısı
- status (VARCHAR 15, default="active") — active / inactive
- notes (TEXT nullable)
- Index: department, status

### `shift_assignments`
- id (UUID, PK) [BaseModel]
- employee_id (UUID FK → employees.id)
- shift_id (UUID FK → shifts.id)
- assigned_date (DATE)
- status (VARCHAR 15, default="scheduled") — scheduled / confirmed / no_show / completed / cancelled
- notes (TEXT nullable)
- Index: employee_id, assigned_date, status

### `attendance`
- id (UUID, PK) [BaseModel]
- employee_id (UUID FK → employees.id)
- clock_in_time (TIMESTAMP)
- clock_out_time (TIMESTAMP nullable)
- shift_assignment_id (UUID FK → shift_assignments.id, nullable)
- is_late (BOOLEAN, default=false) — vardiya başlangıcından geç
- is_early_out (BOOLEAN, default=false)
- notes (TEXT nullable)
- Index: employee_id, clock_in_time

### `leave_requests`
- id (UUID, PK) [BaseModel]
- employee_id (UUID FK → employees.id)
- leave_type (VARCHAR 30) — annual | sick | other
- start_date, end_date (DATE)
- duration_days (DECIMAL 5,2) — toplam gün (0.5 = yarım gün)
- reason (TEXT nullable)
- status (VARCHAR 15, default="pending") — pending / approved / rejected / cancelled
- reviewed_by (UUID FK → employees.id, manager, nullable)
- reviewed_at (TIMESTAMP nullable)
- notes (TEXT nullable)
- Index: employee_id, status, start_date

## 2. Endpoint'ler

### `POST /api/v1/hr/employees`
- Auth: superadmin, manager
- Body: { user_id, department, position, hire_date, annual_leave_balance?, manager_id? }
- 201 döner employee

### `GET /api/v1/hr/employees`
- Auth: superadmin, manager, hr
- Query: ?department=&employment_status=&manager_id=
- 200 döner { data: [{...}], meta: { total, by_department } }

### `GET /api/v1/hr/employees/{id}`
- Auth: superadmin, manager, hr, employee (self)
- 200 döner { id, user_id, department, leave_balances: { annual, sick, other }, manager_id, ... }

### `POST /api/v1/hr/shifts`
- Auth: superadmin, manager
- Body: { name, department, start_time, end_time, min_staff_required }
- 201 döner shift

### `GET /api/v1/hr/shifts`
- Auth: superadmin, manager, hr
- Query: ?department=&status=active
- 200 döner { data: [{...}], meta: {...} }

### `POST /api/v1/hr/shift-assignments`
- Auth: superadmin, manager, hr
- Body: { employee_id, shift_id, assigned_date }
- assigned_date'de aynı employee için başka shift assignment varsa 409 `SHIFT_OVERLAP`
- assigned_date'de pending leave_request varsa warning (proceed anyway, but flag)
- 201 döner shift_assignment (status=scheduled)

### `PATCH /api/v1/hr/shift-assignments/{id}/status`
- Auth: superadmin, manager, hr
- Body: { status }
- Geçişler: scheduled→confirmed→completed; no_show/cancelled her yerden
- 200 döner shift_assignment

### `POST /api/v1/hr/attendance/clock-in`
- Auth: employee (kendi), superadmin, manager
- Body: { employee_id? }
- employee parametresiz ise current_user; admin → employee_id set
- today's shift_assignment query; attendance entry create (clock_in_time=now)
- shift start_time vs. clock_in_time → is_late flag
- 201 döner attendance

### `PATCH /api/v1/hr/attendance/{id}/clock-out`
- Auth: employee (kendi), superadmin, manager
- Body: {}
- clock_out_time=now; is_early_out flag (shift end_time vs. clock_out)
- 200 döner attendance (duration = clock_out - clock_in)

### `GET /api/v1/hr/attendance`
- Auth: superadmin, manager, hr
- Query: ?employee_id=&from_date=&to_date=&is_late=true
- 200 döner { data: [{...}], meta: { late_count, early_out_count } }

### `POST /api/v1/hr/leave-requests`
- Auth: employee (talep), superadmin, manager (onaylama)
- Body: { employee_id?, leave_type, start_date, end_date, reason? }
- leave_type → leave_balance check; insufficient ise 422 `INSUFFICIENT_LEAVE_BALANCE`
- Date range overlap check (pending approval olan başka request varsa 409 `LEAVE_CONFLICT`)
- 201 döner leave_request (status=pending)

### `GET /api/v1/hr/leave-requests`
- Auth: employee (kendi), superadmin, manager, hr
- Query: ?employee_id=&status=&from_date=&to_date=
- employee parametresiz ise current user's requests
- 200 döner { data: [{...}], meta: { by_status: {...} } }

### `PATCH /api/v1/hr/leave-requests/{id}/approve`
- Auth: superadmin, manager (employee'nin manager'ı)
- Body: {}
- status=approved, reviewed_by=current_user, reviewed_at=now
- leave_type → employee.leave_*_balance düş (duration_days kadar)
- 200 döner leave_request

### `PATCH /api/v1/hr/leave-requests/{id}/reject`
- Auth: superadmin, manager
- Body: {}
- status=rejected, reviewed_by, reviewed_at
- leave balance unchanged
- 200 döner leave_request

### `GET /api/v1/hr/roster`
- Auth: superadmin, manager, hr
- Query: ?from_date=&to_date=&department=
- 200 döner { data: { [assigned_date]: [{ employee_id, shift_id, status }, ...] }, meta: {...} }

## 3. İş Mantığı

- **Çalışan oluştur**: user.role=employee | department_specific (e.g., "housekeeping"); employee record + leave balances init
- **Vardiya atama**: employee + shift + date; overlap kontrol (same date, aynı vardiya başlığı yok), pending leave check
- **Puantaj**: clock-in → attendance (is_late check), clock-out → duration, is_early_out flag
- **İzin talebi**: duration_days × leave_type → balance check; insufficient ise 422; date overlap ise 409
- **İzin onayı**: status=approved → balance düş; rejected ise balance unchanged
- **Vardiya müsaitliği**: shift.min_staff_required vs. confirmed assignments günlük kontrol
- **Raporlama**: employee.manager_id → leave onay yetkisi (direct manager); superadmin her yerde

## 4. ShiftAI Ajanı

### Model: `app/core/agents/shift_ai.py`
- Miras: BaseAgent
- agent_name: "shift_ai"
- model_provider: "deepseek" (fallback: "openai", "claude")

### `POST /api/v1/ai/shiftai/suggest-roster`
- Auth: superadmin, manager
- Body: { department, from_date, to_date, occupancy_forecast? }
- LLM prompt (PII masked): "TASK-009 occupancy forecast + workload → optimal shift staffing"
- Forecast yoksa default: occupancy 70%, workload = housekeeping 2:1, fb 1:1, front 1:2 ratio
- Mock: output: { roster: [{ date, suggested_shifts: [...], staffing_level: "adequate" | "understaffed" }, ...], confidence: 0.75 }
- LLM (gerçek): DeepSeek API (forecast + department + available employees → prompt)
- 200 döner { data: { roster: [...], confidence }, meta: {...} }

### `GET /api/v1/ai/shiftai/absence-risk`
- Auth: superadmin, manager
- Query: ?department=&days_ahead=7
- LLM prompt: "Historical attendance + pattern → absence risk scoring per employee"
- Mock: output: { risks: [{ employee_id, risk_score: 0.8, reason: "frequent late arrivals" }, ...] }
- 200 döner { data: { risks: [...] }, meta: {...} }

## 5. Testler (minimum 14)
- employee create → leave balances init
- shift create
- shift_assignment create → overlap 409, leave warning
- clock-in → attendance, is_late flag
- clock-out → is_early_out flag, duration calc
- leave_request create → insufficient balance 422
- leave_request pending + overlap → 409 LEAVE_CONFLICT
- leave_request approve → balance düş
- leave_request reject → balance unchanged
- roster view
- shiftai suggest-roster mock/LLM happy path
- shiftai absence-risk mock/LLM happy path
- RBAC: employee kendi clock-in/out ✓, başka employee 403; manager approve ✓; hr sorgu ✓
- LLM error handling (timeout, model unavailable)

## 6. Teslim dosyaları
```
### FILE: backend/app/models/hr.py
### FILE: backend/app/routers/hr.py
### FILE: backend/app/core/agents/shift_ai.py
### FILE: backend/app/services/hr_service.py
### FILE: backend/tests/test_modules/test_hr.py
### FILE: backend/migrations/versions/005_add_hr_tables.py
```

## 7. Kabul kriterleri
- Tüm testler + kontrat testleri yeşil; review.py PASS
- Leave balance management test edilmiş: insufficient 422, approved düşümü, rejected unchanged
- ShiftAI ajanı BaseAgent'ı miras alır, registry'ye kaydolı, mock modu test için
- Raporlama zinciri (manager_id) RBAC ile test edilmiş
- OpenAPI Türkçe; error kodları `SHIFT_OVERLAP`, `INSUFFICIENT_LEAVE_BALANCE`, `LEAVE_CONFLICT`
