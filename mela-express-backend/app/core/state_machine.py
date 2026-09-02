from app.models import ParcelStatus


class InvalidTransition(Exception):
    def __init__(self, current: ParcelStatus, next_status: ParcelStatus):
        self.current = current
        self.next_status = next_status
        super().__init__(f"Invalid status transition from {current} to {next_status}")


# Rank is used for skip-forward (operators may miss an intermediate scan).
# `in_transit` is the legacy ground-path alias between leaving the origin
# branch and arriving at the destination hub / airport.
_RANK: dict[ParcelStatus, int] = {
    ParcelStatus.CREATED: 0,
    ParcelStatus.RECEIVED_AT_ORIGIN: 10,
    ParcelStatus.PROCESSED_AT_ORIGIN: 20,
    ParcelStatus.DISPATCHED_FROM_ORIGIN: 30,
    ParcelStatus.IN_TRANSIT: 35,
    ParcelStatus.ARRIVED_ORIGIN_AIRPORT: 40,
    ParcelStatus.CHECKED_IN_FLIGHT: 50,
    ParcelStatus.DEPARTED: 60,
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT: 70,
    ParcelStatus.RELEASED_FROM_AIRPORT: 80,
    ParcelStatus.ARRIVED_AT_DESTINATION: 90,
    ParcelStatus.DISTRIBUTED_TO_BRANCH: 100,
    ParcelStatus.READY_FOR_PICKUP: 110,
    ParcelStatus.DELIVERED: 120,
    ParcelStatus.ON_HOLD: -1,
    ParcelStatus.LOST: -2,
    ParcelStatus.RETURNED: 200,
    ParcelStatus.CANCELLED: 200,
}

LINEHAUL_STATUSES = {
    ParcelStatus.PROCESSED_AT_ORIGIN,
    ParcelStatus.DISPATCHED_FROM_ORIGIN,
    ParcelStatus.IN_TRANSIT,
    ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
    ParcelStatus.CHECKED_IN_FLIGHT,
    ParcelStatus.DEPARTED,
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
    ParcelStatus.RELEASED_FROM_AIRPORT,
}

EXCEPTION_STATUSES = {
    ParcelStatus.ON_HOLD,
    ParcelStatus.LOST,
    ParcelStatus.RETURNED,
    ParcelStatus.CANCELLED,
}

TERMINAL_STATUSES = {
    ParcelStatus.DELIVERED,
    ParcelStatus.RETURNED,
    ParcelStatus.CANCELLED,
}

# Prepaid parcels must be paid before they leave the origin counter.
_PAYMENT_GATE_RANK = _RANK[ParcelStatus.DISPATCHED_FROM_ORIGIN]


def is_linehaul_status(status: ParcelStatus) -> bool:
    return status in LINEHAUL_STATUSES


def payment_gated(status: ParcelStatus) -> bool:
    rank = _RANK.get(status, 0)
    return rank >= _PAYMENT_GATE_RANK and status not in EXCEPTION_STATUSES


def validate_transition(current: ParcelStatus, next_status: ParcelStatus) -> bool:
    if next_status == current:
        raise InvalidTransition(current, next_status)

    if current in TERMINAL_STATUSES:
        raise InvalidTransition(current, next_status)

    if next_status in EXCEPTION_STATUSES:
        if current == ParcelStatus.DELIVERED:
            raise InvalidTransition(current, next_status)
        return True

    if current == ParcelStatus.LOST:
        if next_status == ParcelStatus.ON_HOLD:
            return True
        raise InvalidTransition(current, next_status)

    if current == ParcelStatus.ON_HOLD:
        if next_status == ParcelStatus.CREATED:
            raise InvalidTransition(current, next_status)
        return True

    current_rank = _RANK.get(current)
    next_rank = _RANK.get(next_status)
    if current_rank is None or next_rank is None:
        raise InvalidTransition(current, next_status)
    if next_rank > current_rank and next_status not in EXCEPTION_STATUSES:
        return True
    raise InvalidTransition(current, next_status)


def allowed_next(current: ParcelStatus) -> set[ParcelStatus]:
    nxt: set[ParcelStatus] = set()
    for status in ParcelStatus:
        try:
            validate_transition(current, status)
            nxt.add(status)
        except InvalidTransition:
            continue
    return nxt
