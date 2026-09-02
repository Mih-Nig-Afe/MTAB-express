import asyncio
import logging
from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Payment, PaymentStatus
from app.services.chapa import verify_transaction

logger = logging.getLogger(__name__)

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

        if not settings.chapa_secret_key:
            if payments:
                logger.info(
                    "Skipping %d pending webhook retries: Chapa not configured.",
                    len(payments),
                )
            return

        for payment in payments:
            # Plain values captured before any await/commit — ORM instances can
            # expire after session state changes and sync access then blows up.
            tx_ref = payment.chapa_tx_ref
            payment_id = payment.id
            try:
                # Call chapa verify API
                is_valid = await verify_transaction(tx_ref)

                if is_valid:
                    payment.status = PaymentStatus.PAID
                    payment.verified_at = datetime.now(timezone.utc)
                else:
                    payment.status = PaymentStatus.FAILED

                await db.commit()
            except Exception:
                # If there's an error verifying, log it and continue
                logger.exception("Error verifying transaction %s (payment %s)", tx_ref, payment_id)
                await db.rollback()

@shared_task
def retry_failed_webhook():
    """Periodic task to retry failed webhooks."""
    asyncio.run(_retry_failed_webhooks_async())
