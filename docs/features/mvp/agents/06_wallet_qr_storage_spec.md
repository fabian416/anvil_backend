# Wallet QR Code Storage & CDN — Specification

**Version**: 1.0  
**Date**: 2026-02-02  
**Status**: Specification  
**Context**: Wallet QR Code Pre-generation, Storage, and Agent Enrichment  
**Related**: Receive Endpoint (GET /api/v1/wallet/receive), Receive Handler, Celery Background Tasks

---

## Overview

This specification defines a system for **pre-generating and storing QR codes** for wallet addresses. QR codes are generated as PNG images and stored either locally or on DigitalOcean Spaces CDN. The agent response for `RECEIVE` intent includes a `qr_image_url` field populated from the database, providing instant QR code access without on-demand generation.

### Key Features

1. **Pre-generated QR Codes**: QR codes generated in background, stored with wallet record
2. **Dual Storage**: Local filesystem (fallback) or DigitalOcean Spaces CDN (preferred)
3. **Celery Background Task**: Periodic task to generate missing QRs and migrate to CDN
4. **Agent Enrichment**: `qr_image_url` field in receive handler response
5. **EIP-681 Format**: Standard `ethereum:{chain_id}:{address}` QR data format

---

## Database Schema Changes

### Wallet Table Extensions

Add to `wallets` table:

```sql
ALTER TABLE wallets ADD COLUMN qr_image_url VARCHAR(512) NULL;
ALTER TABLE wallets ADD COLUMN qr_storage_type VARCHAR(10) NULL DEFAULT 'pending';
ALTER TABLE wallets ADD COLUMN qr_generated_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE wallets ADD COLUMN qr_chain_id INTEGER NULL DEFAULT 8453;

-- Index for Celery task queries
CREATE INDEX idx_wallets_qr_pending ON wallets (qr_storage_type) WHERE qr_storage_type = 'pending';
CREATE INDEX idx_wallets_qr_local ON wallets (qr_storage_type) WHERE qr_storage_type = 'local';
```

### Column Definitions

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `qr_image_url` | VARCHAR(512) | NULL | Full URL to QR image (local path or CDN URL) |
| `qr_storage_type` | VARCHAR(10) | 'pending' | Storage type: `pending`, `local`, `cdn` |
| `qr_generated_at` | TIMESTAMP | NULL | When QR was last generated |
| `qr_chain_id` | INTEGER | 8453 | Chain ID encoded in QR (default: Base) |

### Storage Type Values

| Value | Description |
|-------|-------------|
| `pending` | QR not yet generated (new wallets) |
| `local` | Stored in local filesystem |
| `cdn` | Stored in DigitalOcean Spaces CDN |

---

## Domain Layer

### Wallet Entity Extension

```python
# src/app/domain/entities/wallet.py

@dataclass(eq=False, kw_only=True)
class Wallet(Entity[WalletId]):
    # ... existing fields ...
    
    # QR Code fields
    qr_image_url: str | None = None
    qr_storage_type: str = "pending"  # pending | local | cdn
    qr_generated_at: datetime | None = None
    qr_chain_id: int = 8453  # Default to Base
```

### QR Storage Type Enum

```python
# src/app/domain/enums/qr_storage_type.py

from enum import Enum

class QRStorageType(str, Enum):
    """Storage type for wallet QR codes."""
    PENDING = "pending"
    LOCAL = "local"
    CDN = "cdn"
```

---

## Infrastructure Layer

### QR Code Generator Service

