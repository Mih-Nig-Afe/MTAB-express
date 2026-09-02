"""Flight status + live ADS-B adapters.

Providers (both optional — the system degrades to staff-entered times):

* AviationStack (`AVIATIONSTACK_API_KEY`) — scheduled/actual times, delay,
  departure/arrival airports. Free tier is ~100 calls/month, so we only poll
  active legs and cache the result on `parcel_flight_legs`.
* OpenSky Network — free ADS-B positions. Anonymous access works with a
  tighter credit budget; OAuth2 client credentials (`OPENSKY_CLIENT_ID` /
  `OPENSKY_CLIENT_SECRET`) raise the allowance. Callsigns are matched in
  the Horn of Africa bounding box so we never pull the global sky.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Horn of Africa — Ethiopia plus a margin so diverted/approach tracks still match.
OPENSKY_BBOX = {"lamin": 3.0, "lomin": 32.0, "lamax": 15.5, "lomax": 48.5}
OPENSKY_STATES_URL = "https://opensky-network.org/api/states/all"
OPENSKY_TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
AVIATIONSTACK_URL = "https://api.aviationstack.com/v1/flights"

_IATA_TO_ICAO = {"ET": "ETH"}
_FLIGHT_RE = re.compile(r"^([A-Z]{2,3})(\d{1,4}[A-Z]?)$")


@dataclass
class FlightSnapshot:
    flight_iata: str
    flight_icao: str | None
    status: str
    airline_iata: str | None
    airline_name: str | None
    origin_iata: str | None
    dest_iata: str | None
    scheduled_departure: datetime | None
    scheduled_arrival: datetime | None
    actual_departure: datetime | None
    estimated_arrival: datetime | None
    delay_minutes: int
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    heading: float | None
    velocity_ms: float | None
    on_ground: bool | None
    provider: str = "aviationstack"


@dataclass
class AircraftPosition:
    icao24: str
    callsign: str
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    velocity_ms: float | None
    heading: float | None
    on_ground: bool
    last_contact: datetime | None
    provider: str = "opensky"


def normalize_callsigns(flight_number: str) -> list[str]:
    raw = (flight_number or "").upper().replace(" ", "").replace("-", "")
    aliases = {raw} if raw else set()
    match = _FLIGHT_RE.match(raw)
    if match:
        airline, number = match.group(1), match.group(2)
        aliases.add(airline + number)
        if airline in _IATA_TO_ICAO:
            aliases.add(_IATA_TO_ICAO[airline] + number)
        for iata, icao in _IATA_TO_ICAO.items():
            if airline == icao:
                aliases.add(iata + number)
    return sorted(aliases)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_aviationstack_flight(payload: dict) -> FlightSnapshot | None:
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not rows:
        return None
    row = rows[0]
    flight = row.get("flight") or {}
    airline = row.get("airline") or {}
    departure = row.get("departure") or {}
    arrival = row.get("arrival") or {}
    live = row.get("live") or {}
    delay = departure.get("delay") or arrival.get("delay") or 0
    speed_kmh = live.get("speed_horizontal")
    velocity_ms = (float(speed_kmh) / 3.6) if speed_kmh else None
    return FlightSnapshot(
        flight_iata=(flight.get("iata") or "").upper(),
        flight_icao=(flight.get("icao") or None),
        status=(row.get("flight_status") or "scheduled").lower(),
        airline_iata=airline.get("iata"),
        airline_name=airline.get("name"),
        origin_iata=departure.get("iata"),
        dest_iata=arrival.get("iata"),
        scheduled_departure=_parse_dt(departure.get("scheduled")),
        scheduled_arrival=_parse_dt(arrival.get("scheduled")),
        actual_departure=_parse_dt(departure.get("actual") or departure.get("estimated")),
        estimated_arrival=_parse_dt(arrival.get("estimated") or arrival.get("actual")),
        delay_minutes=int(delay or 0),
        latitude=live.get("latitude"),
        longitude=live.get("longitude"),
        altitude_m=live.get("altitude"),
        heading=live.get("direction"),
        velocity_ms=velocity_ms,
        on_ground=live.get("is_ground"),
        provider="aviationstack",
    )


def parse_opensky_states(payload: dict, callsigns: Iterable[str]) -> AircraftPosition | None:
    wanted = {c.upper().strip() for c in callsigns}
    for row in payload.get("states") or []:
        if not row or len(row) < 11:
            continue
        callsign = (row[1] or "").strip().upper()
        if callsign not in wanted:
            continue
        last_contact = row[4]
        ts = datetime.fromtimestamp(last_contact, tz=timezone.utc) if last_contact else None
        return AircraftPosition(
            icao24=row[0],
            callsign=callsign,
            longitude=row[5],
            latitude=row[6],
            altitude_m=row[7],
            on_ground=bool(row[8]),
            velocity_ms=row[9],
            heading=row[10],
            last_contact=ts,
        )
    return None


_opensky_token: str | None = None
_opensky_token_expiry: float = 0


def _opensky_headers() -> dict[str, str]:
    token = _get_opensky_token()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _get_opensky_token() -> str | None:
    global _opensky_token, _opensky_token_expiry
    import time

    client_id = getattr(settings, "opensky_client_id", "") or ""
    client_secret = getattr(settings, "opensky_client_secret", "") or ""
    if not client_id or not client_secret:
        return None
    if _opensky_token and time.time() < _opensky_token_expiry - 60:
        return _opensky_token
    try:
        response = httpx.post(
            OPENSKY_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=15,
        )
        response.raise_for_status()
        body = response.json()
        _opensky_token = body.get("access_token")
        _opensky_token_expiry = time.time() + int(body.get("expires_in") or 1800)
        return _opensky_token
    except Exception:
        logger.warning("OpenSky OAuth token request failed", exc_info=True)
        return None


def fetch_opensky_position(flight_number: str) -> AircraftPosition | None:
    aliases = normalize_callsigns(flight_number)
    if not aliases:
        return None
    try:
        response = httpx.get(
            OPENSKY_STATES_URL,
            params=OPENSKY_BBOX,
            headers=_opensky_headers(),
            timeout=20,
        )
        if response.status_code == 429:
            logger.warning("OpenSky rate-limited")
            return None
        response.raise_for_status()
        return parse_opensky_states(response.json(), aliases)
    except Exception:
        logger.warning("OpenSky states request failed", exc_info=True)
        return None


def fetch_aviationstack_flight(flight_number: str) -> FlightSnapshot | None:
    api_key = getattr(settings, "aviationstack_api_key", "") or ""
    if not api_key:
        return None
    iata = normalize_callsigns(flight_number)
    flight_iata = next((c for c in iata if len(c) >= 4 and c[:2] == "ET" and c[:3] != "ETH"), None) or flight_number.upper()
    # Prefer IATA form (ET123) which AviationStack indexes on.
    if flight_iata.startswith("ETH"):
        flight_iata = "ET" + flight_iata[3:]
    try:
        response = httpx.get(
            AVIATIONSTACK_URL,
            params={"access_key": api_key, "flight_iata": flight_iata},
            timeout=20,
        )
        response.raise_for_status()
        return parse_aviationstack_flight(response.json())
    except Exception:
        logger.warning("AviationStack request failed", exc_info=True)
        return None
