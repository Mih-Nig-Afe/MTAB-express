"""Domain-split schema package. Re-exports every name so existing imports
(`from app.schemas import ParcelOut`) keep working unchanged."""
from app.schemas.common import StatusHistoryOut, ManifestCheckpointOut  # noqa: F401
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest  # noqa: F401
from app.schemas.staff import StaffCreate, StaffUpdate, StaffOut  # noqa: F401
from app.schemas.branches import BranchCreate, BranchUpdate, BranchOut  # noqa: F401
from app.schemas.customers import CustomerLink, CustomerOut, CustomerLanguageUpdate  # noqa: F401
from app.schemas.parcels import (  # noqa: F401
    ParcelCreate,
    ParcelStatusUpdate,
    ClassificationPreview,
    ClassificationPreviewOut,
    ParcelScanRequest,
    ParcelScanOut,
    ProofOfDeliveryUpload,
    OTPGenerateOut,
    VerifyPickupRequest,
    ParcelOut,
    ParcelDetailOut,
    ParcelTrackOut,
    FlightLegAttach,
    JourneyEventOut,
    FlightLegOut,
    EtaOut,
)
from app.schemas.manifests import (  # noqa: F401
    ManifestCreate,
    ManifestOut,
    ManifestReceive,
    ManifestCheckpointCreate,
    ManifestDetailOut,
)
from app.schemas.payments import CashCollectRequest, ChapaInitRequest, ChapaWebhookPayload  # noqa: F401
from app.schemas.reports import ReportFilter  # noqa: F401
