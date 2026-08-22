import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import StaffUser, StaffRole
from app.core.security import get_password_hash

async def seed_admin():
    async with AsyncSessionLocal() as db:
        admin_phone = "+251900000000"
        
        stmt = select(StaffUser).where(StaffUser.phone == admin_phone)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            new_admin = StaffUser(
                name="System Admin",
                phone=admin_phone,
                password_hash=get_password_hash("admin123"),
                role=StaffRole.ADMIN,
                branch_id=None
            )
            db.add(new_admin)
            await db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