```python
# src/app/infrastructure/qr/qr_generator.py

import qrcode
from io import BytesIO
from PIL import Image
from pathlib import Path

class QRCodeGenerator:
    """
    Generate QR codes for wallet addresses using EIP-681 format.
    
    Format: ethereum:{chain_id}:{address}
    Example: ethereum:8453:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d
    """
    
    def __init__(
        self,
        box_size: int = 12,
        border: int = 4,
        fill_color: str = "#00d4aa",  # Anvil brand color
        back_color: str = "white",
    ):
        self._box_size = box_size
        self._border = border
        self._fill_color = fill_color
        self._back_color = back_color
    
    def generate(
        self,
        address: str,
        chain_id: int = 8453,
        size: int = 300,
    ) -> bytes:
        """
        Generate QR code PNG bytes for wallet address.
        
        Args:
            address: EVM wallet address (0x...)
            chain_id: Blockchain chain ID
            size: Output image size in pixels
            
        Returns:
            PNG image as bytes
        """
        # Build EIP-681 URI
        qr_data = f"ethereum:{chain_id}:{address}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=self._box_size,
            border=self._border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(
            fill_color=self._fill_color,
            back_color=self._back_color,
        )
        
        # Resize to requested size
        img = img.resize((size, size), Image.LANCZOS)
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
    
    def get_qr_data(self, address: str, chain_id: int = 8453) -> str:
        """Get QR data string without generating image."""
        return f"ethereum:{chain_id}:{address}"
```

### Storage Port (Interface)

```python
# src/app/domain/ports/storage/file_storage.py

from typing import Protocol

class FileStoragePort(Protocol):
    """Port for file storage operations."""
    
    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """
        Upload file and return public URL.
        
        Args:
            data: File content as bytes
            path: Storage path (e.g., "qr/0x7a23...8f4d.png")
            content_type: MIME type
            
        Returns:
            Public URL to access the file
        """
        ...
    
    async def delete(self, path: str) -> bool:
        """Delete file by path."""
        ...
    
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        ...
```

### Local Storage Adapter

```python
# src/app/infrastructure/storage/local_storage.py

import aiofiles
from pathlib import Path

class LocalStorageAdapter:
    """
    Local filesystem storage adapter.
    
    Stores files in: {base_path}/qr/{address_short}/{filename}
    Serves via: /static/qr/{address_short}/{filename}
    """
    
    def __init__(
        self,
        base_path: Path,
        base_url: str = "/static",
    ):
        self._base_path = base_path
        self._base_url = base_url
        
        # Ensure directory exists
        (base_path / "qr").mkdir(parents=True, exist_ok=True)
    
    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """Save file locally and return URL."""
        full_path = self._base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        
        return f"{self._base_url}/{path}"
    
    async def delete(self, path: str) -> bool:
        """Delete local file."""
        full_path = self._base_path / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    async def exists(self, path: str) -> bool:
        """Check if file exists locally."""
        return (self._base_path / path).exists()
```

### DigitalOcean Spaces Adapter

```python
# src/app/infrastructure/storage/digitalocean_spaces.py

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class DigitalOceanSpacesAdapter:
    """
    DigitalOcean Spaces (S3-compatible) storage adapter.
    
    Files are stored in: {bucket}/qr/{address_prefix}/{filename}
    CDN URL: https://{bucket}.{region}.cdn.digitaloceanspaces.com/qr/...
    """
    
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        cdn_enabled: bool = True,
    ):
        self._bucket = bucket
        self._region = region
        self._cdn_enabled = cdn_enabled
        
        # Build CDN or direct URL base
        if cdn_enabled:
            self._base_url = f"https://{bucket}.{region}.cdn.digitaloceanspaces.com"
        else:
            self._base_url = f"https://{bucket}.{region}.digitaloceanspaces.com"
        
        # Initialize S3 client
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://{region}.digitaloceanspaces.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
    
    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """Upload to DigitalOcean Spaces and return CDN URL."""
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=path,
                Body=data,
                ContentType=content_type,
                ACL="public-read",
                CacheControl="public, max-age=31536000",  # 1 year cache
            )
            return f"{self._base_url}/{path}"
        except ClientError as e:
            logger.error(f"Failed to upload to DO Spaces: {e}")
            raise
    
    async def delete(self, path: str) -> bool:
        """Delete from DigitalOcean Spaces."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=path)
            return True
        except ClientError:
            return False
    
    async def exists(self, path: str) -> bool:
        """Check if file exists in bucket."""
        try:
            self._client.head_object(Bucket=self._bucket, Key=path)
            return True
        except ClientError:
            return False
```

---

## Configuration

### TOML Configuration

