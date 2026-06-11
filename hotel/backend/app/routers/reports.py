from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.custom_report import CustomReport
from app.models.budget import Budget


router = APIRouter(prefix="/reports", tags=["Reports"])


class CustomReportCreateRequest(BaseModel):
    name: str
    description: str | None = None
    definition: dict


class CustomReportResponse(BaseModel):
    id: UUID
    name: str
    description: str | None


@router.post("/custom")
async def create_custom_report(
    req: CustomReportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomReportResponse:
    report = CustomReport(
        name=req.name,
        description=req.description,
        definition=req.definition,
        created_by=current_user.id,
    )
    db.add(report)
    await db.commit()

    return CustomReportResponse(
        id=report.id,
        name=report.name,
        description=report.description,
    )


@router.get("/custom")
async def list_custom_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CustomReportResponse]:
    result = await db.execute(select(CustomReport).limit(50))
    reports = result.scalars().all()
    return [
        CustomReportResponse(
            id=r.id,
            name=r.name,
            description=r.description,
        )
        for r in reports
    ]


@router.post("/custom/{report_id}/execute")
async def execute_custom_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(CustomReport).where(CustomReport.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404)

    return {
        "report_name": report.name,
        "definition": report.definition,
        "data": [],
        "generated_at": "2026-06-11T15:00:00Z",
    }


@router.get("/budget/variance")
async def get_budget_variance(
    year: int,
    month: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(Budget).where(Budget.budget_year == year)
    if month:
        query = query.where(Budget.budget_month == month)

    result = await db.execute(query)
    budgets = result.scalars().all()

    variance_data = [
        {
            "department": b.department,
            "budgeted_revenue": float(b.budgeted_revenue),
            "actual_revenue": float(b.actual_revenue) if b.actual_revenue else None,
            "variance_percent": b.variance_percent,
        }
        for b in budgets
    ]

    return {
        "year": year,
        "month": month,
        "data": variance_data,
    }
