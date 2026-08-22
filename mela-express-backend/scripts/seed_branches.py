import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Branch

BRANCHES_DATA = [
    {"code": "HW", "name": "Hawassa", "city": "Hawassa", "phone": "0911000001"},
    {"code": "AA1", "name": "Addis Ababa - Bole", "city": "Addis Ababa", "phone": "0911000002"},
    {"code": "AA2", "name": "Addis Ababa - Megenagna", "city": "Addis Ababa", "phone": "0911000003"},
    {"code": "AA3", "name": "Addis Ababa - Piassa", "city": "Addis Ababa", "phone": "0911000004"},
    {"code": "AA4", "name": "Addis Ababa - Kality", "city": "Addis Ababa", "phone": "0911000005"},
    {"code": "AD", "name": "Adama", "city": "Adama", "phone": "0911000006"},
    {"code": "DD", "name": "Dire Dawa", "city": "Dire Dawa", "phone": "0911000007"},
    {"code": "JJ", "name": "Jimma", "city": "Jimma", "phone": "0911000008"},
]

async def seed_branches():
    async with AsyncSessionLocal() as db:
        for branch_data in BRANCHES_DATA:
            stmt = select(Branch).where(Branch.code == branch_data["code"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_branch = Branch(**branch_data)
                db.add(new_branch)
                print(f"Added branch: {branch_data['name']} ({branch_data['code']})")
            else:
                print(f"Skipped branch: {branch_data['code']} (already exists)")
        
        await db.commit()
        print("Branch seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_branches())
