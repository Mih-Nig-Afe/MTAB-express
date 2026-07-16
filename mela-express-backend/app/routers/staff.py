from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from app.database import get_db
from app.models import StaffUser, StaffRole
from app.schemas import StaffCreate, StaffUpdate, StaffOut
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.core.security import hash_password
from app.exceptions import NotFoundError, ForbiddenError

router = APIRouter(prefix="/api/staff", tags=["staff"])

@router.get("", response_model=List[StaffOut])
async def list_staff(
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(StaffUser).options(selectinload(StaffUser.branch))
    if current_user.role == StaffRole.MANAGER and current_user.branch_id:
        query = query.where(StaffUser.branch_id == current_user.branch_id)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{staff_id}", response_model=StaffOut)
async def get_staff(
    staff_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(StaffUser).options(selectinload(StaffUser.branch)).where(StaffUser.id == staff_id)
    result = await db.execute(query)
    staff = result.scalar_one_or_none()
    
    if not staff:
        raise NotFoundError("Staff not found")
        
    if current_user.role == StaffRole.MANAGER and current_user.branch_id != staff.branch_id:
        raise ForbiddenError("Access denied")
        
    return staff

@router.post("", response_model=StaffOut)
async def create_staff(
    staff_in: StaffCreate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    staff_data = staff_in.model_dump()
    password = staff_data.pop("password")
    staff = StaffUser(**staff_data, password_hash=hash_password(password))
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    
    query = select(StaffUser).where(StaffUser.id == staff.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.patch("/{staff_id}", response_model=StaffOut)
async def update_staff(
    staff_id: uuid.UUID,
    staff_in: StaffUpdate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise NotFoundError("Staff not found")
        
    if current_user.role == StaffRole.MANAGER and current_user.branch_id != staff.branch_id:
        raise ForbiddenError("Access denied")
        
    update_data = staff_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(staff, key, value)
        
    await db.commit()
    await db.refresh(staff)
    
    query = select(StaffUser).options(selectinload(StaffUser.branch)).where(StaffUser.id == staff.id)
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles(StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    staff = await db.get(StaffUser, staff_id)
    if not staff:
        raise NotFoundError("Staff not found")
        
    staff.is_active = False
    await db.commit()
    return {"message": "Staff deactivated successfully"}
