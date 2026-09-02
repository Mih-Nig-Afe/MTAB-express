"""Map a barcode scan at a station → the next UPS-style journey status."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.state_machine import allowed_next
from app.models import Branch, FacilityType, Parcel, ParcelStatus, StaffRole


class ScanError(str, Enum):
    NOT_FOUND = "not_found"
    WRONG_STATION = "wrong_station"
    PAYMENT_REQUIRED = "payment_required"
    TERMINAL = "terminal"
    NO_TRANSITION = "no_transition"


@dataclass(frozen=True)
class ScanResolution:
    to_status: ParcelStatus
    station_label: str
    note: str


@dataclass(frozen=True)
class ScanFailure:
    error: ScanError
    message: str
    current_status: ParcelStatus | None = None


# Ordered candidates per scan context (first match in allowed_next wins).
_ORIGIN_BRANCH = (
    ParcelStatus.RECEIVED_AT_ORIGIN,
    ParcelStatus.PROCESSED_AT_ORIGIN,
    ParcelStatus.DISPATCHED_FROM_ORIGIN,
)
_ORIGIN_AIRPORT = (
    ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
    ParcelStatus.CHECKED_IN_FLIGHT,
    ParcelStatus.DEPARTED,
)
_DEST_AIRPORT = (
    ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
    ParcelStatus.RELEASED_FROM_AIRPORT,
)
_DEST_BRANCH = (
    ParcelStatus.ARRIVED_AT_DESTINATION,
    ParcelStatus.DISTRIBUTED_TO_BRANCH,
    ParcelStatus.READY_FOR_PICKUP,
    ParcelStatus.DELIVERED,
)
_HUB = (
    ParcelStatus.IN_TRANSIT,
    ParcelStatus.ARRIVED_AT_DESTINATION,
    ParcelStatus.DISTRIBUTED_TO_BRANCH,
)


def _pick(candidates: tuple[ParcelStatus, ...], allowed: set[ParcelStatus]) -> ParcelStatus | None:
    for status in candidates:
        if status in allowed:
            return status
    return None


def _branch_context(parcel: Parcel, branch: Branch) -> tuple[tuple[ParcelStatus, ...], str]:
    if branch.facility_type == FacilityType.AIRPORT:
        # Origin-side airport until departed; then destination-side airport.
        if parcel.status in {
            ParcelStatus.CREATED,
            ParcelStatus.RECEIVED_AT_ORIGIN,
            ParcelStatus.PROCESSED_AT_ORIGIN,
            ParcelStatus.DISPATCHED_FROM_ORIGIN,
            ParcelStatus.IN_TRANSIT,
            ParcelStatus.ARRIVED_ORIGIN_AIRPORT,
            ParcelStatus.CHECKED_IN_FLIGHT,
        } or branch.id == parcel.origin_branch_id:
            if parcel.status not in {
                ParcelStatus.DEPARTED,
                ParcelStatus.ARRIVED_DESTINATION_AIRPORT,
                ParcelStatus.RELEASED_FROM_AIRPORT,
            }:
                return _ORIGIN_AIRPORT, branch.name
        return _DEST_AIRPORT, branch.name

    if branch.id == parcel.origin_branch_id:
        return _ORIGIN_BRANCH, branch.name

    if branch.id == parcel.destination_branch_id:
        return _DEST_BRANCH, branch.name

    if branch.facility_type == FacilityType.SORTING_HUB:
        return _HUB, branch.name

    return _HUB, branch.name


def resolve_scan(
    parcel: Parcel,
    branch: Branch | None,
    *,
    role: StaffRole | None = None,
) -> ScanResolution | ScanFailure:
    if parcel.status in {ParcelStatus.DELIVERED, ParcelStatus.CANCELLED, ParcelStatus.RETURNED}:
        return ScanFailure(
            ScanError.TERMINAL,
            f"Parcel is already {parcel.status.value}.",
            parcel.status,
        )

    if branch is None:
        return ScanFailure(ScanError.WRONG_STATION, "Your account is not assigned to a scan station.")

    allowed = allowed_next(parcel.status)
    if not allowed:
        return ScanFailure(
            ScanError.NO_TRANSITION,
            "No further scans apply to this parcel.",
            parcel.status,
        )

    candidates, station = _branch_context(parcel, branch)
    nxt = _pick(candidates, allowed)
    if nxt is None:
        return ScanFailure(
            ScanError.WRONG_STATION,
            f"This parcel ({parcel.status.value}) cannot be scanned at {station}. "
            "Take it to the next designated checkpoint.",
            parcel.status,
        )

    labels = {
        ParcelStatus.RECEIVED_AT_ORIGIN: "Received at origin counter",
        ParcelStatus.PROCESSED_AT_ORIGIN: "Processed / weighed at origin",
        ParcelStatus.DISPATCHED_FROM_ORIGIN: "Dispatched from origin branch",
        ParcelStatus.ARRIVED_ORIGIN_AIRPORT: "Received at origin airport",
        ParcelStatus.CHECKED_IN_FLIGHT: "Checked in for flight",
        ParcelStatus.DEPARTED: "Departed — in flight",
        ParcelStatus.ARRIVED_DESTINATION_AIRPORT: "Landed at destination airport",
        ParcelStatus.RELEASED_FROM_AIRPORT: "Released from airport customs",
        ParcelStatus.ARRIVED_AT_DESTINATION: "Arrived at destination hub",
        ParcelStatus.DISTRIBUTED_TO_BRANCH: "Out for delivery to pickup branch",
        ParcelStatus.READY_FOR_PICKUP: "Ready for customer pickup",
        ParcelStatus.DELIVERED: "Delivered to receiver",
        ParcelStatus.IN_TRANSIT: "In transit between hubs",
    }
    return ScanResolution(
        to_status=nxt,
        station_label=station,
        note=f"Scan at {station}: {labels.get(nxt, nxt.value)}",
    )


def normalize_scan_code(raw: str) -> str:
    """Extract tracking code from raw barcode/QR payload."""
    text = (raw or "").strip().upper()
    if not text:
        return ""
    # QR may encode a URL …/track/MEX-HW-000001
    if "/TRACK/" in text:
        text = text.split("/TRACK/")[-1].split("?")[0].split("#")[0]
    # Some scanners prefix with ]C1 etc.
    for prefix in ("]C1", "]E0", "MELA:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.strip("- ").split()[0][:30]
