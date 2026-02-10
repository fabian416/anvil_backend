"""Storage configuration for QR codes and assets.

Supports local filesystem and Recallium CDN (DigitalOcean Spaces).
"""

from pydantic import BaseModel, Field


class DigitalOceanSettings(BaseModel):
    """DigitalOcean Spaces (Recallium CDN) configuration."""

    enabled: bool = False
    access_key: str = ""
    secret_key: str = ""
    region: str = "nyc3"
    bucket: str = "anvil-assets"
    cdn_enabled: bool = True


class StorageSettings(BaseModel):
    """Storage configuration for QR codes and assets.

    Attributes:
        qr_storage_enabled: Enable QR code pre-generation
        qr_storage_type: Default storage type (local or cdn)
        qr_local_path: Path for local file storage
        qr_local_base_url: Base URL for serving local files

        digitalocean: DigitalOcean Spaces (Recallium) settings
    """

    # QR Storage
    qr_storage_enabled: bool = Field(default=True)
    qr_storage_type: str = Field(default="local")  # local | cdn
    qr_local_path: str = Field(default="./static/qr")
    qr_local_base_url: str = Field(default="/static/qr")

    # DigitalOcean Spaces (Recallium CDN)
    digitalocean: DigitalOceanSettings = Field(default_factory=DigitalOceanSettings)

    @property
    def is_cdn_enabled(self) -> bool:
        """Check if CDN storage is configured and enabled."""
        return (
            self.digitalocean.enabled
            and bool(self.digitalocean.access_key)
            and bool(self.digitalocean.secret_key)
        )

    @property
    def do_enabled(self) -> bool:
        """Alias for CDN enabled check."""
        return self.digitalocean.enabled

    @property
    def do_access_key(self) -> str:
        """Alias for DO access key."""
        return self.digitalocean.access_key

    @property
    def do_secret_key(self) -> str:
        """Alias for DO secret key."""
        return self.digitalocean.secret_key

    @property
    def do_region(self) -> str:
        """Alias for DO region."""
        return self.digitalocean.region

    @property
    def do_bucket(self) -> str:
        """Alias for DO bucket."""
        return self.digitalocean.bucket

    @property
    def do_cdn_enabled(self) -> bool:
        """Alias for DO CDN enabled."""
        return self.digitalocean.cdn_enabled

    @property
    def effective_storage_type(self) -> str:
        """Get effective storage type based on configuration.

        Returns 'cdn' only if CDN is fully configured, otherwise 'local'.
        """
        if self.qr_storage_type == "cdn" and self.is_cdn_enabled:
            return "cdn"
        return "local"
