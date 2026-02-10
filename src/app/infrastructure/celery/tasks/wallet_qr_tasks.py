"""
Wallet QR Code Generation Celery Tasks.

Background tasks for generating and storing wallet QR codes.
Runs periodically to:
1. Generate QR codes for wallets with pending/NULL status
2. Migrate local QR codes to CDN when enabled

Task Configuration:
- Runs every 3 minutes
- Processes max 30 wallets per run
- Uses EIP-681 format: ethereum:{chain_id}:{address}

Storage Options:
- Local: ./static/qr/{prefix}/{address}.png
- CDN: https://{bucket}.{region}.cdn.digitaloceanspaces.com/qr/{prefix}/{address}.png
"""

import asyncio
import logging
from pathlib import Path

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.provider_registry import get_providers
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings

logger = logging.getLogger(__name__)


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container using all registered providers."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()


@celery_app.task(name="generate_wallet_qr_codes")
def generate_wallet_qr_codes():
    """Generate QR codes for wallets that don't have them.

    Runs every 3 minutes, processes up to 30 wallets:
    1. Generate QR for wallets with qr_storage_type='pending' or NULL
    2. If CDN enabled, migrate qr_storage_type='local' to CDN

    This task handles inconsistencies by processing both NULL and 'pending'
    states, ensuring all wallets eventually get QR codes.
    """

    async def runner(container):
        from app.application.wallet.tasks.generate_wallet_qr import (
            GenerateWalletQRTask,
        )
        from app.domain.ports.wallet.wallet_repository import WalletRepository
        from app.infrastructure.qr.qr_generator import QRCodeGenerator
        from app.infrastructure.storage.local_storage import LocalStorageAdapter
        from app.infrastructure.storage.recallium_storage import RecalliumStorageAdapter
        from app.setup.config.storage import StorageSettings

        try:
            # Get wallet repository
            wallet_repo = await container.get(WalletRepository)

            # Get storage settings (may not be registered, use defaults)
            try:
                storage_settings = await container.get(StorageSettings)
            except Exception:
                logger.warning("StorageSettings not in container, using defaults")
                storage_settings = StorageSettings()

            # Create local storage adapter
            local_path = Path(storage_settings.qr_local_path)
            local_storage = LocalStorageAdapter(
                base_path=local_path,
                base_url=storage_settings.qr_local_base_url,
            )

            # Create CDN storage adapter if configured
            cdn_storage = None
            cdn_enabled = storage_settings.is_cdn_enabled
            if cdn_enabled:
                try:
                    cdn_storage = RecalliumStorageAdapter(
                        access_key=storage_settings.do_access_key,
                        secret_key=storage_settings.do_secret_key,
                        region=storage_settings.do_region,
                        bucket=storage_settings.do_bucket,
                        cdn_enabled=storage_settings.do_cdn_enabled,
                    )
                    logger.info("CDN storage (Recallium) enabled")
                except Exception as e:
                    logger.warning(f"Failed to initialize CDN storage: {e}")
                    cdn_enabled = False

            # Create QR generator
            qr_generator = QRCodeGenerator()

            # Create and run task
            task = GenerateWalletQRTask(
                wallet_repository=wallet_repo,
                local_storage=local_storage,
                cdn_storage=cdn_storage,
                qr_generator=qr_generator,
                cdn_enabled=cdn_enabled,
            )

            stats = await task.run()

            logger.info(
                f"Wallet QR generation completed: "
                f"generated={stats.generated}, "
                f"migrated={stats.migrated}, "
                f"errors={stats.errors}"
            )

            if stats.errors > 0:
                logger.warning(
                    f"QR generation errors for: {', '.join(stats.error_addresses)}"
                )

        except Exception as e:
            logger.error(f"Wallet QR generation task failed: {e}", exc_info=True)
            raise

    asyncio.run(_run_task(runner))
