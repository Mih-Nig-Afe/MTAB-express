"""Tests for UPS-style classification and scan routing."""
from app.core.classification import classify_parcel, classify_size, volumetric_weight_kg
from app.core.scan_workflow import normalize_scan_code, resolve_scan, ScanFailure, ScanError
from app.models import Branch, FacilityType, Parcel, ParcelStatus, StaffRole, SizeCategory, ContentCategory
import uuid


def _branch(*, facility: FacilityType = FacilityType.BRANCH, branch_id=None) -> Branch:
    return Branch(
        id=branch_id or uuid.uuid4(),
        name="Test",
        code="TST",
        city="Addis Ababa",
        facility_type=facility,
    )


def _parcel(*, status: ParcelStatus, origin_id=None, dest_id=None) -> Parcel:
    oid = origin_id or uuid.uuid4()
    did = dest_id or uuid.uuid4()
    return Parcel(
        id=uuid.uuid4(),
        tracking_code="MEX-TST-000001",
        origin_branch_id=oid,
        destination_branch_id=did,
        sender_id=uuid.uuid4(),
        receiver_name="Receiver",
        receiver_phone="0911000000",
        price=150,
        payment_mode="before",
        status=status,
        created_by=uuid.uuid4(),
    )


def test_volumetric_weight():
    assert volumetric_weight_kg(50, 40, 30) == 12.0


def test_classify_size_small():
    assert classify_size(30, 20, 15) == SizeCategory.SMALL


def test_classify_size_medium():
    assert classify_size(40, 30, 20) == SizeCategory.MEDIUM


def test_classify_size_oversized():
    assert classify_size(120, 80, 60) == SizeCategory.OVERSIZED


def test_classify_parcel_suggested_price():
    result = classify_parcel(
        weight_kg=2,
        length_cm=30,
        width_cm=20,
        height_cm=15,
        content_category=ContentCategory.GENERAL,
    )
    assert result.size_category == SizeCategory.SMALL
    assert result.chargeable_weight_kg >= 2
    assert result.suggested_price > 0


def test_normalize_scan_code_from_url():
    assert normalize_scan_code("https://app.example.com/track/MEX-HW-000042") == "MEX-HW-000042"


def test_normalize_scan_code_raw():
    assert normalize_scan_code("mex-hw-000001") == "MEX-HW-000001"


def test_scan_origin_branch_received_to_processed():
    oid = uuid.uuid4()
    parcel = _parcel(status=ParcelStatus.RECEIVED_AT_ORIGIN, origin_id=oid, dest_id=uuid.uuid4())
    branch = _branch(facility=FacilityType.BRANCH, branch_id=oid)
    res = resolve_scan(parcel, branch, role=StaffRole.OPERATOR)
    assert not isinstance(res, ScanFailure)
    assert res.to_status == ParcelStatus.PROCESSED_AT_ORIGIN


def test_scan_airport_arrival():
    parcel = _parcel(status=ParcelStatus.DISPATCHED_FROM_ORIGIN)
    branch = _branch(facility=FacilityType.AIRPORT)
    res = resolve_scan(parcel, branch, role=StaffRole.OPERATOR)
    assert res.to_status == ParcelStatus.ARRIVED_ORIGIN_AIRPORT


def test_scan_dest_branch_ready():
    did = uuid.uuid4()
    parcel = _parcel(status=ParcelStatus.DISTRIBUTED_TO_BRANCH, dest_id=did)
    branch = _branch(facility=FacilityType.BRANCH, branch_id=did)
    res = resolve_scan(parcel, branch, role=StaffRole.OPERATOR)
    assert res.to_status == ParcelStatus.READY_FOR_PICKUP


def test_scan_wrong_station():
    parcel = _parcel(status=ParcelStatus.READY_FOR_PICKUP)
    branch = _branch(facility=FacilityType.AIRPORT)
    res = resolve_scan(parcel, branch, role=StaffRole.OPERATOR)
    assert isinstance(res, ScanFailure)
    assert res.error == ScanError.WRONG_STATION


def test_scan_terminal_delivered():
    parcel = _parcel(status=ParcelStatus.DELIVERED)
    branch = _branch()
    res = resolve_scan(parcel, branch)
    assert isinstance(res, ScanFailure)
    assert res.error == ScanError.TERMINAL
