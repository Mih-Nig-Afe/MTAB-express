import asyncio
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models import Parcel
from app.services.pdf import render_waybill_html, generate_pdf_bytes
from app.services.storage import upload_file

async def _generate_waybill_pdf_async(parcel_id: str):
    async with AsyncSessionLocal() as db:
        # Load parcel with related branches
        stmt = select(Parcel).options(
            selectinload(Parcel.origin_branch),
            selectinload(Parcel.destination_branch)
        ).where(Parcel.id == parcel_id)
        
        result = await db.execute(stmt)
        parcel = result.scalar_one_or_none()
        
        if not parcel:
            print(f"Parcel {parcel_id} not found.")
            return

        # Prepare parcel data for rendering
        parcel_data = {
            "tracking_code": parcel.tracking_code,
            "sender_name": "Sender Name Placeholder", # We don't load sender in this basic model but could
            "receiver_name": parcel.receiver_name,
            "origin_branch": parcel.origin_branch.name if parcel.origin_branch else "Unknown",
            "destination_branch": parcel.destination_branch.name if parcel.destination_branch else "Unknown",
            "weight_kg": parcel.weight_kg,
            "description": parcel.description
        }
        
        # Render HTML and generate PDF bytes
        html = render_waybill_html(parcel_data)
        pdf_bytes = generate_pdf_bytes(html)
        
        # Upload to S3/R2
        filename = f"waybills/{parcel.tracking_code}.pdf"
        url = await upload_file(filename, pdf_bytes, content_type="application/pdf")
        
        # Update DB
        parcel.waybill_url = url
        await db.commit()

@shared_task
def generate_waybill_pdf(parcel_id: str):
    """Generates a PDF waybill and uploads to storage."""
    asyncio.run(_generate_waybill_pdf_async(parcel_id))
