"""Poll AviationStack + OpenSky for parcels currently on an air leg."""
import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import ParcelFlightLeg, ParcelStatus
from app.services.flight_tracking import fetch_aviationstack_flight, fetch_opensky_position
from app.services.journey import refresh_eta

logger = logging.getLogger(__name__)

_AIRBORNE = {
    ParcelStatus.CHECKED_IN_FLIGHT,
    ParcelStatus.DEPARTED,
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
}
_ACTIVE_FLIGHT = {"scheduled", "active", "delayed"}


def _apply_snapshot(leg: ParcelFlightLeg, snap) -> None:
    leg.status = snap.status or leg.status
    if snap.airline_iata:
        leg.airline_iata = snap.airline_iata
    if snap.airline_name:
        leg.airline_name = snap.airline_name
    if snap.origin_iata:
        leg.origin_iata = snap.origin_iata
    if snap.dest_iata:
        leg.dest_iata = snap.dest_iata
    if snap.scheduled_departure:
        leg.scheduled_departure = snap.scheduled_departure
    if snap.scheduled_arrival:
        leg.scheduled_arrival = snap.scheduled_arrival
    if snap.actual_departure:
        leg.actual_departure = snap.actual_departure
    if snap.estimated_arrival:
        leg.scheduled_arrival = leg.scheduled_arrival or snap.estimated_arrival
    leg.delay_minutes = snap.delay_minutes or 0
    if snap.latitude is not None:
        leg.latitude = snap.latitude
        leg.longitude = snap.longitude
        leg.altitude_m = snap.altitude_m
        leg.heading = snap.heading
        leg.velocity_ms = snap.velocity_ms
        leg.on_ground = snap.on_ground
        leg.last_position_at = datetime.now(timezone.utc)
    leg.provider = snap.provider
    leg.last_polled_at = datetime.now(timezone.utc)


def _apply_position(leg: ParcelFlightLeg, pos) -> None:
    if pos.latitude is None:
        return
    leg.latitude = pos.latitude
    leg.longitude = pos.longitude
    leg.altitude_m = pos.altitude_m
    leg.heading = pos.heading
    leg.velocity_ms = pos.velocity_ms
    leg.on_ground = pos.on_ground
    leg.last_position_at = pos.last_contact or datetime.now(timezone.utc)
    if pos.on_ground and leg.status == "active":
        # Still airborne until staff scans landed; keep status active.
        pass
    elif not pos.on_ground:
        leg.status = "active"
    if not leg.provider:
        leg.provider = "opensky"
    elif "opensky" not in (leg.provider or ""):
        leg.provider = f"{leg.provider}+opensky"
    leg.last_polled_at = datetime.now(timezone.utc)


async def _poll_async() -> int:
    updated = 0
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ParcelFlightLeg)
            .options(selectinload(ParcelFlightLeg.parcel))
            .where(ParcelFlightLeg.status.in_(tuple(_ACTIVE_FLIGHT)))
        )
        legs = (await db.execute(stmt)).scalars().all()
        for leg in legs:
            parcel = leg.parcel
            if parcel is None or parcel.status not in _AIRBORNE | {
                ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
                ParcelStatus.RELEASED_FROM_AIRPORT,
            }:
                if parcel and parcel.status in (
                    ParcelStatus.DELIVERED,
                    ParcelStatus.CANCELLED,
                    ParcelStatus.RETURNED,
                ):
                    leg.status = "landed" if parcel.status == ParcelStatus.DELIVERED else leg.status
                continue

            snap = fetch_aviationstack_flight(leg.flight_number)
            if snap:
                _apply_snapshot(leg, snap)
            pos = fetch_opensky_position(leg.flight_number)
            if pos:
                _apply_position(leg, pos)
            if snap or pos:
                refresh_eta(parcel, leg)
                updated += 1
        await db.commit()
    return updated


@shared_task(name="app.workers.flight_tasks.poll_active_flights")
def poll_active_flights():
    try:
        return asyncio.run(_poll_async())
    except Exception:
        logger.exception("poll_active_flights failed")
        raise
