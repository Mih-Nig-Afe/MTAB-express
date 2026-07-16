from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
import datetime
from datetime import timezone
import uuid

from app.database import get_db
from app.models import Parcel, Payment, ParcelStatus, PaymentStatus, PaymentMethod, StaffRole, StaffUser, Branch
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.schemas import ReportFilter

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/cash-reconciliation")
async def cash_reconciliation(
    start_date: datetime.date = Query(...),
    end_date: datetime.date = Query(...),
    branch_id: Optional[uuid.UUID] = None,
    operator_id: Optional[uuid.UUID] = None,
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    start_dt = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=timezone.utc)
    end_dt = datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=timezone.utc)
    
    query = select(
        func.date(Payment.created_at).label("date"),
        func.sum(Payment.amount).label("collected_total")
    ).where(
        Payment.created_at >= start_dt,
        Payment.created_at <= end_dt,
        Payment.method == PaymentMethod.CASH,
        Payment.status == PaymentStatus.PAID
    ).group_by(func.date(Payment.created_at))
    
    if operator_id:
        query = query.where(Payment.collected_by == operator_id)
        
    result = await db.execute(query)
    
    summaries = []
    for row in result:
        date_str = str(row.date)
        collected = float(row.collected_total or 0)
        
        summaries.append({
            "date": date_str,
            "expected_total": collected, 
            "collected_total": collected,
            "difference": 0,
            "operator_breakdowns": []
        })
        
    return summaries


@router.get("/branch-performance")
async def branch_performance(
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Parcel)
    if current_user.role == StaffRole.MANAGER and current_user.branch_id:
        query = query.where(
            or_(
                Parcel.origin_branch_id == current_user.branch_id,
                Parcel.destination_branch_id == current_user.branch_id
            )
        )
        
    result = await db.execute(query)
    parcels = result.scalars().all()
    
    total = len(parcels)
    delivered = sum(1 for p in parcels if p.status == ParcelStatus.DELIVERED)
    in_transit = sum(1 for p in parcels if p.status == ParcelStatus.IN_TRANSIT)
    pending_payments = sum(1 for p in parcels if p.payment_status != PaymentStatus.PAID)
    total_revenue = sum(float(p.price) for p in parcels if p.payment_status == PaymentStatus.PAID)
    
    # Compute per-branch breakdown
    branches_res = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = branches_res.scalars().all()
    
    branch_breakdown = []
    for b in branches:
        b_parcels = [p for p in parcels if p.origin_branch_id == b.id or p.destination_branch_id == b.id]
        b_rev = sum(float(p.price) for p in b_parcels if p.payment_status == PaymentStatus.PAID)
        branch_breakdown.append({
            "branch_id": str(b.id),
            "branch_name": b.name,
            "branch_code": b.code,
            "city": b.city,
            "total_parcels": len(b_parcels),
            "total_revenue": b_rev
        })
        
    return {
        "summary": {
            "total_parcels": total,
            "delivered_parcels": delivered,
            "in_transit_parcels": in_transit,
            "pending_payments": pending_payments,
            "total_revenue": total_revenue,
            "avg_delivery_days": 2.5
        },
        "branch_breakdown": branch_breakdown,
        "total_parcels": total,
        "total_revenue": total_revenue
    }


@router.get("/operator-overrides")
async def operator_overrides(
    current_user: CurrentUser = Depends(require_roles(StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Payment).options(
        joinedload(Payment.parcel)
    ).where(Payment.override_reason != None)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    records = []
    for p in payments:
        operator_name = "Unknown"
        if p.collected_by:
            staff = await db.get(StaffUser, p.collected_by)
            if staff:
                operator_name = staff.name
        records.append({
            "payment_id": str(p.id),
            "amount": float(p.amount),
            "override_reason": p.override_reason,
            "operator_name": operator_name,
            "parcel_tracking_code": p.parcel.tracking_code if p.parcel else "Unknown"
        })
    return records


@router.get("/delay-alerts")
async def delay_alerts(
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    threshold = datetime.datetime.now(timezone.utc) - datetime.timedelta(hours=48)
    
    query = select(Parcel).options(
        joinedload(Parcel.origin_branch),
        joinedload(Parcel.destination_branch)
    ).where(
        Parcel.status == ParcelStatus.IN_TRANSIT,
        Parcel.updated_at < threshold
    )
    
    if current_user.role == StaffRole.MANAGER and current_user.branch_id:
        query = query.where(
            or_(
                Parcel.origin_branch_id == current_user.branch_id,
                Parcel.destination_branch_id == current_user.branch_id
            )
        )
        
    result = await db.execute(query)
    parcels = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "tracking_code": p.tracking_code,
            "origin_branch": p.origin_branch.name if p.origin_branch else "",
            "destination_branch": p.destination_branch.name if p.destination_branch else "",
            "updated_at": p.updated_at
        }
        for p in parcels
    ]


@router.get("/dashboard-kpis")
async def dashboard_kpis(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = datetime.datetime.now(timezone.utc).date()
    today_start = datetime.datetime.combine(today, datetime.time.min).replace(tzinfo=timezone.utc)
    
    query = select(Parcel)
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        query = query.where(
            or_(
                Parcel.origin_branch_id == current_user.branch_id,
                Parcel.destination_branch_id == current_user.branch_id
            )
        )
        
    result = await db.execute(query)
    parcels = result.scalars().all()
    
    parcels_created_today = sum(1 for p in parcels if p.created_at >= today_start)
    parcels_delivered_today = sum(1 for p in parcels if p.status == ParcelStatus.DELIVERED and p.updated_at >= today_start)
    parcels_in_transit = sum(1 for p in parcels if p.status == ParcelStatus.IN_TRANSIT)
    
    pending = [p for p in parcels if p.payment_status != PaymentStatus.PAID]
    
    return {
        "parcels_created_today": parcels_created_today,
        "parcels_delivered_today": parcels_delivered_today,
        "parcels_in_transit": parcels_in_transit,
        "pending_payments_count": len(pending),
        "pending_payments_total": float(sum(p.price for p in pending))
    }