```toml
# config/local/config.toml

[storage]
# QR code storage configuration
qr_storage_enabled = true
qr_storage_type = "local"  # "local" or "cdn"
qr_local_path = "./static/qr"
qr_local_base_url = "/static/qr"

# DigitalOcean Spaces (optional, for CDN)
[storage.digitalocean]
enabled = false
region = "nyc3"
bucket = "anvil-assets"
cdn_enabled = true
```

```toml
# config/local/.secrets.toml

[storage.digitalocean]
access_key = ""
secret_key = ""
```

### Settings Class

```python
# src/app/setup/config/storage.py

from pydantic import Field
from pydantic_settings import BaseSettings

class StorageSettings(BaseSettings):
    """Storage configuration for QR codes and assets."""
    
    # QR Storage
    qr_storage_enabled: bool = Field(default=True)
    qr_storage_type: str = Field(default="local")  # local | cdn
    qr_local_path: str = Field(default="./static/qr")
    qr_local_base_url: str = Field(default="/static/qr")
    
    # DigitalOcean Spaces
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
```

---

## Application Layer

### QR Generation Task

```python
# src/app/application/wallet/tasks/generate_wallet_qr.py

from dataclasses import dataclass
from datetime import datetime, UTC
import logging

from app.domain.enums.qr_storage_type import QRStorageType
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.ports.storage.file_storage import FileStoragePort
from app.infrastructure.qr.qr_generator import QRCodeGenerator

logger = logging.getLogger(__name__)

@dataclass
class QRGenerationStats:
    """Statistics from QR generation task."""
    generated: int = 0
    migrated: int = 0
    errors: int = 0
    skipped: int = 0

class GenerateWalletQRTask:
    """
    Background task to generate and store wallet QR codes.
    
    Runs every 3 minutes, processes up to 30 wallets per run:
    1. Find wallets with qr_storage_type='pending' → generate QR
    2. If CDN enabled, find qr_storage_type='local' → migrate to CDN
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
        self._wallet_repo = wallet_repository
        self._local_storage = local_storage
        self._cdn_storage = cdn_storage
        self._qr_generator = qr_generator
        self._cdn_enabled = cdn_enabled and cdn_storage is not None
    
    async def run(self) -> QRGenerationStats:
        """Execute QR generation task."""
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
        """Generate QR codes for wallets without QR."""
        # Get wallets needing QR generation
        wallets = await self._wallet_repo.get_wallets_without_qr(
            limit=self.BATCH_SIZE
        )
        
        for wallet in wallets:
            try:
                # Generate QR image
                qr_bytes = self._qr_generator.generate(
                    address=wallet.address,
                    chain_id=self.DEFAULT_CHAIN_ID,
                )
                
                # Determine storage target
                storage = self._cdn_storage if self._cdn_enabled else self._local_storage
                storage_type = QRStorageType.CDN if self._cdn_enabled else QRStorageType.LOCAL
                
                # Upload QR image
                path = self._get_qr_path(wallet.address)
                url = await storage.upload(qr_bytes, path)
                
                # Update wallet record
                await self._wallet_repo.update_qr_info(
                    wallet_id=wallet.id_,
                    qr_image_url=url,
                    qr_storage_type=storage_type.value,
                    qr_chain_id=self.DEFAULT_CHAIN_ID,
                )
                
                stats.generated += 1
                logger.debug(f"Generated QR for wallet {wallet.address[:10]}...")
                
            except Exception as e:
                logger.error(f"Failed to generate QR for {wallet.address}: {e}")
                stats.errors += 1
    
    async def _migrate_to_cdn(self, stats: QRGenerationStats) -> None:
        """Migrate local QR codes to CDN."""
        remaining = self.BATCH_SIZE - stats.generated
        if remaining <= 0:
            return
        
        # Get wallets with local QRs
        wallets = await self._wallet_repo.get_wallets_with_local_qr(limit=remaining)
        
        for wallet in wallets:
            try:
                # Regenerate QR for CDN (fresher, optimized)
                qr_bytes = self._qr_generator.generate(
                    address=wallet.address,
                    chain_id=wallet.qr_chain_id or self.DEFAULT_CHAIN_ID,
                )
                
                # Upload to CDN
                path = self._get_qr_path(wallet.address)
                url = await self._cdn_storage.upload(qr_bytes, path)
                
                # Update wallet record
                await self._wallet_repo.update_qr_info(
                    wallet_id=wallet.id_,
                    qr_image_url=url,
                    qr_storage_type=QRStorageType.CDN.value,
                    qr_chain_id=wallet.qr_chain_id or self.DEFAULT_CHAIN_ID,
                )
                
                # Optionally delete local copy
                if wallet.qr_image_url:
                    old_path = wallet.qr_image_url.split("/static/qr/")[-1]
                    await self._local_storage.delete(f"qr/{old_path}")
                
                stats.migrated += 1
                logger.debug(f"Migrated QR to CDN for {wallet.address[:10]}...")
                
            except Exception as e:
                logger.error(f"Failed to migrate QR for {wallet.address}: {e}")
                stats.errors += 1
    
    def _get_qr_path(self, address: str) -> str:
        """Generate storage path for QR image."""
        # Use address prefix for directory sharding
        prefix = address[2:4].lower()  # First 2 chars after 0x
        filename = f"{address.lower()}.png"
        return f"qr/{prefix}/{filename}"
```

