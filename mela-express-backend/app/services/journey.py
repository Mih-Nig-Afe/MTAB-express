"""Apply a scan, attach a flight, recompute ETA, and notify both parties."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.eta import airport_for_city, eta_from_now, promised_delivery_at, remaining_minutes
from app.core.pickup_reminders import reminder_day_number
from app.core.state_machine import allowed_next, validate_transition
from app.models import (
    Branch,
    Customer,
    Parcel,
    ParcelFlightLeg,
    ParcelJourneyEvent,
    ParcelStatus,
    ParcelStatusHistory,
    PickupReminderLog,
)
from app.schemas.parcels import EtaOut, FlightLegOut, JourneyEventOut
from app.services.notifications import notify_parcel_parties


def _now() -> datetime:
    return datetime.now(timezone.utc)


def infer_airport(branch: Branch | None) -> str | None:
    if branch is None:
        return None
    if branch.airport_iata:
        return branch.airport_iata.upper()
    return airport_for_city(branch.city)


def _live_from_leg(leg: ParcelFlightLeg | None) -> dict | None:
    if not leg or leg.latitude is None or leg.longitude is None:
        return None
    return {
        "lat": float(leg.latitude),
        "lon": float(leg.longitude),
        "ground_speed_ms": float(leg.velocity_ms or 0),
    }


async def latest_flight_leg(db: AsyncSession, parcel_id) -> ParcelFlightLeg | None:
    result = await db.execute(
        select(ParcelFlightLeg)
        .where(ParcelFlightLeg.parcel_id == parcel_id)
        .order_by(ParcelFlightLeg.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def refresh_eta(parcel: Parcel, leg: ParcelFlightLeg | None = None) -> None:
    now = _now()
    live = _live_from_leg(leg)
    parcel.current_eta_at = eta_from_now(
        status=parcel.status.value,
        now=now,
        origin_iata=parcel.origin_airport_iata or (leg.origin_iata if leg else None),
        dest_iata=parcel.dest_airport_iata or (leg.dest_iata if leg else None),
        created_at=parcel.created_at,
        scheduled_arrival=(leg.actual_arrival or leg.scheduled_arrival) if leg else None,
        delay_minutes=int(leg.delay_minutes or 0) if leg else 0,
        live=live,
    )


async def seed_parcel_plan(db: AsyncSession, parcel: Parcel) -> None:
    origin = await db.get(Branch, parcel.origin_branch_id)
    dest = await db.get(Branch, parcel.destination_branch_id)
    parcel.origin_airport_iata = infer_airport(origin)
    parcel.dest_airport_iata = infer_airport(dest)
    parcel.promised_delivery_at = promised_delivery_at(
        created_at=parcel.created_at or _now(),
        origin_iata=parcel.origin_airport_iata,
        dest_iata=parcel.dest_airport_iata,
    )
    refresh_eta(parcel)


async def upsert_flight_leg(db: AsyncSession, parcel: Parcel, payload) -> ParcelFlightLeg:
    leg = await latest_flight_leg(db, parcel.id)
    fields = {
        "flight_number": (payload.flight_number or "").upper().replace(" ", ""),
        "airline_iata": (payload.airline_iata or None),
        "origin_iata": (payload.origin_airport_iata or parcel.origin_airport_iata),
        "dest_iata": (payload.destination_airport_iata or parcel.dest_airport_iata),
        "airway_bill": getattr(payload, "airway_bill", None),
        "scheduled_departure": getattr(payload, "scheduled_departure", None),
        "scheduled_arrival": getattr(payload, "scheduled_arrival", None),
    }
    if not fields["flight_number"]:
        raise ValueError("flight_number is required")
    if leg and leg.flight_number == fields["flight_number"]:
        for key, value in fields.items():
            if value is not None:
                setattr(leg, key, value)
    else:
        leg = ParcelFlightLeg(parcel_id=parcel.id, status="scheduled", **fields)
        db.add(leg)
    if fields["origin_iata"]:
        parcel.origin_airport_iata = fields["origin_iata"]
    if fields["dest_iata"]:
        parcel.dest_airport_iata = fields["dest_iata"]
    refresh_eta(parcel, leg)
    return leg


async def record_scan(
    db: AsyncSession,
    parcel: Parcel,
    *,
    to_status: ParcelStatus,
    staff_id,
    branch_id=None,
    note: str | None = None,
    location_name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    flight_payload=None,
    source: str = "staff",
) -> Parcel:
    validate_transition(parcel.status, to_status)
    from_status = parcel.status
    parcel.status = to_status

    if to_status == ParcelStatus.READY_FOR_PICKUP and parcel.pickup_ready_at is None:
        parcel.pickup_ready_at = _now()
        parcel.pickup_reminders_sent = 1
        parcel.last_pickup_reminder_at = parcel.pickup_ready_at
        if not parcel.pickup_otp:
            parcel.pickup_otp = f"{secrets.randbelow(900000) + 100000:06d}"
            parcel.otp_expires_at = _now() + timedelta(days=7)

    history = ParcelStatusHistory(
        parcel_id=parcel.id,
        from_status=from_status,
        to_status=to_status,
        changed_by=staff_id,
        branch_id=branch_id,
        note=note,
    )
    db.add(history)

    flight_number = getattr(flight_payload, "flight_number", None) if flight_payload else None
    event = ParcelJourneyEvent(
        parcel_id=parcel.id,
        event_type=to_status.value,
        to_status=to_status,
        location_name=location_name,
        facility_type=_facility_for(to_status),
        latitude=latitude,
        longitude=longitude,
        flight_number=(flight_number or "").upper() or None,
        note=note,
        source=source,
        actor_staff_id=staff_id,
    )
    db.add(event)

    leg = None
    if flight_payload and getattr(flight_payload, "flight_number", None):
        leg = await upsert_flight_leg(db, parcel, flight_payload)
        if to_status == ParcelStatus.DEPARTED:
            leg.status = "active"
            leg.actual_departure = leg.actual_departure or _now()
        elif to_status == ParcelStatus.ARRIVED_DESTINATION_AIRPORT:
            leg.status = "landed"
            leg.actual_arrival = leg.actual_arrival or _now()
        elif to_status == ParcelStatus.CHECKED_IN_FLIGHT:
            leg.status = "scheduled"
    else:
        leg = await latest_flight_leg(db, parcel.id)

    refresh_eta(parcel, leg)
    return parcel


def _facility_for(status: ParcelStatus) -> str:
    air = {
        ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
        ParcelStatus.CHECKED_IN_FLIGHT,
        ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
        ParcelStatus.RELEASED_FROM_AIRPORT,
    }
    if status == ParcelStatus.DEPARTED:
        return "aircraft"
    if status in air:
        return "airport"
    return "branch"


async def notify_after_scan(db: AsyncSession, parcel: Parcel, to_status: ParcelStatus, note: str | None) -> None:
    sender = await db.get(Customer, parcel.sender_id)
    receiver = await db.get(Customer, parcel.receiver_id) if parcel.receiver_id else None
    dest_branch = await db.get(Branch, parcel.destination_branch_id)
    notify_note = note
    if to_status == ParcelStatus.READY_FOR_PICKUP and parcel.pickup_otp:
        notify_note = f"{note or ''} OTP: {parcel.pickup_otp}".strip()
    await notify_parcel_parties(
        db=db,
        sender=sender,
        receiver=receiver,
        receiver_phone=parcel.receiver_phone,
        tracking_code=parcel.tracking_code,
        branch_name=dest_branch.name if dest_branch else "",
        to_status=to_status,
        note=notify_note,
        parcel_id=parcel.id,
        payment_status=parcel.payment_status.value if parcel.payment_status else "pending",
    )
    if to_status == ParcelStatus.READY_FOR_PICKUP:
        day = reminder_day_number(parcel.pickup_ready_at or _now(), _now())
        for role in ("sender", "receiver"):
            db.add(
                PickupReminderLog(
                    parcel_id=parcel.id,
                    day_number=day,
                    recipient_role=role,
                    channel="auto",
                    status="sent",
                )
            )


async def load_parcel_for_update(db: AsyncSession, parcel_id) -> Parcel | None:
    result = await db.execute(
        select(Parcel)
        .options(
            selectinload(Parcel.status_history),
            selectinload(Parcel.journey_events),
            selectinload(Parcel.flight_legs),
        )
        .where(Parcel.id == parcel_id)
    )
    return result.scalar_one_or_none()


def active_leg(parcel: Parcel) -> ParcelFlightLeg | None:
    legs = list(parcel.flight_legs or [])
    if not legs:
        return None
    return max(legs, key=lambda item: item.created_at)


def eta_view(parcel: Parcel, leg: ParcelFlightLeg | None = None) -> EtaOut:
    leg = leg or active_leg(parcel)
    now = _now()
    live = _live_from_leg(leg)
    remaining = remaining_minutes(
        status=parcel.status.value,
        now=now,
        origin_iata=parcel.origin_airport_iata or (leg.origin_iata if leg else None),
        dest_iata=parcel.dest_airport_iata or (leg.dest_iata if leg else None),
        created_at=parcel.created_at,
        scheduled_arrival=(leg.actual_arrival or leg.scheduled_arrival) if leg else None,
        delay_minutes=int(leg.delay_minutes or 0) if leg else 0,
        live=live,
    )
    delay = int(leg.delay_minutes or 0) if leg else 0
    promised = parcel.promised_delivery_at
    eta_at = parcel.current_eta_at
    on_time = None
    if promised and eta_at:
        on_time = eta_at <= promised
    return EtaOut(
        promised_delivery_at=promised,
        current_eta_at=eta_at,
        remaining_minutes=remaining,
        delay_minutes=delay,
        on_time=on_time,
    )


def tracking_extras(parcel: Parcel) -> dict:
    leg = active_leg(parcel)
    events = sorted(parcel.journey_events or [], key=lambda e: e.created_at)
    return {
        "journey_events": [JourneyEventOut.model_validate(e) for e in events],
        "flight": FlightLegOut.model_validate(leg) if leg else None,
        "eta": eta_view(parcel, leg),
        "allowed_next": sorted(allowed_next(parcel.status), key=lambda s: s.value),
    }
