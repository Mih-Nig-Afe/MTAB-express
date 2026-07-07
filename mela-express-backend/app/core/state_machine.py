from app.models import ParcelStatus

class InvalidTransition(Exception):
    def __init__(self, current: ParcelStatus, next_status: ParcelStatus):
        self.current = current
        self.next_status = next_status
        super().__init__(f"Invalid status transition from {current} to {next_status}")

ALLOWED_TRANSITIONS = {
    ParcelStatus.CREATED: {ParcelStatus.RECEIVED_AT_ORIGIN, ParcelStatus.CANCELLED},
    ParcelStatus.RECEIVED_AT_ORIGIN: {ParcelStatus.IN_TRANSIT, ParcelStatus.ON_HOLD, ParcelStatus.CANCELLED},
    ParcelStatus.IN_TRANSIT: {ParcelStatus.ARRIVED_AT_DESTINATION, ParcelStatus.ON_HOLD, ParcelStatus.LOST},
    ParcelStatus.ARRIVED_AT_DESTINATION: {ParcelStatus.READY_FOR_PICKUP, ParcelStatus.ON_HOLD},
    ParcelStatus.READY_FOR_PICKUP: {ParcelStatus.DELIVERED, ParcelStatus.RETURNED, ParcelStatus.ON_HOLD},
    ParcelStatus.ON_HOLD: {ParcelStatus.IN_TRANSIT, ParcelStatus.RECEIVED_AT_ORIGIN, ParcelStatus.RETURNED, ParcelStatus.CANCELLED},
    ParcelStatus.DELIVERED: set(),
    ParcelStatus.RETURNED: set(),
    ParcelStatus.CANCELLED: set(),
    ParcelStatus.LOST: {ParcelStatus.ON_HOLD},
}

def validate_transition(current: ParcelStatus, next_status: ParcelStatus) -> bool:
    if next_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransition(current, next_status)
    return True
