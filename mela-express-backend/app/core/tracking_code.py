import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models import Parcel

async def generate_tracking_code(branch_code: str, db: AsyncSession) -> str:
    prefix = settings.tracking_prefix.upper()
    for _ in range(5):
        random_num = f"{random.randint(100000, 999999):06d}"
        code = f"{prefix}-{branch_code}-{random_num}"
        result = await db.execute(select(Parcel).where(Parcel.tracking_code == code))
        if not result.scalar_one_or_none():
            return code
    raise RuntimeError("Could not generate a unique tracking code after 5 attempts")
