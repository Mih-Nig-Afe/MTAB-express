"""Public, unauthenticated config — brand identity for all clients."""
from fastapi import APIRouter

from app.core.brand import brand_name, brand_short, sms_sender_id, tracking_example, tracking_prefix

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/brand")
async def get_public_brand():
    """Return white-label branding. Single source of truth from server env."""
    prefix = tracking_prefix()
    return {
        "brand_name": brand_name(),
        "brand_short": brand_short(),
        "tracking_prefix": prefix,
        "tracking_example": tracking_example(),
        "tracking_placeholder": f"{prefix}-HW-000000" if prefix else "",
        "sms_sender_id": sms_sender_id(),
    }
