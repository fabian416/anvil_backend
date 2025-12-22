# Export Generator Integration Guide

This guide explains how to integrate the ExportGeneratorAdapter into your application.

## Prerequisites

- Python 3.12+
- Existing conversation and message infrastructure
- (Optional) reportlab for PDF generation

## Installation Steps

### 1. Install Optional Dependencies

For PDF support:

```bash
pip install reportlab==3.6.13
```

Or add to `pyproject.toml`:

```toml
[project.optional-dependencies]
export = [
    "reportlab>=3.6.0",
]
```

Then install:

```bash
uv pip install -e '.[export]'
```

### 2. Verify File Structure

Ensure these files are in place:

```
src/app/
├── domain/
│   ├── ports/
│   │   └── export_generator.py          # Port interface
│   ├── exceptions/
│   │   └── chat.py                       # Extended with export exceptions
│   └── value_objects/
│       └── chat/
│           └── export.py                 # Existing value objects
└── infrastructure/
    └── adapters/
        └── chat/
            ├── __init__.py               # Module exports
            └── export_generator_adapter.py  # Adapter implementation

tests/unit/infrastructure/adapters/
└── test_export_generator_adapter.py      # Unit tests

examples/
└── export_generator_demo.py              # Demo script
```

### 3. Configure Dishka Dependency Injection

Create a provider for export services:

```python
# src/app/setup/ioc/export.py

from dishka import Provider, Scope, provide

from app.domain.ports.export_generator import ExportGenerator
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)
from app.infrastructure.config import Config


class ExportProvider(Provider):
    """Provider for export-related dependencies."""

    scope = Scope.APP

    @provide
    def export_generator(self, config: Config) -> ExportGenerator:
        """
        Provide export generator adapter.

        Args:
            config: Application configuration

        Returns:
            Export generator implementation
        """
        storage_path = config.export.storage_path or "/tmp/conversation_exports"

        return ExportGeneratorAdapter(storage_path=storage_path)
```

### 4. Add Configuration

Add export configuration to your config files:

```toml
# config/local/config.toml

[export]
storage_path = "/tmp/conversation_exports"
default_format = "json"
enable_pii_redaction = true
default_compliance_standard = ""  # empty = no compliance by default

[export.retention]
default_days = 30
sec_years = 7
gdpr_years = 2
finra_years = 6
```

Create config model:

```python
# src/app/infrastructure/config/export.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExportRetentionConfig:
    """Export retention configuration."""

    default_days: int = 30
    sec_years: int = 7
    gdpr_years: int = 2
    finra_years: int = 6


@dataclass
class ExportConfig:
    """Export configuration."""

    storage_path: str
    default_format: str = "json"
    enable_pii_redaction: bool = True
    default_compliance_standard: str = ""
    retention: ExportRetentionConfig = None

    def __post_init__(self):
        if self.retention is None:
            self.retention = ExportRetentionConfig()
```

Add to main config:

```python
# src/app/infrastructure/config/__init__.py

from app.infrastructure.config.export import ExportConfig

@dataclass
class Config:
    # ... existing fields ...
    export: ExportConfig
```

### 5. Register Provider

Add the export provider to your container setup:

```python
# src/app/setup/ioc/__init__.py

from app.setup.ioc.export import ExportProvider

def create_container() -> Container:
    container = make_container(
        # ... existing providers ...
        ExportProvider(),
    )
    return container
```

### 6. Create Application Service (Optional)

Create an application-level export service:

