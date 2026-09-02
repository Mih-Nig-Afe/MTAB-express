"""Lane ETA / promised-delivery math for Ethiopian air + ground express.

Remaining time is the sum of still-ahead handling buffers plus the air leg.
Once a parcel is airborne, scheduled arrival (and optional ADS-B position)
overrides the typical block time for that airport pair.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

# Typical Ethiopian Airlines domestic block times (minutes). Symmetric pairs
# are filled below so either direction looks up in O(1).
_BLOCK: dict[tuple[str, str], int] = {
    ("ADD", "DIR"): 70,
    ("ADD", "BJR"): 60,
    ("ADD", "GDQ"): 75,
    ("ADD", "MQX"): 80,
    ("ADD", "JIM"): 60,
    ("ADD", "AWA"): 50,
    ("ADD", "AMH"): 65,
    ("ADD", "AXU"): 85,
    ("ADD", "LLI"): 60,
    ("ADD", "GMB"): 85,
    ("ADD", "ASO"): 80,
    ("ADD", "BCO"): 90,
    ("DIR", "BJR"): 90,
}

TYPICAL_FLIGHT_MINUTES: dict[tuple[str, str], int] = {}
for (_o, _d), _m in _BLOCK.items():
    TYPICAL_FLIGHT_MINUTES[(_o, _d)] = _m
    TYPICAL_FLIGHT_MINUTES[(_d, _o)] = _m

DEFAULT_FLIGHT_MINUTES = 90

AIRPORTS: dict[str, dict] = {
    "ADD": {"name": "Addis Ababa Bole", "city": "Addis Ababa", "lat": 8.9779, "lon": 38.7993},
    "DIR": {"name": "Dire Dawa", "city": "Dire Dawa", "lat": 9.6247, "lon": 41.8542},
    "BJR": {"name": "Bahir Dar", "city": "Bahir Dar", "lat": 11.6081, "lon": 37.3216},
    "GDQ": {"name": "Gondar", "city": "Gondar", "lat": 12.5199, "lon": 37.4340},
    "MQX": {"name": "Mekelle Alula Aba Nega", "city": "Mekelle", "lat": 13.4674, "lon": 39.5336},
    "JIM": {"name": "Jimma Aba Segud", "city": "Jimma", "lat": 7.6661, "lon": 36.8166},
    "AWA": {"name": "Hawassa", "city": "Hawassa", "lat": 7.0692, "lon": 38.4894},
    "AMH": {"name": "Arba Minch", "city": "Arba Minch", "lat": 6.0394, "lon": 37.5905},
    "AXU": {"name": "Axum", "city": "Axum", "lat": 14.1468, "lon": 38.7728},
    "LLI": {"name": "Lalibela", "city": "Lalibela", "lat": 11.9750, "lon": 38.9797},
    "GMB": {"name": "Gambela", "city": "Gambela", "lat": 8.1288, "lon": 34.5631},
    "ASO": {"name": "Asosa", "city": "Asosa", "lat": 10.0185, "lon": 34.5863},
    "BCO": {"name": "Jinka", "city": "Jinka", "lat": 5.7829, "lon": 36.5620},
}

_CITY_IATA = {meta["city"].lower(): code for code, meta in AIRPORTS.items()}
_CITY_IATA["addis"] = "ADD"
_CITY_IATA["hawassa"] = "AWA"
_CITY_IATA["awasa"] = "AWA"
_CITY_IATA["mekelle"] = "MQX"
_CITY_IATA["mek'ele"] = "MQX"


@dataclass(frozen=True)
class HandlingBuffers:
    origin_processing_min: int = 60
    origin_to_airport_min: int = 90
    origin_airport_handling_min: int = 90
    dest_airport_handling_min: int = 90
    dest_airport_to_branch_min: int = 90
    dest_processing_min: int = 45


DEFAULT_BUFFERS = HandlingBuffers()

# Status values that still have the named segment ahead of them.
_ORIGIN_PROCESSING = {
    "created",
    "received_at_origin",
}
_ORIGIN_TO_AIRPORT = _ORIGIN_PROCESSING | {
    "processed_at_origin",
}
_ORIGIN_AIRPORT_HANDLING = _ORIGIN_TO_AIRPORT | {
    "dispatched_from_origin",
    "in_transit",
    "arrived_origin_airport",
}
_AIR_LEG = _ORIGIN_AIRPORT_HANDLING | {
    "checked_in_flight",
    "departed",
}
_DEST_AIRPORT_HANDLING = _AIR_LEG | {
    "arrived_destination_airport",
}
_DEST_TO_BRANCH = _DEST_AIRPORT_HANDLING | {
    "released_from_airport",
}
_DEST_PROCESSING = _DEST_TO_BRANCH | {
    "arrived_at_destination",
}

_DONE = {"ready_for_pickup", "delivered", "returned", "cancelled", "lost", "distributed_to_branch"}


def airport_for_city(city: str | None) -> str | None:
    if not city:
        return None
    return _CITY_IATA.get(city.strip().lower())


def typical_flight_minutes(origin_iata: str | None, dest_iata: str | None) -> int:
    if not origin_iata or not dest_iata:
        return DEFAULT_FLIGHT_MINUTES
    key = (origin_iata.upper(), dest_iata.upper())
    if key[0] == key[1]:
        return 0
    return TYPICAL_FLIGHT_MINUTES.get(key, DEFAULT_FLIGHT_MINUTES)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def live_remaining_minutes(
    lat: float,
    lon: float,
    dest_lat: float,
    dest_lon: float,
    ground_speed_ms: float,
) -> int:
    """ADS-B remaining time: distance / ground speed, 5-minute floor."""
    if ground_speed_ms is None or ground_speed_ms <= 5:
        return 0
    km = haversine_km(lat, lon, dest_lat, dest_lon)
    hours = km / (ground_speed_ms * 3.6)
    return max(5, int(round(hours * 60)))


def _flight_remaining(
    status: str,
    now: datetime,
    origin_iata: str | None,
    dest_iata: str | None,
    scheduled_arrival: datetime | None,
    delay_minutes: int,
    live: Mapping[str, float] | None,
) -> int:
    if status not in _AIR_LEG:
        return 0
    dest_meta = AIRPORTS.get((dest_iata or "").upper())
    if live and dest_meta and live.get("ground_speed_ms"):
        return live_remaining_minutes(
            float(live["lat"]),
            float(live["lon"]),
            dest_meta["lat"],
            dest_meta["lon"],
            float(live["ground_speed_ms"]),
        )
    if status in {"departed", "checked_in_flight"} and scheduled_arrival:
        arrival = scheduled_arrival
        if arrival.tzinfo is None:
            arrival = arrival.replace(tzinfo=timezone.utc)
        minutes = int((arrival - now).total_seconds() / 60) + int(delay_minutes or 0)
        return max(0, minutes)
    if status in {"created", "received_at_origin", "processed_at_origin",
                  "dispatched_from_origin", "in_transit", "arrived_origin_airport",
                  "checked_in_flight"}:
        return typical_flight_minutes(origin_iata, dest_iata)
    return typical_flight_minutes(origin_iata, dest_iata)


def remaining_minutes(
    *,
    status: str,
    now: datetime,
    origin_iata: str | None,
    dest_iata: str | None,
    created_at: datetime | None = None,  # reserved for cutoff-aware future use
    buffers: HandlingBuffers = DEFAULT_BUFFERS,
    scheduled_arrival: datetime | None = None,
    delay_minutes: int = 0,
    live: Mapping[str, float] | None = None,
) -> int:
    status = (status or "").lower()
    if status in {"delivered", "cancelled", "returned"}:
        return 0
    if status in {"ready_for_pickup", "distributed_to_branch"}:
        return 0

    total = 0
    if status in _ORIGIN_PROCESSING:
        total += buffers.origin_processing_min
    if status in _ORIGIN_TO_AIRPORT:
        total += buffers.origin_to_airport_min
    if status in _ORIGIN_AIRPORT_HANDLING:
        total += buffers.origin_airport_handling_min
    total += _flight_remaining(
        status, now, origin_iata, dest_iata, scheduled_arrival, delay_minutes, live
    )
    if status in _DEST_AIRPORT_HANDLING:
        total += buffers.dest_airport_handling_min
    if status in _DEST_TO_BRANCH:
        total += buffers.dest_airport_to_branch_min
    if status in _DEST_PROCESSING:
        total += buffers.dest_processing_min
    return max(0, int(total))


def promised_delivery_at(
    *,
    created_at: datetime,
    origin_iata: str | None,
    dest_iata: str | None,
    buffers: HandlingBuffers = DEFAULT_BUFFERS,
    scheduled_departure: datetime | None = None,
) -> datetime:
    origin_side = (
        buffers.origin_processing_min
        + buffers.origin_to_airport_min
        + buffers.origin_airport_handling_min
    )
    dest_side = (
        buffers.dest_airport_handling_min
        + buffers.dest_airport_to_branch_min
        + buffers.dest_processing_min
    )
    flight = typical_flight_minutes(origin_iata, dest_iata)
    earliest_depart = created_at + timedelta(minutes=origin_side)
    if scheduled_departure is not None:
        dep = scheduled_departure
        if dep.tzinfo is None:
            dep = dep.replace(tzinfo=created_at.tzinfo or timezone.utc)
        wheels_up = max(earliest_depart, dep)
    else:
        wheels_up = earliest_depart
    return wheels_up + timedelta(minutes=flight + dest_side)


def eta_from_now(
    *,
    status: str,
    now: datetime,
    origin_iata: str | None,
    dest_iata: str | None,
    created_at: datetime | None = None,
    buffers: HandlingBuffers = DEFAULT_BUFFERS,
    scheduled_arrival: datetime | None = None,
    delay_minutes: int = 0,
    live: Mapping[str, float] | None = None,
) -> datetime:
    mins = remaining_minutes(
        status=status,
        now=now,
        origin_iata=origin_iata,
        dest_iata=dest_iata,
        created_at=created_at,
        buffers=buffers,
        scheduled_arrival=scheduled_arrival,
        delay_minutes=delay_minutes,
        live=live,
    )
    return now + timedelta(minutes=mins)
