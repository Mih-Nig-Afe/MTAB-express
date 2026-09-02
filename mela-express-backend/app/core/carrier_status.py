"""UPS/DHL-style customer-facing status labels (IATA RP1745 / GS1 aligned)."""
from __future__ import annotations

from app.models import ParcelStatus

# Internal status → carrier scan event code + English label shown to customers.
CARRIER_STATUS: dict[ParcelStatus, dict[str, str]] = {
    ParcelStatus.CREATED: {"code": "OC", "label": "Order Created"},
    ParcelStatus.RECEIVED_AT_ORIGIN: {"code": "OR", "label": "Origin Scan — Received"},
    ParcelStatus.PROCESSED_AT_ORIGIN: {"code": "OP", "label": "Origin Scan — Processed"},
    ParcelStatus.DISPATCHED_FROM_ORIGIN: {"code": "DP", "label": "Departed Origin Facility"},
    ParcelStatus.IN_TRANSIT: {"code": "IT", "label": "In Transit"},
    ParcelStatus.ARRIVED_ORIGIN_AIRPORT: {"code": "AR", "label": "Arrived at Origin Airport"},
    ParcelStatus.CHECKED_IN_FLIGHT: {"code": "CI", "label": "Checked In for Flight"},
    ParcelStatus.DEPARTED: {"code": "AF", "label": "Departed — In Flight"},
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT: {"code": "AD", "label": "Arrived at Destination Airport"},
    ParcelStatus.RELEASED_FROM_AIRPORT: {"code": "RL", "label": "Released from Customs"},
    ParcelStatus.ARRIVED_AT_DESTINATION: {"code": "DS", "label": "Arrived at Destination Facility"},
    ParcelStatus.DISTRIBUTED_TO_BRANCH: {"code": "OD", "label": "Out for Delivery to Branch"},
    ParcelStatus.READY_FOR_PICKUP: {"code": "PU", "label": "Ready for Pickup"},
    ParcelStatus.DELIVERED: {"code": "DL", "label": "Delivered"},
    ParcelStatus.RETURNED: {"code": "RT", "label": "Returned to Sender"},
    ParcelStatus.CANCELLED: {"code": "CA", "label": "Cancelled"},
    ParcelStatus.LOST: {"code": "LS", "label": "Exception — Lost"},
    ParcelStatus.ON_HOLD: {"code": "EX", "label": "Exception — On Hold"},
}


def carrier_label(status: ParcelStatus | str) -> str:
    if isinstance(status, str):
        try:
            status = ParcelStatus(status)
        except ValueError:
            return status.replace("_", " ").title()
    return CARRIER_STATUS.get(status, {}).get("label", status.value.replace("_", " ").title())


def carrier_code(status: ParcelStatus | str) -> str:
    if isinstance(status, str):
        try:
            status = ParcelStatus(status)
        except ValueError:
            return "UN"
    return CARRIER_STATUS.get(status, {}).get("code", "UN")
