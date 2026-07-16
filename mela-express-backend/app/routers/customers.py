from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Customer, Parcel
from app.schemas import CustomerLink, CustomerOut, ParcelOut

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.post("/link", response_model=CustomerOut)
async def link_customer(request: CustomerLink, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.phone == request.phone))
    customer = result.scalar_one_or_none()
    
    if customer:
        if request.telegram_id:
            customer.telegram_id = request.telegram_id
        if request.name:
            customer.name = request.name
    else:
        customer = Customer(
            phone=request.phone,
            name=request.name or "Unknown",
            telegram_id=request.telegram_id
        )
        db.add(customer)
        
    await db.commit()
    await db.refresh(customer)
    return customer

@router.get("/me/parcels", response_model=List[ParcelOut])
async def get_my_parcels(phone: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.phone == phone))
    customer = result.scalar_one_or_none()
    
    if not customer:
        return []
        
    query = select(Parcel).options(
        selectinload(Parcel.sender),
        selectinload(Parcel.receiver),
        selectinload(Parcel.origin_branch),
        selectinload(Parcel.destination_branch)
    ).where(
        (Parcel.sender_id == customer.id) | (Parcel.receiver_id == customer.id)
    ).order_by(Parcel.created_at.desc())
    
    parcels_result = await db.execute(query)
    return parcels_result.scalars().all()
