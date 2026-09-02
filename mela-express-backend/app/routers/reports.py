from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
import datetime
from datetime import timezone
import uuid

from app.database import get_db
from app.models import Parcel, Payment, ParcelStatus, PaymentStatus, PaymentMethod, StaffRole, StaffUser, Branch, ParcelFlightLeg, ParcelStatusHistory
from app.core.state_machine import LINEHAUL_STATUSES, is_linehaul_status
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
    total_collected = 0.0
    transaction_count = 0
    for row in result:
        date_str = str(row.date)
        collected = float(row.collected_total or 0)
        total_collected += collected
        
        summaries.append({
            "date": date_str,
            "expected_total": collected, 
            "collected_total": collected,
            "difference": 0,
            "operator_breakdowns": []
        })

    count_q = select(func.count(Payment.id)).where(
        Payment.created_at >= start_dt,
        Payment.created_at <= end_dt,
        Payment.method == PaymentMethod.CASH,
        Payment.status == PaymentStatus.PAID,
    )
    if operator_id:
        count_q = count_q.where(Payment.collected_by == operator_id)
    transaction_count = int(await db.scalar(count_q) or 0)
        
    return {
        "total_cash_collected": total_collected,
        "transaction_count": transaction_count,
        "daily_breakdown": summaries,
    }


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
    in_transit = sum(1 for p in parcels if is_linehaul_status(p.status))
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
        Parcel.status.in_(tuple(LINEHAUL_STATUSES)),
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
    start_date: Optional[datetime.date] = Query(None, description="Inclusive start (YYYY-MM-DD). Defaults to today."),
    end_date: Optional[datetime.date] = Query(None, description="Inclusive end (YYYY-MM-DD). Defaults to start_date."),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = datetime.datetime.now(timezone.utc).date()
    range_start = start_date or today
    range_end = end_date or range_start
    if range_end < range_start:
        range_end = range_start

    start_dt = datetime.datetime.combine(range_start, datetime.time.min).replace(tzinfo=timezone.utc)
    end_dt = datetime.datetime.combine(
        range_end + datetime.timedelta(days=1), datetime.time.min
    ).replace(tzinfo=timezone.utc)
    created_in_range = and_(Parcel.created_at >= start_dt, Parcel.created_at < end_dt)

    branch_filter = None
    if current_user.role in [StaffRole.OPERATOR, StaffRole.MANAGER] and current_user.branch_id:
        branch_filter = or_(
            Parcel.origin_branch_id == current_user.branch_id,
            Parcel.destination_branch_id == current_user.branch_id,
        )

    def _scoped(base, *, apply_date: bool = True):
        q = base
        if branch_filter is not None:
            q = q.where(branch_filter)
        if apply_date:
            q = q.where(created_in_range)
        return q

    status_rows = await db.execute(
        _scoped(select(Parcel.status, func.count(Parcel.id)).group_by(Parcel.status))
    )
    status_counts = {s.value: 0 for s in ParcelStatus}
    for status, count in status_rows.all():
        status_counts[status.value] = int(count)

    total_parcels = sum(status_counts.values())
    parcels_created_today = total_parcels

    delivered_q = _scoped(
        select(func.count(func.distinct(ParcelStatusHistory.parcel_id)))
        .select_from(ParcelStatusHistory)
        .join(Parcel, Parcel.id == ParcelStatusHistory.parcel_id)
        .where(
            ParcelStatusHistory.to_status == ParcelStatus.DELIVERED,
            ParcelStatusHistory.timestamp >= start_dt,
            ParcelStatusHistory.timestamp < end_dt,
        ),
        apply_date=False,
    )
    if branch_filter is not None:
        delivered_q = delivered_q.where(branch_filter)
    parcels_delivered_today = int(await db.scalar(delivered_q) or 0)

    pending_q = _scoped(
        select(func.count(Parcel.id), func.coalesce(func.sum(Parcel.price), 0)).where(
            Parcel.payment_status != PaymentStatus.PAID
        )
    )
    pending_row = (await db.execute(pending_q)).one()
    pending_count = int(pending_row[0] or 0)
    pending_total = float(pending_row[1] or 0)

    ready_for_pickup = status_counts.get(ParcelStatus.READY_FOR_PICKUP.value, 0)
    parcels_in_transit = sum(
        status_counts.get(s.value, 0) for s in ParcelStatus if is_linehaul_status(s)
    )

    delayed_q = _scoped(
        select(func.count(Parcel.id)).where(
            Parcel.current_eta_at.isnot(None),
            Parcel.promised_delivery_at.isnot(None),
            Parcel.current_eta_at > Parcel.promised_delivery_at,
            Parcel.status.notin_([
                ParcelStatus.DELIVERED,
                ParcelStatus.CANCELLED,
                ParcelStatus.RETURNED,
            ]),
        )
    )
    delayed_vs_eta = int(await db.scalar(delayed_q) or 0)

    return {
        "start_date": range_start.isoformat(),
        "end_date": range_end.isoformat(),
        "total_parcels": total_parcels,
        "status_counts": status_counts,
        "parcels_created_today": parcels_created_today,
        "parcels_delivered_today": parcels_delivered_today,
        "parcels_in_transit": parcels_in_transit,
        "pending_payments_count": pending_count,
        "pending_payments_total": pending_total,
        "ready_for_pickup": ready_for_pickup,
        "delayed_vs_promised": delayed_vs_eta,
    }


