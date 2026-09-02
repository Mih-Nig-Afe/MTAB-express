"""Domain-split model package. Re-exports every name so existing imports
(`from app.models import Parcel`) keep working unchanged."""
from app.models.base import gen_uuid  # noqa: F401
from app.models.branches import Branch, FacilityType  # noqa: F401
from app.models.staff import StaffRole, StaffUser  # noqa: F401
from app.models.customers import Customer  # noqa: F401
from app.models.parcels import (  # noqa: F401
    ParcelStatus,
    PaymentMode,
    PaymentMethod,
    PaymentStatus,
    SizeCategory,
    ContentCategory,
    Parcel,
    ParcelStatusHistory,
    ParcelProofOfDelivery,
)
from app.models.journey import (  # noqa: F401
    ParcelJourneyEvent,
    ParcelFlightLeg,
    PickupReminderLog,
)
from app.models.payments import Payment  # noqa: F401
from app.models.manifests import (  # noqa: F401
    ManifestStatus,
    TransferManifest,
    ManifestParcel,
    ManifestCheckpoint,
)
from app.models.notifications import NotificationLog  # noqa: F401

__all__ = [
    "gen_uuid",
    "Branch", "FacilityType",
    "StaffRole", "StaffUser",
    "Customer",
    "ParcelStatus", "PaymentMode", "PaymentMethod", "PaymentStatus",
    "SizeCategory", "ContentCategory",
    "Parcel", "ParcelStatusHistory", "ParcelProofOfDelivery",
    "ParcelJourneyEvent", "ParcelFlightLeg", "PickupReminderLog",
    "Payment",
    "ManifestStatus", "TransferManifest", "ManifestParcel", "ManifestCheckpoint",
    "NotificationLog",
]
