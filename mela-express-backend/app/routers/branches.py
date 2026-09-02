from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.database import get_db
from app.models import Branch, StaffRole
from app.schemas import BranchCreate, BranchUpdate, BranchOut
from app.dependencies import get_current_user, require_roles, CurrentUser
from app.exceptions import NotFoundError

router = APIRouter(prefix="/api/branches", tags=["branches"])

@router.get("", response_model=List[BranchOut])
async def list_branches(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    return result.scalars().all()

@router.get("/public")
async def list_public_branches(db: AsyncSession = Depends(get_db)):
    """Unauthenticated basic branch info (name/city/phone) for customer-facing
    surfaces like the Telegram bot."""
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    return [
        {"name": b.name, "city": b.city, "phone": b.phone}
        for b in result.scalars().all()
    ]

@router.get("/{branch_id}", response_model=BranchOut)
async def get_branch(
    branch_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    branch = await db.get(Branch, branch_id)
    if not branch or not branch.is_active:
        raise NotFoundError("Branch not found")
    return branch

@router.post("", response_model=BranchOut)
async def create_branch(
    branch_in: BranchCreate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    branch = Branch(**branch_in.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch

@router.patch("/{branch_id}", response_model=BranchOut)
async def update_branch(
    branch_id: uuid.UUID,
    branch_in: BranchUpdate,
    current_user: CurrentUser = Depends(require_roles(StaffRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise NotFoundError("Branch not found")
        
    update_data = branch_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(branch, key, value)
        
    await db.commit()
    await db.refresh(branch)
    return branch
