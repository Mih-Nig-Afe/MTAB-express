"""Journey lifecycle, ETA, pickup reminders, and dual-notify targeting."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.eta import (
    HandlingBuffers,
    airport_for_city,
    haversine_km,
    live_remaining_minutes,
    promised_delivery_at,
    remaining_minutes,
)
from app.core.pickup_reminders import (
    PICKUP_REMINDER_DAYS,
    reminder_day_number,
    reminder_due,
)
from app.core.state_machine import (
    InvalidTransition,
    allowed_next,
    is_linehaul_status,
    payment_gated,
    validate_transition,
)
from app.models import ParcelStatus
from app.services.flight_tracking import (
    normalize_callsigns,
    parse_aviationstack_flight,
    parse_opensky_states,
)
from app.services.notifications import resolve_notify_targets


# ---------------------------------------------------------------------------
# State machine — air-cargo path + legacy ground path
# ---------------------------------------------------------------------------

AIR_PATH = [
    ParcelStatus.CREATED,
    ParcelStatus.RECEIVED_AT_ORIGIN,
    ParcelStatus.PROCESSED_AT_ORIGIN,
    ParcelStatus.DISPATCHED_FROM_ORIGIN,
    ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
    ParcelStatus.CHECKED_IN_FLIGHT,
    ParcelStatus.DEPARTED,
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
    ParcelStatus.RELEASED_FROM_AIRPORT,
    ParcelStatus.ARRIVED_AT_DESTINATION,
    ParcelStatus.DISTRIBUTED_TO_BRANCH,
    ParcelStatus.READY_FOR_PICKUP,
    ParcelStatus.DELIVERED,
]


def test_full_air_cargo_path_is_valid():
    for current, nxt in zip(AIR_PATH, AIR_PATH[1:]):
        assert validate_transition(current, nxt) is True


def test_legacy_ground_path_still_valid():
    validate_transition(ParcelStatus.CREATED, ParcelStatus.RECEIVED_AT_ORIGIN)
    validate_transition(ParcelStatus.RECEIVED_AT_ORIGIN, ParcelStatus.IN_TRANSIT)
    validate_transition(ParcelStatus.IN_TRANSIT, ParcelStatus.ARRIVED_AT_DESTINATION)
    validate_transition(ParcelStatus.ARRIVED_AT_DESTINATION, ParcelStatus.READY_FOR_PICKUP)


def test_can_skip_optional_origin_processing():
    validate_transition(ParcelStatus.RECEIVED_AT_ORIGIN, ParcelStatus.DISPATCHED_FROM_ORIGIN)
    validate_transition(ParcelStatus.RECEIVED_AT_ORIGIN, ParcelStatus.ARRIVED_ORIGIN_AIRPORT)


def test_cannot_move_backwards():
    with pytest.raises(InvalidTransition):
        validate_transition(ParcelStatus.DEPARTED, ParcelStatus.CHECKED_IN_FLIGHT)
    with pytest.raises(InvalidTransition):
        validate_transition(ParcelStatus.READY_FOR_PICKUP, ParcelStatus.RECEIVED_AT_ORIGIN)


def test_hold_and_lost_from_active_leg():
    validate_transition(ParcelStatus.DEPARTED, ParcelStatus.ON_HOLD)
    validate_transition(ParcelStatus.DEPARTED, ParcelStatus.LOST)
    validate_transition(ParcelStatus.ON_HOLD, ParcelStatus.DEPARTED)


def test_delivered_is_terminal():
    with pytest.raises(InvalidTransition):
        validate_transition(ParcelStatus.DELIVERED, ParcelStatus.READY_FOR_PICKUP)
    assert allowed_next(ParcelStatus.DELIVERED) == set()


def test_linehaul_includes_air_milestones():
    assert is_linehaul_status(ParcelStatus.IN_TRANSIT)
    assert is_linehaul_status(ParcelStatus.DEPARTED)
    assert is_linehaul_status(ParcelStatus.CHECKED_IN_FLIGHT)
    assert not is_linehaul_status(ParcelStatus.READY_FOR_PICKUP)
    assert not is_linehaul_status(ParcelStatus.CREATED)


def test_prepaid_is_gated_once_parcel_leaves_origin_counter():
    assert payment_gated(ParcelStatus.DISPATCHED_FROM_ORIGIN)
    assert payment_gated(ParcelStatus.IN_TRANSIT)
    assert payment_gated(ParcelStatus.DEPARTED)
    assert not payment_gated(ParcelStatus.RECEIVED_AT_ORIGIN)
    assert not payment_gated(ParcelStatus.CREATED)


# ---------------------------------------------------------------------------
# ETA
# ---------------------------------------------------------------------------

def test_promised_delivery_uses_flight_plus_handling():
    created = datetime(2026, 9, 2, 6, 0, tzinfo=timezone.utc)
    promised = promised_delivery_at(
        created_at=created,
        origin_iata="ADD",
        dest_iata="DIR",
        buffers=HandlingBuffers(
            origin_processing_min=30,
            origin_to_airport_min=30,
            origin_airport_handling_min=30,
            dest_airport_handling_min=30,
            dest_airport_to_branch_min=30,
            dest_processing_min=30,
        ),
    )
    # ADD-DIR typical block ~70 min + 180 min handling = ~250 min
    delta = (promised - created).total_seconds() / 60
    assert 200 <= delta <= 400


def test_remaining_minutes_shrinks_as_journey_advances():
    created = datetime(2026, 9, 2, 6, 0, tzinfo=timezone.utc)
    now = created + timedelta(hours=1)
    origin_left = remaining_minutes(
        status=ParcelStatus.RECEIVED_AT_ORIGIN.value,
        now=now,
        origin_iata="ADD",
        dest_iata="BJR",
        created_at=created,
    )
    airborne = remaining_minutes(
        status=ParcelStatus.DEPARTED.value,
        now=now,
        origin_iata="ADD",
        dest_iata="BJR",
        created_at=created,
        scheduled_arrival=now + timedelta(minutes=40),
    )
    ready = remaining_minutes(
        status=ParcelStatus.READY_FOR_PICKUP.value,
        now=now,
        origin_iata="ADD",
        dest_iata="BJR",
        created_at=created,
    )
    delivered = remaining_minutes(
        status=ParcelStatus.DELIVERED.value,
        now=now,
        origin_iata="ADD",
        dest_iata="BJR",
        created_at=created,
    )
    assert origin_left > airborne > ready
    assert delivered == 0


def test_live_remaining_from_adsb_position():
    # Roughly Addis → Dire Dawa (~450 km). At 700 km/h that's ~40 min.
    minutes = live_remaining_minutes(
        lat=8.98,
        lon=38.80,
        dest_lat=9.62,
        dest_lon=41.85,
        ground_speed_ms=194.0,  # ~700 km/h
    )
    assert 20 <= minutes <= 80


def test_haversine_addis_dire_dawa_is_plausible():
    km = haversine_km(8.9779, 38.7993, 9.6247, 41.8542)
    assert 300 < km < 550


def test_airport_inferred_from_ethiopian_city():
    assert airport_for_city("Addis Ababa") == "ADD"
    assert airport_for_city("Bahir Dar") == "BJR"
    assert airport_for_city("unknown village") is None


# ---------------------------------------------------------------------------
# Pickup reminders
# ---------------------------------------------------------------------------

def test_first_ready_notice_counts_as_day_one():
    ready_at = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
    assert reminder_day_number(ready_at, ready_at) == 1
    assert reminder_due(ready_at=ready_at, last_sent_at=None, now=ready_at) is True


def test_daily_cadence_for_seven_days_then_stops():
    ready_at = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)
    last = ready_at
    sent = 1
    for day in range(2, PICKUP_REMINDER_DAYS + 1):
        now = ready_at + timedelta(days=day - 1, hours=1)
        assert reminder_due(ready_at=ready_at, last_sent_at=last, now=now, already_sent=sent)
        assert reminder_day_number(ready_at, now) == day
        last = now
        sent += 1
    after_week = ready_at + timedelta(days=8)
    assert reminder_due(
        ready_at=ready_at, last_sent_at=last, now=after_week, already_sent=sent
    ) is False


def test_no_reminder_after_pickup():
    ready_at = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)
    now = ready_at + timedelta(days=2)
    assert reminder_due(
        ready_at=ready_at, last_sent_at=ready_at, now=now, picked_up=True
    ) is False


def test_does_not_spam_same_day():
    ready_at = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)
    now = ready_at + timedelta(hours=3)
    assert reminder_due(ready_at=ready_at, last_sent_at=ready_at, now=now, already_sent=1) is False


# ---------------------------------------------------------------------------
# Dual notify + flight parsers
# ---------------------------------------------------------------------------

class _C:
    def __init__(self, id, phone=None, telegram_id=None):
        self.id = id
        self.phone = phone
        self.telegram_id = telegram_id


def test_notify_targets_include_sender_and_receiver():
    sender = _C("s1", phone="+251911000001", telegram_id="111")
    receiver = _C("r1", phone="+251911000002", telegram_id="222")
    targets = resolve_notify_targets(
        sender=sender,
        receiver=receiver,
        receiver_phone="+251911000002",
    )
    roles = {t.role for t in targets}
    assert roles == {"sender", "receiver"}
    channels = {(t.role, t.channel) for t in targets}
    assert ("sender", "telegram") in channels
    assert ("receiver", "telegram") in channels


def test_notify_falls_back_to_sms_when_no_telegram():
    sender = _C("s1", phone="+251911000001", telegram_id=None)
    targets = resolve_notify_targets(
        sender=sender,
        receiver=None,
        receiver_phone="+251922000009",
    )
    by_role = {t.role: t for t in targets}
    assert by_role["sender"].channel == "sms"
    assert by_role["receiver"].channel == "sms"
    assert by_role["receiver"].address == "+251922000009"


def test_callsign_aliases_cover_ethiopian_airlines():
    aliases = normalize_callsigns("ET123")
    assert "ET123" in aliases
    assert "ETH123" in aliases


def test_parse_aviationstack_active_flight():
    payload = {
        "data": [
            {
                "flight_status": "active",
                "flight": {"iata": "ET123", "icao": "ETH123", "number": "123"},
                "airline": {"iata": "ET", "name": "Ethiopian Airlines"},
                "departure": {
                    "iata": "ADD",
                    "scheduled": "2026-09-02T08:00:00+00:00",
                    "actual": "2026-09-02T08:22:00+00:00",
                    "delay": 22,
                },
                "arrival": {
                    "iata": "DIR",
                    "scheduled": "2026-09-02T09:10:00+00:00",
                    "estimated": "2026-09-02T09:32:00+00:00",
                    "delay": 22,
                },
                "live": {
                    "latitude": 9.1,
                    "longitude": 40.2,
                    "altitude": 9800,
                    "speed_horizontal": 720,
                    "direction": 75,
                    "is_ground": False,
                },
            }
        ]
    }
    snap = parse_aviationstack_flight(payload)
    assert snap is not None
    assert snap.flight_iata == "ET123"
    assert snap.status == "active"
    assert snap.delay_minutes == 22
    assert snap.origin_iata == "ADD"
    assert snap.dest_iata == "DIR"
    assert snap.latitude == 9.1


def test_parse_opensky_matches_callsign():
    payload = {
        "states": [
            [
                "040123",
                "ETH123  ",
                "Ethiopia",
                1690000000,
                1690000001,
                39.5,
                9.2,
                10000.0,
                False,
                200.0,
                80.0,
                0.0,
                None,
                10200.0,
                "1273",
                False,
                0,
            ]
        ]
    }
    pos = parse_opensky_states(payload, callsigns={"ETH123", "ET123"})
    assert pos is not None
    assert pos.callsign == "ETH123"
    assert pos.longitude == 39.5
    assert pos.on_ground is False
    assert pos.velocity_ms == 200.0


def test_parse_opensky_returns_none_when_callsign_absent():
    payload = {"states": [["abc", "KLM900  ", "Netherlands", 0, 0, 4.0, 52.0, 0, True, 0, 0, 0, None, 0, None, False, 0]]}
    assert parse_opensky_states(payload, callsigns={"ETH123"}) is None
