"""Background task for generating and storing wallet QR codes.

This task runs periodically via Celery to:
1. Generate QR codes for wallets with pending/NULL qr_storage_type
2. Migrate local QR codes to CDN when CDN is enabled

Handles inconsistencies by processing both NULL and 'pending' states.
"""

import logging
from dataclasses import dataclass, field

from app.domain.enums.qr_storage_type import QRStorageType
from app.domain.ports.storage.file_storage import FileStoragePort
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.infrastructure.qr.qr_generator import QRCodeGenerator

logger = logging.getLogger(__name__)


@dataclass
class QRGenerationStats:
    """Statistics from QR generation task."""

    generated: int = 0
    migrated: int = 0
    errors: int = 0
    skipped: int = 0
    error_addresses: list[str] = field(default_factory=list)


class GenerateWalletQRTask:
    """Background task to generate and store wallet QR codes.

    Runs every 3 minutes, processes up to BATCH_SIZE wallets per run:
    1. Find wallets with qr_storage_type='pending' or NULL -> generate QR
    2. If CDN enabled, find qr_storage_type='local' -> migrate to CDN

    Attributes:
        BATCH_SIZE: Maximum wallets to process per run
        DEFAULT_CHAIN_ID: Default chain ID for QR codes (Base)
    """

    BATCH_SIZE = 30
    DEFAULT_CHAIN_ID = 8453  # Base

    def __init__(
        self,
        wallet_repository: WalletRepository,
        local_storage: FileStoragePort,
        cdn_storage: FileStoragePort | None,
        qr_generator: QRCodeGenerator,
        cdn_enabled: bool = False,
    ):
        """Initialize QR generation task.

        Args:
            wallet_repository: Repository for wallet persistence
            local_storage: Local filesystem storage adapter
            cdn_storage: CDN storage adapter (Recallium), optional
            qr_generator: QR code generator service
            cdn_enabled: Whether CDN storage is enabled and configured
        """
        self._wallet_repo = wallet_repository
        self._local_storage = local_storage
        self._cdn_storage = cdn_storage
        self._qr_generator = qr_generator
        self._cdn_enabled = cdn_enabled and cdn_storage is not None

    async def run(self) -> QRGenerationStats:
        """Execute QR generation task.

        Returns:
            Statistics about generated, migrated, and failed QR codes
        """
        stats = QRGenerationStats()

        # Phase 1: Generate QRs for pending wallets
        await self._generate_pending_qrs(stats)

        # Phase 2: Migrate local QRs to CDN (if enabled)
        if self._cdn_enabled:
            await self._migrate_to_cdn(stats)

        logger.info(
            f"QR generation complete: generated={stats.generated}, "
            f"migrated={stats.migrated}, errors={stats.errors}"
        )
        return stats

    async def _generate_pending_qrs(self, stats: QRGenerationStats) -> None:
        """Generate QR codes for wallets without QR.

        Processes wallets with qr_storage_type='pending' or NULL.
        """
        # Get wallets needing QR generation
        wallets = await self._wallet_repo.get_wallets_without_qr(
            limit=self.BATCH_SIZE
        )

        logger.info(f"Found {len(wallets)} wallets needing QR generation")

        for wallet in wallets:
            try:
                # Generate QR image
                qr_bytes = self._qr_generator.generate(
                    address=wallet.address,
                    chain_id=self.DEFAULT_CHAIN_ID,
                )

                # Determine storage target
                if self._cdn_enabled and self._cdn_storage:
                    storage = self._cdn_storage
                    storage_type = QRStorageType.CDN
                else:
                    storage = self._local_storage
                    storage_type = QRStorageType.LOCAL

                # Upload QR image
                path = self._qr_generator.get_storage_path(wallet.address)
                url = await storage.upload(qr_bytes, path)

                # Update wallet record
                await self._wallet_repo.update_qr_info(
                    wallet_id=wallet.id_,
                    qr_image_url=url,
                    qr_storage_type=storage_type.value,
                    qr_chain_id=self.DEFAULT_CHAIN_ID,
                )

                stats.generated += 1
                logger.debug(
                    f"Generated QR for wallet {wallet.address[:10]}... "
                    f"-> {storage_type.value}"
                )

            except Exception as e:
                logger.error(f"Failed to generate QR for {wallet.address}: {e}")
                stats.errors += 1
                stats.error_addresses.append(wallet.address[:10] + "...")

    async def _migrate_to_cdn(self, stats: QRGenerationStats) -> None:
        """Migrate local QR codes to CDN.

        Only runs if CDN is enabled and there's capacity in this batch.
        """
        if not self._cdn_storage:
            return

        remaining = self.BATCH_SIZE - stats.generated
        if remaining <= 0:
            return

        # Get wallets with local QRs
        wallets = await self._wallet_repo.get_wallets_with_local_qr(limit=remaining)

        logger.info(f"Found {len(wallets)} wallets to migrate to CDN")

        for wallet in wallets:
            try:
                # Regenerate QR for CDN (fresher, optimized)
                qr_bytes = self._qr_generator.generate(
                    address=wallet.address,
                    chain_id=wallet.qr_chain_id or self.DEFAULT_CHAIN_ID,
                )

                # Upload to CDN
                path = self._qr_generator.get_storage_path(wallet.address)
                url = await self._cdn_storage.upload(qr_bytes, path)

                # Update wallet record
                await self._wallet_repo.update_qr_info(
                    wallet_id=wallet.id_,
                    qr_image_url=url,
                    qr_storage_type=QRStorageType.CDN.value,
                    qr_chain_id=wallet.qr_chain_id or self.DEFAULT_CHAIN_ID,
                )

                # Optionally delete local copy
                if wallet.qr_image_url and "/static/qr/" in wallet.qr_image_url:
                    old_path = wallet.qr_image_url.split("/static/qr/")[-1]
                    await self._local_storage.delete(f"qr/{old_path}")

                stats.migrated += 1
                logger.debug(f"Migrated QR to CDN for {wallet.address[:10]}...")

            except Exception as e:
                logger.error(f"Failed to migrate QR for {wallet.address}: {e}")
                stats.errors += 1
                stats.error_addresses.append(wallet.address[:10] + "...")
