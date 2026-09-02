import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Branch, FacilityType

BRANCHES_DATA = [
    {"code": "HW", "name": "Hawassa", "city": "Hawassa", "phone": "0911000001", "facility_type": FacilityType.BRANCH},
    {"code": "AA1", "name": "Addis Ababa - Bole", "city": "Addis Ababa", "phone": "0911000002", "facility_type": FacilityType.BRANCH},
    {"code": "AA2", "name": "Addis Ababa - Megenagna", "city": "Addis Ababa", "phone": "0911000003", "facility_type": FacilityType.BRANCH},
    {"code": "AA3", "name": "Addis Ababa - Piassa", "city": "Addis Ababa", "phone": "0911000004", "facility_type": FacilityType.BRANCH},
    {"code": "AA4", "name": "Addis Ababa - Kality", "city": "Addis Ababa", "phone": "0911000005", "facility_type": FacilityType.BRANCH},
    {"code": "AD", "name": "Adama", "city": "Adama", "phone": "0911000006", "facility_type": FacilityType.BRANCH},
    {"code": "DD", "name": "Dire Dawa", "city": "Dire Dawa", "phone": "0911000007", "facility_type": FacilityType.BRANCH},
    {"code": "JJ", "name": "Jimma", "city": "Jimma", "phone": "0911000008", "facility_type": FacilityType.BRANCH},
    # Airports — scan routing for linehaul
    {"code": "ADD", "name": "Addis Ababa Bole Airport", "city": "Addis Ababa", "phone": "0911000100",
     "facility_type": FacilityType.AIRPORT, "airport_iata": "ADD"},
    {"code": "BJR", "name": "Bahir Dar Airport", "city": "Bahir Dar", "phone": "0911000101",
     "facility_type": FacilityType.AIRPORT, "airport_iata": "BJR"},
    {"code": "DIR", "name": "Dire Dawa Airport", "city": "Dire Dawa", "phone": "0911000102",
     "facility_type": FacilityType.AIRPORT, "airport_iata": "DIR"},
    {"code": "HUB", "name": "Central Sorting Hub", "city": "Addis Ababa", "phone": "0911000200",
     "facility_type": FacilityType.SORTING_HUB},
    {"code": "AA22", "name": "Addis Ababa - Branch 22", "city": "Addis Ababa", "phone": "0911000022",
     "facility_type": FacilityType.BRANCH},
]


async def seed_branches():
    async with AsyncSessionLocal() as db:
        for branch_data in BRANCHES_DATA:
            stmt = select(Branch).where(Branch.code == branch_data["code"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                db.add(Branch(**branch_data))
                print(f"Added branch: {branch_data['name']} ({branch_data['code']})")
            else:
                for key, value in branch_data.items():
                    setattr(existing, key, value)
                print(f"Updated branch: {branch_data['code']}")

        await db.commit()
        print("Branch seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_branches())
