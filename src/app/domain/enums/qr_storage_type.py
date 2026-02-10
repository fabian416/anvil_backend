"""QR code storage type enumeration."""

from enum import Enum


class QRStorageType(str, Enum):
    """Storage type for wallet QR codes.

    Attributes:
        PENDING: QR not yet generated (new wallets or pending regeneration)
        LOCAL: Stored in local filesystem
        CDN: Stored in DigitalOcean Spaces CDN (Recallium)
    """

    PENDING = "pending"
    LOCAL = "local"
    CDN = "cdn"
