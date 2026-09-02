"""
Seed realistic sample data: customers, parcels across the full lifecycle,
status history timelines, and payments.

Idempotent: skips any parcel whose tracking_code already exists.

Run inside the api container:
    docker compose -f docker-compose.dev.yml exec api python scripts/seed_sample_data.py
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import (
    Branch,
    Customer,
    Parcel,
    ParcelStatus,
    ParcelStatusHistory,
    Payment,
    PaymentMethod,
    PaymentMode,
    PaymentStatus,
    StaffUser,
)

CUSTOMERS_DATA = [
    {"phone": "+251911234567", "name": "Abebe Kebede"},
    {"phone": "+251922345678", "name": "Hanna Girma"},
    {"phone": "+251933456789", "name": "Dawit Tesfaye"},
    {"phone": "+251944567890", "name": "Selamawit Alemu"},
]

# (code, origin, dest, sender_idx, receiver_name, receiver_phone, receiver_idx,
#  description, weight, declared_value, price, mode, method, status, history_notes)
PARCELS_DATA = [
    (
        "MEX-AA1-483920", "AA1", "HW", 0, "Chaltu Bekele", "+251966789012", None,
        "Laptop bag with documents", 2.5, 15000, 180,
        PaymentMode.BEFORE, PaymentMethod.CASH, ParcelStatus.CREATED,
        ["Parcel registered at Bole branch counter"],
    ),
    (
        "MEX-HW-271654", "HW", "AA1", 1, "Yonas Haile", "+251977890123", None,
        "Traditional habesha kemis (2 pcs)", 4.0, 6000, 320,
        PaymentMode.BEFORE, PaymentMethod.CASH, ParcelStatus.RECEIVED_AT_ORIGIN,
        [
            "Parcel registered at Hawassa branch",
            "Received and scanned at Hawassa warehouse",
        ],
    ),
    (
        "MEX-AA2-639817", "AA2", "DD", 2, "Meron Abeje", "+251988901234", None,
        "Smartphone (boxed)", 0.8, 45000, 250,
        PaymentMode.BEFORE, PaymentMethod.CHAPA, ParcelStatus.IN_TRANSIT,
        [
            "Parcel registered at Megenagna branch",
            "Received and scanned at Megenagna warehouse",
            "Loaded on vehicle AA2→AD transfer",
            "Departed Addis Ababa toward Dire Dawa via Adama corridor",
        ],
    ),
    (
        "MEX-DD-552340", "DD", "JJ", 3, "Kalkidan Fikru", "+251999012345", None,
        "Coffee beans (1 kg, vacuum sealed)", 1.2, 900, 210,
        PaymentMode.AFTER, None, ParcelStatus.READY_FOR_PICKUP,
        [
            "Parcel registered at Dire Dawa branch",
            "Received and scanned at Dire Dawa warehouse",
            "In transit toward Jimma",
            "Arrived at Jimma branch — ready for pickup",
        ],
    ),
    (
        "MEX-JJ-908341", "JJ", "AA3", 0, "Biruk Solomon", "+251900123456", None,
        "Barber clippers set", 3.5, 8000, 290,
        PaymentMode.AFTER, PaymentMethod.CASH, ParcelStatus.DELIVERED,
        [
            "Parcel registered at Jimma branch",
            "Received and scanned at Jimma warehouse",
            "In transit toward Addis Ababa",
            "Arrived at Piassa branch — out for delivery",
            "Delivered and signed for by receiver",
        ],
    ),
    (
        "MEX-AD-114728", "AD", "AA4", 1, "Nahom Zerihun", "+251901234567", None,
        "Textile rolls (sample batch)", 12.0, 22000, 480,
        PaymentMode.BEFORE, PaymentMethod.CHAPA, ParcelStatus.ON_HOLD,
        [
            "Parcel registered at Adama branch",
            "Placed on hold: incomplete receiver address, awaiting customer call",
        ],
    ),
]


async def seed_sample_data():
    async with AsyncSessionLocal() as db:
        # Admin who registers the parcels
        result = await db.execute(select(StaffUser).where(StaffUser.phone == "+251900000000"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("ERROR: run scripts/seed_admin.py first (no admin found).")
            return

        # Branch lookup
        result = await db.execute(select(Branch))
        branches = {b.code: b for b in result.scalars().all()}
        missing = {code for _, o, d, *_ in PARCELS_DATA for code in (o, d)} - set(branches)
        if missing:
            print(f"ERROR: run scripts/seed_branches.py first (missing branches: {missing}).")
            return

        # Customers
        customers = {}
        for c in CUSTOMERS_DATA:
            result = await db.execute(select(Customer).where(Customer.phone == c["phone"]))
            cust = result.scalar_one_or_none()
            if not cust:
                cust = Customer(phone=c["phone"], name=c["name"])
                db.add(cust)
                await db.flush()
                print(f"Added customer: {c['name']} ({c['phone']})")
            else:
                print(f"Skipped customer: {c['phone']} (already exists)")
            customers[c["phone"]] = cust

        now = datetime.now(timezone.utc)

        # Parcels
        for row in PARCELS_DATA:
            (code, orig, dest, sidx, r_name, r_phone, _ridx,
             desc, weight, value, price, mode, method, status, history) = row

            existing = (await db.execute(
                select(Parcel).where(Parcel.tracking_code == code)
            )).scalar_one_or_none()
            if existing:
                print(f"Skipped parcel: {code} (already exists)")
                continue

            sender = CUSTOMERS_DATA[sidx]["phone"]
            created_at = now - timedelta(days=len(history) * 2)

            parcel = Parcel(
                tracking_code=code,
                origin_branch_id=branches[orig].id,
                destination_branch_id=branches[dest].id,
                sender_id=customers[sender].id,
                receiver_name=r_name,
                receiver_phone=r_phone,
                description=desc,
                weight_kg=weight,
                declared_value=value,
                price=price,
                payment_mode=mode,
                payment_method=method,
                payment_status=(
                    PaymentStatus.PENDING if mode == PaymentMode.AFTER or method is None
                    else PaymentStatus.PAID
                ),
                status=status,
                created_by=admin.id,
                created_at=created_at,
            )
            db.add(parcel)
            await db.flush()

            # Timeline entries spread over the last days
            for i, note in enumerate(history):
                db.add(ParcelStatusHistory(
                    parcel_id=parcel.id,
                    from_status=None if i == 0 else ParcelStatus.CREATED,
                    to_status=status if i == len(history) - 1 else ParcelStatus.CREATED
                    if i == 0 else status,
                    changed_by=admin.id,
                    branch_id=branches[orig].id,
                    note=note,
                    timestamp=created_at + timedelta(hours=i * 14),
                ))

            # Payment record when already paid
            if parcel.payment_status == PaymentStatus.PAID:
                db.add(Payment(
                    parcel_id=parcel.id,
                    amount=price,
                    method=method,
                    chapa_tx_ref=f"SEED-{code.replace('-', '')}" if method == PaymentMethod.CHAPA else None,
                    status=PaymentStatus.PAID,
                    collected_by=admin.id,
                    verified_at=created_at + timedelta(hours=2),
                    created_at=created_at + timedelta(hours=1),
                ))

            label = f"{status.value}" + (" (payment pending)" if parcel.payment_status == PaymentStatus.PENDING else "")
            print(f"Added parcel: {code} [{label}]")

        await db.commit()
        print("Sample data seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_sample_data())