```python
# src/app/application/services/export_service.py

from uuid import UUID
from typing import List, Optional

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.ports.export_generator import ExportGenerator
from app.domain.ports.conversation_repository import ConversationRepository
from app.domain.ports.message_repository import MessageRepository
from app.domain.ports.export_repository import ExportRepository
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)
from app.domain.entities.chat.conversation_export import ConversationExport
from app.domain.exceptions.chat import ConversationNotFoundError


class ExportService:
    """
    Application service for conversation exports.

    Orchestrates export generation, storage, and retrieval.
    """

    def __init__(
        self,
        export_generator: ExportGenerator,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        export_repository: ExportRepository,
    ):
        self.export_generator = export_generator
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.export_repository = export_repository

    async def create_export(
        self,
        conversation_id: UUID,
        user_id: int,
        format: ExportFormat,
        redact_pii: bool = False,
        pii_config: Optional[PIIRedactionConfig] = None,
        compliance_standard: Optional[ComplianceStandard] = None,
    ) -> ConversationExport:
        """
        Create a conversation export.

        Args:
            conversation_id: Conversation to export
            user_id: User requesting export
            format: Export format
            redact_pii: Whether to redact PII
            pii_config: PII redaction configuration
            compliance_standard: Compliance standard to apply

        Returns:
            ConversationExport entity

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
            ConversationAccessDeniedError: If user doesn't own conversation
        """
        # Get conversation
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        # Verify ownership
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedError(conversation_id, user_id)

        # Get messages
        messages = await self.message_repository.get_by_conversation(conversation_id)

        # Create export entity
        export = ConversationExport(
            id=uuid4(),
            conversation_id=conversation_id,
            user_id=user_id,
            format=format,
            status="pending",
            redact_pii=redact_pii,
            pii_redaction_config=pii_config,
            compliance_standard=compliance_standard,
        )

        # Save export record
        export = await self.export_repository.save(export)

        # Mark as processing
        export.mark_as_processing()
        await self.export_repository.save(export)

        try:
            # Generate export
            file_path, content = await self.export_generator.generate_export(
                conversation=conversation,
                messages=messages,
                format=format,
                redact_pii=redact_pii,
                pii_config=pii_config,
                compliance_standard=compliance_standard,
            )

            # Mark as completed
            from datetime import datetime, timedelta
            export.mark_as_completed(
                file_path=file_path,
                file_size_bytes=len(content),
                download_url=f"/api/exports/{export.id}/download",
                expires_at=datetime.utcnow() + timedelta(days=30),
            )

        except Exception as e:
            # Mark as failed
            export.mark_as_failed(str(e))
            raise

        finally:
            # Save final state
            await self.export_repository.save(export)

        return export

    async def get_export(self, export_id: UUID, user_id: int) -> ConversationExport:
        """
        Get export by ID.

        Args:
            export_id: Export identifier
            user_id: User requesting export

        Returns:
            ConversationExport entity

        Raises:
            ExportNotFoundError: If export doesn't exist
            ExportAccessDeniedError: If user doesn't own export
        """
        export = await self.export_repository.get_by_id(export_id)
        if not export:
            raise ExportNotFoundError(export_id)

        if export.user_id != user_id:
            raise ExportAccessDeniedError(export_id, user_id)

        return export
```

### 7. Create HTTP Controller (FastAPI)

```python
# src/app/presentation/http/controllers/exports/router.py

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from dishka.integrations.fastapi import FromDishka

from app.application.services.export_service import ExportService
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)
from app.presentation.http.controllers.exports.schemas import (
    CreateExportRequest,
    ExportResponse,
)
from app.presentation.http.auth.dependencies import get_current_user_id


router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportResponse)
async def create_export(
    request: CreateExportRequest,
    export_service: FromDishka[ExportService],
    user_id: int = Depends(get_current_user_id),
):
    """
    Create a conversation export.

    Generates an export of the conversation in the requested format.
    Export can include PII redaction and compliance formatting.
    """
    pii_config = None
    if request.redact_pii:
        pii_config = PIIRedactionConfig(
            redact_emails=True,
            redact_wallet_addresses=True,
            redact_phone_numbers=True,
        )

    export = await export_service.create_export(
        conversation_id=request.conversation_id,
        user_id=user_id,
        format=request.format,
        redact_pii=request.redact_pii,
        pii_config=pii_config,
        compliance_standard=request.compliance_standard,
    )

    return ExportResponse.from_entity(export)


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: UUID,
    export_service: FromDishka[ExportService],
    user_id: int = Depends(get_current_user_id),
):
    """Get export by ID."""
    export = await export_service.get_export(export_id, user_id)
    return ExportResponse.from_entity(export)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    export_service: FromDishka[ExportService],
    user_id: int = Depends(get_current_user_id),
):
    """Download export file."""
    from fastapi.responses import FileResponse

    export = await export_service.get_export(export_id, user_id)

    if export.is_expired():
        raise HTTPException(status_code=410, detail="Export has expired")

    if not export.is_completed():
        raise HTTPException(status_code=404, detail="Export not ready")

    return FileResponse(
        export.file_path,
        media_type=f"application/{export.format.value}",
        filename=f"conversation_{export.conversation_id}.{export.format.value}",
    )
```

