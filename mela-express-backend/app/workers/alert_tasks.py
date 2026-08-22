import asyncio
from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models import Parcel, ParcelStatus, Branch, StaffUser, StaffRole
from app.workers.notification_tasks import send_telegram_notification, send_sms_notification

async def _check_transit_delays_async():
    """Finds parcels in transit for more than 48 hours and alerts managers."""
    async with AsyncSessionLocal() as db:
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=48)
        
        stmt = select(Parcel).options(
            selectinload(Parcel.destination_branch)
        ).where(
            Parcel.status == ParcelStatus.IN_TRANSIT,
            Parcel.updated_at <= threshold_time
        )
        
        result = await db.execute(stmt)
        delayed_parcels = result.scalars().all()
        
        if not delayed_parcels:
            return

        admin_telegram_ids = ["ADMIN_GROUP_CHAT_ID"] # Placeholder
        
        for parcel in delayed_parcels:
            msg = f"ALERT: Parcel {parcel.tracking_code} has been IN_TRANSIT for over 48 hours."
            for chat_id in admin_telegram_ids:
                send_telegram_notification.delay(chat_id, msg)

async def _daily_manager_digest_async():
    """Generates daily KPIs for each branch and alerts branch managers."""
    async with AsyncSessionLocal() as db:
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        
        branches_stmt = select(Branch)
        branches_result = await db.execute(branches_stmt)
        branches = branches_result.scalars().all()
        
        for branch in branches:
            created_stmt = select(func.count(Parcel.id)).where(
                Parcel.origin_branch_id == branch.id,
                Parcel.created_at >= start_of_day
            )
            created_count = (await db.execute(created_stmt)).scalar()
            
            delivered_stmt = select(func.count(Parcel.id)).where(
                Parcel.destination_branch_id == branch.id,
                Parcel.status == ParcelStatus.DELIVERED,
                Parcel.updated_at >= start_of_day
            )
            delivered_count = (await db.execute(delivered_stmt)).scalar()
            
            msg = (
                f"Daily Digest for {branch.name}:\n"
                f"- Parcels Created: {created_count}\n"
                f"- Parcels Delivered: {delivered_count}\n"
            )
            
            manager_stmt = select(StaffUser).where(
                StaffUser.branch_id == branch.id,
                StaffUser.role == StaffRole.MANAGER
            )
            managers = (await db.execute(manager_stmt)).scalars().all()
            
            for manager in managers:
                send_sms_notification.delay(manager.phone, msg)

@shared_task
def check_transit_delays():
    """Celery task to check transit delays."""
    asyncio.run(_check_transit_delays_async())

@shared_task
def daily_manager_digest():
    """Celery task to send daily manager digest."""
    asyncio.run(_daily_manager_digest_async())
