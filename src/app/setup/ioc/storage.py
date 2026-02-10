"""
Storage providers for file storage operations (QR codes, assets, etc.).

Provides local and CDN storage adapters based on configuration.
"""

from pathlib import Path

from dishka import Provider, Scope, provide

from app.domain.ports.storage.file_storage import FileStoragePort
from app.infrastructure.qr.qr_generator import QRCodeGenerator
from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.storage.recallium_storage import RecalliumStorageAdapter
from app.setup.config.storage import StorageSettings


class StorageProvider(Provider):
    """Provider for storage-related dependencies."""

    scope = Scope.REQUEST

    @provide
    def provide_qr_generator(self) -> QRCodeGenerator:
        """Provide QR code generator service."""
        return QRCodeGenerator()

    @provide
    def provide_local_storage(
        self, settings: StorageSettings
    ) -> LocalStorageAdapter:
        """Provide local file storage adapter."""
        return LocalStorageAdapter(
            base_path=Path(settings.qr_local_path),
            base_url=settings.qr_local_base_url,
        )

    @provide
    def provide_cdn_storage(
        self, settings: StorageSettings
    ) -> RecalliumStorageAdapter | None:
        """
        Provide CDN (DigitalOcean Spaces) storage adapter.

        Returns None if CDN is not enabled or configured.
        """
        if not settings.is_cdn_enabled:
            return None

        return RecalliumStorageAdapter(
            access_key=settings.do_access_key,
            secret_key=settings.do_secret_key,
            region=settings.do_region,
            bucket=settings.do_bucket,
            cdn_enabled=settings.do_cdn_enabled,
        )

    @provide
    def provide_file_storage(
        self,
        settings: StorageSettings,
        local_storage: LocalStorageAdapter,
        cdn_storage: RecalliumStorageAdapter | None,
    ) -> FileStoragePort:
        """
        Provide the active file storage adapter based on configuration.

        Uses CDN if enabled, otherwise falls back to local storage.
        """
        if settings.is_cdn_enabled and cdn_storage is not None:
            return cdn_storage
        return local_storage
