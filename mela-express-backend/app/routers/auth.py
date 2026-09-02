from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import StaffUser
from app.schemas import LoginRequest, TokenResponse, RefreshRequest, StaffOut
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

from app.core.phones import normalize_phone as _normalize_phone

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    norm_phone = _normalize_phone(request.phone)
    raw_phone = request.phone.strip()
    
    result = await db.execute(
        select(StaffUser).where(
            (StaffUser.phone == norm_phone) | (StaffUser.phone == raw_phone)
        ).where(StaffUser.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "branch_id": str(user.branch_id) if user.branch_id else None
    }
    
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest):
    try:
        payload = decode_token(request.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid payload")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    new_payload = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "branch_id": payload.get("branch_id")
    }
    access_token = create_access_token(new_payload)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        token_type="bearer"
    )

@router.get("/me", response_model=StaffOut)
async def me(current_user: StaffUser = Depends(get_current_user)):
    return current_user
