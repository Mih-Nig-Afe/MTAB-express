import asyncio
from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Payment, PaymentStatus
from app.services.chapa import verify_transaction

async def _retry_failed_webhooks_async():
    """Async task body to find and retry failed webhooks."""
    async with AsyncSessionLocal() as db:
        # Find payments pending for more than 15 mins with a chapa tx ref
        threshold_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        stmt = select(Payment).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.chapa_tx_ref.isnot(None),
            Payment.created_at <= threshold_time
        )
        
        result = await db.execute(stmt)
        payments = result.scalars().all()
        
        for payment in payments:
            try:
                # Call chapa verify API
                is_valid = await verify_transaction(payment.chapa_tx_ref)
                
                if is_valid:
                    payment.status = PaymentStatus.PAID
                    payment.verified_at = datetime.now(timezone.utc)
                else:
                    payment.status = PaymentStatus.FAILED
                    
                await db.commit()
            except Exception as e:
                # If there's an error verifying, log it and continue
                print(f"Error verifying transaction {payment.chapa_tx_ref}: {e}")
                await db.rollback()

@shared_task
def retry_failed_webhook():
    """Periodic task to retry failed webhooks."""
    asyncio.run(_retry_failed_webhooks_async())
