"""Storage configuration for QR codes and assets.

Supports local filesystem and Recallium CDN (DigitalOcean Spaces).
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    """Storage configuration for QR codes and assets.

    Attributes:
        qr_storage_enabled: Enable QR code pre-generation
        qr_storage_type: Default storage type (local or cdn)
        qr_local_path: Path for local file storage
        qr_local_base_url: Base URL for serving local files

        do_enabled: Enable DigitalOcean Spaces (Recallium)
        do_access_key: DO Spaces access key
        do_secret_key: DO Spaces secret key
        do_region: DO region (e.g., nyc3, sfo3)
        do_bucket: Bucket name
        do_cdn_enabled: Use CDN URLs
    """

    # QR Storage
    qr_storage_enabled: bool = Field(default=True)
    qr_storage_type: str = Field(default="local")  # local | cdn
    qr_local_path: str = Field(default="./static/qr")
    qr_local_base_url: str = Field(default="/static/qr")

    # DigitalOcean Spaces (Recallium)
    do_enabled: bool = Field(default=False, alias="STORAGE_DO_ENABLED")
    do_access_key: str = Field(default="", alias="STORAGE_DO_ACCESS_KEY")
    do_secret_key: str = Field(default="", alias="STORAGE_DO_SECRET_KEY")
    do_region: str = Field(default="nyc3", alias="STORAGE_DO_REGION")
    do_bucket: str = Field(default="anvil-assets", alias="STORAGE_DO_BUCKET")
    do_cdn_enabled: bool = Field(default=True, alias="STORAGE_DO_CDN_ENABLED")

    @property
    def is_cdn_enabled(self) -> bool:
        """Check if CDN storage is configured and enabled."""
        return (
            self.do_enabled
            and bool(self.do_access_key)
            and bool(self.do_secret_key)
        )

    @property
    def effective_storage_type(self) -> str:
        """Get effective storage type based on configuration.

        Returns 'cdn' only if CDN is fully configured, otherwise 'local'.
        """
        if self.qr_storage_type == "cdn" and self.is_cdn_enabled:
            return "cdn"
        return "local"

    class Config:
        env_prefix = "STORAGE_"
        case_sensitive = False