### Wallet Repository Extensions

```python
# Add to WalletRepository protocol

async def get_wallets_without_qr(self, limit: int = 30) -> list[Wallet]:
    """
    Get wallets with qr_storage_type='pending'.
    
    Args:
        limit: Maximum wallets to return
        
    Returns:
        List of wallets needing QR generation
    """
    ...

async def get_wallets_with_local_qr(self, limit: int = 30) -> list[Wallet]:
    """
    Get wallets with qr_storage_type='local'.
    
    For CDN migration.
    
    Args:
        limit: Maximum wallets to return
        
    Returns:
        List of wallets with local QR storage
    """
    ...

async def update_qr_info(
    self,
    wallet_id: WalletId,
    qr_image_url: str,
    qr_storage_type: str,
    qr_chain_id: int,
) -> bool:
    """
    Update wallet QR information.
    
    Args:
        wallet_id: Wallet ID
        qr_image_url: URL to QR image
        qr_storage_type: Storage type (local/cdn)
        qr_chain_id: Chain ID encoded in QR
        
    Returns:
        True if updated successfully
    """
    ...
```

---

## Celery Task

```python
# src/app/infrastructure/celery/tasks/wallet_qr_tasks.py

import asyncio
from celery.schedules import crontab

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.provider_registry import get_providers
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container."""
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
    """
    Generate QR codes for wallets that don't have them.
    
    Runs every 3 minutes, processes up to 30 wallets:
    1. Generate QR for wallets with qr_storage_type='pending'
    2. If CDN enabled, migrate qr_storage_type='local' to CDN
    """
    
    async def runner(container):
        from app.application.wallet.tasks.generate_wallet_qr import GenerateWalletQRTask
        from app.domain.ports.wallet.wallet_repository import WalletRepository
        from app.domain.ports.storage.file_storage import FileStoragePort
        from app.infrastructure.qr.qr_generator import QRCodeGenerator
        from app.setup.config.storage import StorageSettings
        
        # Get dependencies
        wallet_repo = await container.get(WalletRepository)
        storage_settings = await container.get(StorageSettings)
        
        # Get storage adapters
        local_storage = await container.get(FileStoragePort, qualifier="local")
        cdn_storage = None
        if storage_settings.is_cdn_enabled:
            cdn_storage = await container.get(FileStoragePort, qualifier="cdn")
        
        # Create task
        task = GenerateWalletQRTask(
            wallet_repository=wallet_repo,
            local_storage=local_storage,
            cdn_storage=cdn_storage,
            qr_generator=QRCodeGenerator(),
            cdn_enabled=storage_settings.is_cdn_enabled,
        )
        
        # Run
        stats = await task.run()
        print(
            f"Wallet QR generation: generated={stats.generated}, "
            f"migrated={stats.migrated}, errors={stats.errors}"
        )
    
    asyncio.run(_run_task(runner))


# Beat schedule entry (add to celery app config)
# "generate_wallet_qr_codes": {
#     "task": "generate_wallet_qr_codes",
#     "schedule": crontab(minute="*/3"),  # Every 3 minutes
# }
```

