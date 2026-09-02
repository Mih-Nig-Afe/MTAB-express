"""
Seed one staff account per role so every dashboard journey is testable.

Idempotent: skips phones that already exist.

Run inside the api container:
    docker compose -f docker-compose.dev.yml exec api python scripts/seed_staff.py
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Branch, StaffRole, StaffUser
from app.core.security import hash_password

STAFF_DATA = [
    # (name, phone, password, role, branch_code)
    ("Bole Branch Manager", "+251911000020", "manager123", StaffRole.MANAGER, "AA1"),
    ("Bole Counter Operator", "+251911000010", "operator123", StaffRole.OPERATOR, "AA1"),
    ("Hawassa Counter Operator", "+251911000011", "operator123", StaffRole.OPERATOR, "HW"),
    ("Bole Airport Cargo Operator", "+251911000012", "operator123", StaffRole.OPERATOR, "ADD"),
    ("Central Hub Operator", "+251911000013", "operator123", StaffRole.OPERATOR, "HUB"),
    ("Addis Branch 22 Operator", "+251911000022", "operator123", StaffRole.OPERATOR, "AA22"),
    ("Fleet Driver Abebe", "+251911000030", "driver123", StaffRole.DRIVER, "AA1"),
]


async def seed_staff():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Branch))
        branches = {b.code: b.id for b in result.scalars().all()}

        for name, phone, password, role, branch_code in STAFF_DATA:
            existing = (await db.execute(
                select(StaffUser).where(StaffUser.phone == phone)
            )).scalar_one_or_none()
            if existing:
                print(f"Skipped staff: {phone} (already exists)")
                continue

            branch_id = branches.get(branch_code)
            if not branch_id:
                print(f"ERROR: branch {branch_code} missing — run seed_branches.py first")
                return

            db.add(StaffUser(
                name=name,
                phone=phone,
                password_hash=hash_password(password),
                role=role,
                branch_id=branch_id,
            ))
            print(f"Added staff: {name} ({role.value}) {phone} @ {branch_code}")

        await db.commit()
        print("Staff seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_staff())