@router.get("/operations-kpis")
async def operations_kpis(
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Admin/manager operations board: funnel, OTD, dwell, pickup aging, flights."""
    now = datetime.datetime.now(timezone.utc)
    query = select(Parcel)
    if current_user.role == StaffRole.MANAGER and current_user.branch_id:
        query = query.where(
            or_(
                Parcel.origin_branch_id == current_user.branch_id,
                Parcel.destination_branch_id == current_user.branch_id
            )
        )
    parcels = (await db.execute(query)).scalars().all()

    funnel = {}
    for status in ParcelStatus:
        funnel[status.value] = sum(1 for p in parcels if p.status == status)

    delivered = [p for p in parcels if p.status == ParcelStatus.DELIVERED]
    on_time = [
        p for p in delivered
        if p.promised_delivery_at and p.updated_at and p.updated_at <= p.promised_delivery_at
    ]
    otd_pct = round(100.0 * len(on_time) / len(delivered), 1) if delivered else None

    exceptions = sum(
        1 for p in parcels
        if p.status in (ParcelStatus.ON_HOLD, ParcelStatus.LOST, ParcelStatus.RETURNED, ParcelStatus.CANCELLED)
    )
    exception_rate = round(100.0 * exceptions / len(parcels), 1) if parcels else 0

    ready = [p for p in parcels if p.status == ParcelStatus.READY_FOR_PICKUP]
    def _age_hours(p):
        start = p.pickup_ready_at or p.updated_at
        if not start:
            return 0
        return (now - start).total_seconds() / 3600

    aging = {
        "ready_now": len(ready),
        "over_24h": sum(1 for p in ready if _age_hours(p) >= 24),
        "over_72h": sum(1 for p in ready if _age_hours(p) >= 72),
        "over_7d": sum(1 for p in ready if _age_hours(p) >= 168),
        "avg_hours_waiting": round(sum(_age_hours(p) for p in ready) / len(ready), 1) if ready else 0,
        "reminders_sent": sum(int(p.pickup_reminders_sent or 0) for p in ready),
    }

    dwell = {}
    for status in ParcelStatus:
        cohort = [p for p in parcels if p.status == status and p.updated_at]
        if not cohort:
            continue
        hours = [max(0, (now - p.updated_at).total_seconds() / 3600) for p in cohort]
        dwell[status.value] = round(sum(hours) / len(hours), 1)

    promised_with_eta = [
        p for p in parcels
        if p.promised_delivery_at and p.current_eta_at
        and p.status not in (ParcelStatus.DELIVERED, ParcelStatus.CANCELLED, ParcelStatus.RETURNED)
    ]
    delayed = [p for p in promised_with_eta if p.current_eta_at > p.promised_delivery_at]

    legs = (await db.execute(select(ParcelFlightLeg))).scalars().all()
    active_flights = [lg for lg in legs if lg.status in ("scheduled", "active", "delayed")]
    delayed_flights = [lg for lg in legs if (lg.delay_minutes or 0) >= 15 or lg.status == "delayed"]

    return {
        "volume": {
            "total": len(parcels),
            "linehaul": sum(1 for p in parcels if is_linehaul_status(p.status)),
            "ready_for_pickup": len(ready),
            "delivered": len(delivered),
            "exceptions": exceptions,
        },
        "on_time_delivery_pct": otd_pct,
        "exception_rate_pct": exception_rate,
        "funnel": funnel,
        "dwell_hours": dwell,
        "pickup_aging": aging,
        "eta": {
            "late_vs_promised": len(delayed),
            "tracked_with_eta": len(promised_with_eta),
        },
        "flights": {
            "active": len(active_flights),
            "delayed": len(delayed_flights),
        },
        "generated_at": now.isoformat(),
    }