---

## Agent Response Enrichment

### Updated Receive Handler

```python
# Updated ReceiveHandlerResult in receive_handler.py

@dataclass
class ReceiveHandlerResult:
    """Result from receive handler."""
    
    content: str
    wallet_address: str
    ens_handle: str | None
    supported_networks: list[str]
    chain: str
    latency_ms: int
    language: str = "en"
    handler: str = "receive_handler"
    pending_action: str | None = None
    
    # NEW: QR Code fields from database
    qr_image_url: str | None = None      # Pre-generated QR image URL
    qr_data: str | None = None            # EIP-681 URI for client-side generation
    qr_chain_id: int = 8453               # Chain ID encoded in QR
```

### Handler Integration

```python
# In ReceiveHandler.get_receive_info()

async def get_receive_info(
    self,
    user_id: int,
    chain: str = "base",
    language: str = "en",
) -> ReceiveHandlerResult:
    """Get receive information with QR code from database."""
    start_time = time.time()
    
    try:
        # Get wallet with QR info
        wallets = await self._wallet_repo.get_by_user_id(UserId(user_id))
        
        if not wallets:
            return self._no_wallet_response(chain, language, start_time)
        
        wallet = self._select_primary_wallet(wallets)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build QR data for client-side fallback
        qr_chain_id = wallet.qr_chain_id or 8453
        qr_data = f"ethereum:{qr_chain_id}:{wallet.address}"
        
        return ReceiveHandlerResult(
            content=self._format_receive_response(
                wallet_address=wallet.address,
                ens_handle=None,
                chain=chain,
                language=language,
            ),
            wallet_address=wallet.address,
            ens_handle=None,
            supported_networks=[n["name"] for n in self.SUPPORTED_NETWORKS],
            chain=chain,
            latency_ms=latency_ms,
            language=language,
            
            # QR fields from database
            qr_image_url=wallet.qr_image_url,
            qr_data=qr_data,
            qr_chain_id=qr_chain_id,
        )
    except Exception as e:
        # ... error handling
```

---

## Response Schema

### Chat Response with QR Enrichment

```json
{
  "user_message": { "content": "I want to receive ETH", "..." },
  "agent_message": {
    "content": "📥 **Receive Funds**\n\nYour Wallet Address:\n`0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d`\n...",
    "agent_type": "receive_handler"
  },
  "routing": {
    "intent": "RECEIVE",
    "confidence": 0.95,
    "handler": "receive_handler"
  },
  "enrichment": {
    "receive_info": {
      "type": "receive_info",
      "address": "0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d",
      "qr_image_url": "https://anvil-assets.nyc3.cdn.digitaloceanspaces.com/qr/7a/0x7a23b8c9d4e5f6a7b8c9d4e5f6a78f4d.png",
      "qr_data": "ethereum:8453:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d",
      "qr_chain_id": 8453,
      "supported_networks": ["Ethereum", "Base", "Arbitrum", "Polygon", "Optimism"],
      "warning": "⚠️ Only send tokens on the correct network to avoid loss"
    }
  }
}
```

---

## Hexagonal Architecture

| Layer | File | Component |
|-------|------|-----------|
| **Domain** | `entities/wallet.py` | Extended Wallet entity with QR fields |
| **Domain** | `enums/qr_storage_type.py` | QRStorageType enum |
| **Domain** | `ports/storage/file_storage.py` | FileStoragePort interface |
| **Application** | `wallet/tasks/generate_wallet_qr.py` | GenerateWalletQRTask |
| **Application** | `chat/handlers/receive_handler.py` | Updated with QR response fields |
| **Infrastructure** | `qr/qr_generator.py` | QRCodeGenerator service |
| **Infrastructure** | `storage/local_storage.py` | LocalStorageAdapter |
| **Infrastructure** | `storage/digitalocean_spaces.py` | DigitalOceanSpacesAdapter |
| **Infrastructure** | `celery/tasks/wallet_qr_tasks.py` | Celery task definition |
| **Infrastructure** | `persistence_sqla/mappings/wallet.py` | Updated with QR columns |
| **Presentation** | Response schemas | Updated with qr_image_url field |

