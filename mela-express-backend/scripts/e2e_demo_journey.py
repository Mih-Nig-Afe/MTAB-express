#!/usr/bin/env python3
"""
End-to-end demo: Hawassa (HW) → flight ET302 → Addis Ababa Branch 22 (AA22).

Run inside api container:
  docker compose -f docker-compose.dev.yml exec api python scripts/e2e_demo_journey.py

Or from host (API on 8001):
  API_BASE=http://localhost:8001/api python scripts/e2e_demo_journey.py
"""
from __future__ import annotations

import asyncio
import os
import sys

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = os.environ.get("API_BASE", "http://127.0.0.1:8000/api").rstrip("/")
FLIGHT = "ET302"
SENDER_PHONE = "+251911234567"
RECEIVER_PHONE = "+251922345678"

STAFF = {
    "HW": ("+251911000011", "operator123"),
    "HUB": ("+251911000013", "operator123"),
    "ADD": ("+251911000012", "operator123"),
    "AA22": ("+251911000022", "operator123"),
}


async def login(client: httpx.AsyncClient, phone: str, password: str) -> str:
    r = await client.post(f"{API}/auth/login", json={"phone": phone, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


async def branch_map(client: httpx.AsyncClient, token: str) -> dict[str, str]:
    r = await client.get(f"{API}/branches", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return {b["code"]: b["id"] for b in r.json()}


async def scan(client: httpx.AsyncClient, token: str, code: str, flight: str | None = None) -> dict:
    body: dict = {"code": code}
    if flight:
        body["flight_number"] = flight
    r = await client.post(f"{API}/parcels/scan", json=body, headers={"Authorization": f"Bearer {token}"})
    if r.status_code >= 400:
        print(f"  SCAN FAIL ({r.status_code}): {r.text}")
        r.raise_for_status()
    data = r.json()
    print(f"  → {data.get('status_label', data.get('status'))} @ {data.get('station', '?')}")
    return data


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        admin_token = await login(client, "+251900000000", "admin123")
        branches = await branch_map(client, admin_token)
        for code in ("HW", "AA22", "ADD", "HUB"):
            if code not in branches:
                print(f"ERROR: branch {code} missing — run seed_branches.py")
                return

        hw_token = await login(client, *STAFF["HW"])
        create_body = {
            "origin_branch_id": branches["HW"],
            "destination_branch_id": branches["AA22"],
            "sender_phone": SENDER_PHONE,
            "sender_name": "Abebe Kebede",
            "receiver_phone": RECEIVER_PHONE,
            "receiver_name": "Hanna Girma",
            "description": "E2E demo — Hawassa to Addis Branch 22 via ET302",
            "weight_kg": 3.5,
            "length_cm": 40,
            "width_cm": 30,
            "height_cm": 20,
            "content_category": "general",
            "payment_mode": "before",
            "payment_method": "cash",
            "declared_value": 5000,
        }
        r = await client.post(
            f"{API}/parcels",
            json=create_body,
            headers={"Authorization": f"Bearer {hw_token}"},
        )
        r.raise_for_status()
        parcel = r.json()
        code = parcel["tracking_code"]
        parcel_id = parcel["id"]
        print(f"\n✅ Created parcel: {code}")

        # Prepaid — collect cash before dispatch scans
        pay = await client.post(
            f"{API}/payments/cash/{parcel_id}/collect",
            json={},
            headers={"Authorization": f"Bearer {hw_token}"},
        )
        pay.raise_for_status()
        print("  💰 Cash payment collected")

        # Origin branch scans
        print("\n— Hawassa branch —")
        for _ in range(3):
            try:
                await scan(client, hw_token, code)
            except httpx.HTTPStatusError:
                break

        # Hub — single in-transit scan only (then airport for flight leg)
        print("\n— Sorting hub (in transit) —")
        hub_token = await login(client, *STAFF["HUB"])
        try:
            await scan(client, hub_token, code)
        except httpx.HTTPStatusError:
            pass

        # Airport origin + flight ET302 (Hawassa corridor → ADD)
        print("\n— Bole Airport (ADD) — flight", FLIGHT)
        add_token = await login(client, *STAFF["ADD"])
        for i in range(6):
            try:
                await scan(client, add_token, code, flight=FLIGHT)
            except httpx.HTTPStatusError:
                break

        # Destination branch
        print("\n— Addis Ababa Branch 22 —")
        aa22_token = await login(client, *STAFF["AA22"])
        for _ in range(5):
            try:
                await scan(client, aa22_token, code)
            except httpx.HTTPStatusError:
                break

        # Public track
        tr = await client.get(f"{API}/parcels/track/{code}")
        tr.raise_for_status()
        track = tr.json()
        print(f"\n📍 Public track status: {track['status']} ({track.get('carrier_status_label', '')})")
        print(f"   Route: {track['origin_branch_name']} → {track['destination_branch_name']}")
        if track.get("flight"):
            fl = track["flight"]
            print(f"   Flight: {fl.get('flight_number')} {fl.get('origin_iata')}→{fl.get('dest_iata')} [{fl.get('status')}]")
        print(f"   Journey events: {len(track.get('journey_events', []))}")
        print(f"   History entries: {len(track.get('status_history', []))}")

        portal = os.environ.get("PUBLIC_PORTAL_URL", "http://localhost:3011")
        print(f"\n🌐 Live tracking: {portal}/track/{code}")
        print(f"📱 Telegram: /track {code}")
        print(f"   Link phone {SENDER_PHONE} via bot to see in My Orders")


if __name__ == "__main__":
    asyncio.run(main())
