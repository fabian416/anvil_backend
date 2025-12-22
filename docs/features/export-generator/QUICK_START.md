# Export Generator Quick Start Guide

## Installation

The export generator is included in the base installation. For PDF support, install reportlab:

```bash
pip install reportlab
```

## Basic Usage

### 1. Import Required Classes

```python
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)
```

### 2. Initialize Adapter

```python
# Default storage: /tmp/conversation_exports
adapter = ExportGeneratorAdapter()

# Custom storage path
adapter = ExportGeneratorAdapter(storage_path="/var/exports")
```

### 3. Generate Export

```python
file_path, content = await adapter.generate_export(
    conversation=my_conversation,
    messages=my_messages,
    format=ExportFormat.JSON,  # or PDF, HTML, MARKDOWN
)

print(f"Export saved to: {file_path}")
```

## Common Scenarios

### JSON Export (API Integration)

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    include_metadata=True,
    include_timestamps=True,
)
```

### HTML Export (Web Preview)

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.HTML,
    include_agent_names=True,
)
```

### PDF Export (Professional Report)

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
    include_metadata=True,
)
```

### Export with PII Redaction

```python
pii_config = PIIRedactionConfig(
    redact_emails=True,
    redact_wallet_addresses=True,
    replacement_text="[REDACTED]",
)

file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    redact_pii=True,
    pii_config=pii_config,
)
```

### SEC Compliance Export

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
    compliance_standard=ComplianceStandard.SEC,
)
```

### GDPR Compliance Export

```python
pii_config = PIIRedactionConfig()  # All PII redaction enabled

file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.HTML,
    compliance_standard=ComplianceStandard.GDPR,
    redact_pii=True,
    pii_config=pii_config,
)
```

## Format Comparison

| Format   | Use Case                | Pros                          | Cons                    |
|----------|------------------------|-------------------------------|-------------------------|
| JSON     | API, programmatic      | Structured, complete data     | Not human-readable      |
| Markdown | Documentation, sharing | Readable, portable            | Limited styling         |
| HTML     | Web viewing, preview   | Rich styling, interactive     | Requires browser        |
| PDF      | Reports, archival      | Professional, universal       | Requires reportlab lib  |

## Compliance Standards

| Standard | Retention | Allowed Formats | Digital Signature | PII Redaction |
|----------|-----------|----------------|-------------------|---------------|
| SEC      | 7 years   | PDF, JSON      | Required          | Optional      |
| GDPR     | 2 years   | All            | Not required      | Required      |
| FINRA    | 6 years   | PDF, JSON      | Required          | Optional      |

## PII Redaction Patterns

| Data Type        | Example                              | Redacted          |
|-----------------|--------------------------------------|-------------------|
| Email           | user@example.com                     | [REDACTED]        |
| Phone           | 555-123-4567                         | [REDACTED]        |
| Wallet Address  | 0x742d35Cc6634C0532925a3b844Bc9e... | [REDACTED]        |
| IP Address      | 192.168.1.100                        | [REDACTED]        |
| SSN             | 123-45-6789                          | [REDACTED]        |
| Credit Card     | 4111-1111-1111-1111                  | [REDACTED]        |

## Error Handling

```python
from app.domain.exceptions.chat import (
    ExportGenerationError,
    ComplianceViolationError,
)

try:
    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.PDF,
        compliance_standard=ComplianceStandard.SEC,
    )
except ComplianceViolationError as e:
    # Format not allowed for compliance standard
    print(f"Compliance violation: {e}")
except ExportGenerationError as e:
    # General export failure
    print(f"Export failed: {e}")
```

## Best Practices

### 1. Storage Management

```python
# Use dedicated export directory
adapter = ExportGeneratorAdapter(
    storage_path="/var/exports/conversations"
)

# Implement cleanup for old exports
import os
from datetime import datetime, timedelta

def cleanup_old_exports(path, days=30):
    cutoff = datetime.now() - timedelta(days=days)
    for file in Path(path).glob("*.json"):
        if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
            file.unlink()
```

### 2. PII Protection

```python
# Always redact PII for public exports
if export_is_public:
    pii_config = PIIRedactionConfig()  # All redaction enabled
    redact_pii = True
else:
    pii_config = None
    redact_pii = False
```

### 3. Compliance Selection

```python
# Select compliance based on business context
if is_financial_conversation:
    compliance = ComplianceStandard.FINRA
elif is_eu_user:
    compliance = ComplianceStandard.GDPR
elif is_securities_related:
    compliance = ComplianceStandard.SEC
else:
    compliance = None
```

### 4. Format Selection

```python
# Choose format based on use case
if request.accepts("application/json"):
    format = ExportFormat.JSON
elif request.accepts("application/pdf"):
    format = ExportFormat.PDF
elif request.accepts("text/html"):
    format = ExportFormat.HTML
else:
    format = ExportFormat.MARKDOWN  # Default fallback
```

## Testing

Quick test to verify installation:

```python
import asyncio
from uuid import uuid4
from datetime import datetime

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)
from app.domain.value_objects.chat.export import ExportFormat

async def test_export():
    # Create test data
    conversation = Conversation(
        id=uuid4(),
        user_id=1,
        title="Test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    messages = [
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello",
            created_at=datetime.now(),
        )
    ]

    # Test export
    adapter = ExportGeneratorAdapter()
    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.JSON,
    )

    print(f"✓ Export successful: {file_path}")
    return True

# Run test
asyncio.run(test_export())
```

## Next Steps

- Review [Full Documentation](README.md)
- Run [Demo Script](../../examples/export_generator_demo.py)
- Check [Test Suite](../../tests/unit/infrastructure/adapters/test_export_generator_adapter.py)
- Explore [Integration Examples](#integration-examples)

## Support

For issues or questions:
1. Check the [Full Documentation](README.md)
2. Review error messages in exceptions
3. Enable debug logging
4. Consult test examples