---

## Dependencies

### pyproject.toml

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "qrcode[pil]>=7.4.0",  # QR code generation with PIL support
    "Pillow>=10.0.0",       # Image processing
    "aiofiles>=23.0.0",     # Async file operations
    "boto3>=1.34.0",        # S3-compatible storage (already included)
]
```

### Install Command

```bash
uv pip install "qrcode[pil]>=7.4.0" "Pillow>=10.0.0" "aiofiles>=23.0.0"
```

---

## Migration

### Alembic Migration

```python
# migrations/versions/YYYYMMDD_add_wallet_qr_columns.py

def upgrade():
    op.add_column('wallets', sa.Column('qr_image_url', sa.String(512), nullable=True))
    op.add_column('wallets', sa.Column('qr_storage_type', sa.String(10), nullable=True, server_default='pending'))
    op.add_column('wallets', sa.Column('qr_generated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('wallets', sa.Column('qr_chain_id', sa.Integer(), nullable=True, server_default='8453'))
    
    # Indexes for Celery queries
    op.create_index('idx_wallets_qr_pending', 'wallets', ['qr_storage_type'], 
                    postgresql_where=sa.text("qr_storage_type = 'pending'"))
    op.create_index('idx_wallets_qr_local', 'wallets', ['qr_storage_type'],
                    postgresql_where=sa.text("qr_storage_type = 'local'"))

def downgrade():
    op.drop_index('idx_wallets_qr_local', 'wallets')
    op.drop_index('idx_wallets_qr_pending', 'wallets')
    op.drop_column('wallets', 'qr_chain_id')
    op.drop_column('wallets', 'qr_generated_at')
    op.drop_column('wallets', 'qr_storage_type')
    op.drop_column('wallets', 'qr_image_url')
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| QR generation time | < 100ms per image |
| Celery task duration | < 30s for 30 wallets |
| CDN response time | < 50ms (cached) |
| Local storage response | < 10ms (filesystem) |
| Agent response with QR | < 200ms |

---

## Monitoring

### Celery Task Metrics

```python
# Log after each run
logger.info(
    "wallet_qr_generation",
    extra={
        "generated": stats.generated,
        "migrated": stats.migrated,
        "errors": stats.errors,
        "duration_ms": duration_ms,
    }
)
```

### Health Checks

```python
# Admin endpoint to check QR generation status
GET /api/v1/admin/wallet-qr/status

{
  "pending_count": 150,
  "local_count": 45,
  "cdn_count": 1205,
  "last_run": "2026-02-02T14:30:00Z",
  "cdn_enabled": true
}
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| QR generation fails | Log error, increment error count, skip wallet |
| CDN upload fails | Fall back to local storage |
| CDN not configured | Use local storage only |
| No QR available | Return `qr_data` for client-side generation |
| Storage quota exceeded | Alert admin, pause task |

---

## Frontend Fallback

If `qr_image_url` is null, frontend can generate QR client-side:

```typescript
import QRCode from 'react-native-qrcode-svg';

const ReceiveQR = ({ qr_image_url, qr_data }: ReceiveInfo) => {
  if (qr_image_url) {
    return <Image source={{ uri: qr_image_url }} style={styles.qr} />;
  }
  
  // Fallback: generate client-side
  return <QRCode value={qr_data} size={200} />;
};
```

---

## Testing

### Unit Tests

- QRCodeGenerator generates valid PNG
- Storage adapters upload/delete correctly
- Task processes batch correctly
- Migration to CDN works

### Integration Tests

- End-to-end QR generation for new wallet
- CDN migration flow
- Agent response includes QR URL
- Fallback to local storage

---

## Open Items

- [ ] Logo overlay in QR code (Anvil branding)
- [ ] SVG format support for web
- [ ] Multi-chain QR (user selects chain, regenerate QR)
- [ ] QR regeneration on chain preference change
- [ ] Cleanup task for orphaned QR files
- [ ] Rate limiting for QR generation API endpoint