### 8. Add Celery Task for Background Exports

```python
# src/app/infrastructure/celery/tasks/export_tasks.py

from uuid import UUID
from celery import shared_task

from app.setup.ioc import get_container
from app.application.services.export_service import ExportService


@shared_task(name="exports.generate_export")
def generate_export_task(
    export_id: str,
    conversation_id: str,
    user_id: int,
    format: str,
    redact_pii: bool = False,
    compliance_standard: str | None = None,
):
    """
    Background task for export generation.

    Args:
        export_id: Export identifier
        conversation_id: Conversation to export
        user_id: User requesting export
        format: Export format
        redact_pii: Whether to redact PII
        compliance_standard: Optional compliance standard
    """
    from app.domain.value_objects.chat.export import ExportFormat, ComplianceStandard

    container = get_container()
    export_service = container.resolve(ExportService)

    # Convert format string to enum
    export_format = ExportFormat(format)
    compliance = ComplianceStandard(compliance_standard) if compliance_standard else None

    # Generate export
    asyncio.run(
        export_service.create_export(
            conversation_id=UUID(conversation_id),
            user_id=user_id,
            format=export_format,
            redact_pii=redact_pii,
            compliance_standard=compliance,
        )
    )
```

## Testing Integration

### Run Unit Tests

```bash
pytest tests/unit/infrastructure/adapters/test_export_generator_adapter.py -v
```

### Run Demo Script

```bash
python examples/export_generator_demo.py
```

### Manual Integration Test

```python
import asyncio
from uuid import uuid4

async def test_integration():
    from app.setup.ioc import get_container
    from app.application.services.export_service import ExportService
    from app.domain.value_objects.chat.export import ExportFormat

    container = get_container()
    export_service = container.resolve(ExportService)

    # Create test export
    export = await export_service.create_export(
        conversation_id=uuid4(),  # Replace with real ID
        user_id=1,
        format=ExportFormat.JSON,
    )

    print(f"Export created: {export.id}")
    print(f"Status: {export.status}")
    print(f"File path: {export.file_path}")

asyncio.run(test_integration())
```

## Production Deployment

### 1. Environment Variables

```bash
# .env
EXPORT_STORAGE_PATH=/var/exports/conversations
EXPORT_DEFAULT_FORMAT=json
EXPORT_ENABLE_PII_REDACTION=true
```

### 2. Storage Configuration

```bash
# Create export directory
mkdir -p /var/exports/conversations
chmod 700 /var/exports/conversations
chown app:app /var/exports/conversations
```

### 3. Cleanup Cron Job

```bash
# /etc/cron.daily/cleanup-exports
#!/bin/bash
find /var/exports/conversations -type f -mtime +30 -delete
```

### 4. Monitoring

Add metrics for:
- Export creation rate
- Export completion time
- Export failures
- Storage usage

## Troubleshooting

### PDF Generation Fails

```bash
# Install reportlab
pip install reportlab

# Verify installation
python -c "import reportlab; print(reportlab.__version__)"
```

### Storage Permission Errors

```bash
# Check directory permissions
ls -la /var/exports/

# Fix permissions
sudo chown -R app:app /var/exports/conversations
sudo chmod -R 700 /var/exports/conversations
```

### Import Errors

```bash
# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Install in development mode
uv pip install -e .
```

## Next Steps

1. Review [Quick Start Guide](QUICK_START.md)
2. Customize configuration for your environment
3. Implement additional export formats if needed
4. Add monitoring and alerting
5. Set up automated cleanup jobs
6. Configure cloud storage if needed

## Support

For issues:
1. Check logs for detailed error messages
2. Review test suite for examples
3. Consult [README](README.md) for feature documentation
4. Check compliance requirements for your use case
