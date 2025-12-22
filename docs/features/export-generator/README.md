# Conversation Export Generator

Enterprise-grade conversation export system with support for multiple formats, PII redaction, and compliance standards.

## Overview

The `ExportGeneratorAdapter` implements the hexagonal architecture pattern, providing a domain-agnostic way to export conversations in multiple formats with comprehensive privacy and compliance features.

## Architecture

### Port (Domain Layer)
- **Location**: `src/app/domain/ports/export_generator.py`
- **Interface**: `ExportGenerator` - Abstract base class defining export operations

### Adapter (Infrastructure Layer)
- **Location**: `src/app/infrastructure/adapters/chat/export_generator_adapter.py`
- **Implementation**: `ExportGeneratorAdapter` - Concrete implementation with all format generators

### Value Objects
- **Location**: `src/app/domain/value_objects/chat/export.py`
- **Objects**:
  - `ExportFormat` - Enum for export formats
  - `ComplianceStandard` - Enum for compliance standards
  - `PIIRedactionConfig` - Configuration for PII redaction
  - `ExportMetadata` - Metadata for exports
  - `ComplianceRequirements` - Compliance requirements

## Features

### 1. Multiple Export Formats

#### JSON Export
- Complete conversation data with metadata
- Structured format for programmatic access
- Preserves all message properties

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    include_metadata=True,
)
```

#### Markdown Export
- Human-readable formatted conversation
- Proper heading hierarchy
- Code block support
- Timestamped messages

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.MARKDOWN,
)
```

#### HTML Export
- Professional web-viewable export
- Built-in CSS styling
- Color-coded message roles
- Responsive design

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.HTML,
)
```

#### PDF Export
- Professional report format
- Uses reportlab library
- Paginated output
- Proper typography

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
)
```

**Note**: PDF generation requires the `reportlab` library:
```bash
pip install reportlab
```

### 2. PII Redaction

The adapter supports comprehensive PII redaction using regex patterns:

- **Email addresses**: `user@example.com` → `[REDACTED]`
- **Phone numbers**: `555-123-4567` → `[REDACTED]`
- **Wallet addresses**: `0x742d35Cc...` → `[REDACTED]`
- **IP addresses**: `192.168.1.1` → `[REDACTED]`
- **SSN**: `123-45-6789` → `[REDACTED]`
- **Credit cards**: `4111-1111-1111-1111` → `[REDACTED]`

```python
pii_config = PIIRedactionConfig(
    redact_emails=True,
    redact_wallet_addresses=True,
    redact_phone_numbers=True,
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

### 3. Compliance Standards

#### SEC (Securities and Exchange Commission)
- **Retention**: 7 years
- **Allowed formats**: PDF, JSON
- **Digital signature**: Required
- **Timestamp verification**: Required
- **PII redaction**: Optional (may need unredacted data)

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    compliance_standard=ComplianceStandard.SEC,
)
```

#### GDPR (General Data Protection Regulation)
- **Retention**: 2 years (right to erasure)
- **Allowed formats**: All formats
- **Digital signature**: Not required
- **Timestamp verification**: Required
- **PII redaction**: Required

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.HTML,
    compliance_standard=ComplianceStandard.GDPR,
    redact_pii=True,
    pii_config=PIIRedactionConfig(),
)
```

#### FINRA (Financial Industry Regulatory Authority)
- **Retention**: 6 years
- **Allowed formats**: PDF, JSON
- **Digital signature**: Required
- **Timestamp verification**: Required
- **PII redaction**: Optional

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
    compliance_standard=ComplianceStandard.FINRA,
)
```

### 4. Export Metadata

Generate comprehensive metadata for audit trails:

```python
metadata = await adapter.get_export_metadata(
    export_id=uuid4(),
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    file_size_bytes=1024,
    compliance_standard=ComplianceStandard.SEC,
    pii_redacted=True,
)

print(f"Export ID: {metadata.export_id}")
print(f"Message Count: {metadata.message_count}")
print(f"Hash: {metadata.hash_value}")
print(f"Digitally Signed: {metadata.digitally_signed}")
```

### 5. Async File Generation

All export operations are asynchronous and support progress tracking:

```python
# Generate export asynchronously
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
)

# File is written to storage path
print(f"Export saved to: {file_path}")
print(f"File size: {len(content)} bytes")
```

## Configuration

### Storage Path

Configure the export storage directory:

```python
adapter = ExportGeneratorAdapter(
    storage_path="/var/exports/conversations"
)
```

Default: `/tmp/conversation_exports`

### Export Options

Control what's included in exports:

```python
file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
    include_metadata=True,      # Include conversation metadata
    include_timestamps=True,     # Include message timestamps
    include_agent_names=True,    # Include agent type information
)
```

## Usage Examples

### Basic Export

```python
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)
from app.domain.value_objects.chat.export import ExportFormat

adapter = ExportGeneratorAdapter()

file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.JSON,
)
```

### Export with PII Redaction

```python
from app.domain.value_objects.chat.export import PIIRedactionConfig

pii_config = PIIRedactionConfig(
    redact_wallet_addresses=True,
    redact_emails=True,
)

file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.HTML,
    redact_pii=True,
    pii_config=pii_config,
)
```

### Compliance Export

```python
from app.domain.value_objects.chat.export import ComplianceStandard

file_path, content = await adapter.generate_export(
    conversation=conversation,
    messages=messages,
    format=ExportFormat.PDF,
    compliance_standard=ComplianceStandard.SEC,
)
```

## Error Handling

### Export Generation Errors

```python
from app.domain.exceptions.chat import ExportGenerationError

try:
    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.PDF,
    )
except ExportGenerationError as e:
    print(f"Export failed: {e}")
```

### Compliance Violations

```python
from app.domain.exceptions.chat import ComplianceViolationError

try:
    # CSV not allowed for SEC compliance
    file_path, content = await adapter.generate_export(
        conversation=conversation,
        messages=messages,
        format=ExportFormat.CSV,
        compliance_standard=ComplianceStandard.SEC,
    )
except ComplianceViolationError as e:
    print(f"Compliance violation: {e}")
```

## Testing

Run the test suite:

```bash
pytest tests/unit/infrastructure/adapters/test_export_generator_adapter.py -v
```

Run the demonstration script:

```bash
python examples/export_generator_demo.py
```

## Integration with Dishka

Example Dishka provider configuration:

```python
from dishka import Provider, Scope, provide
from app.domain.ports.export_generator import ExportGenerator
from app.infrastructure.adapters.chat.export_generator_adapter import (
    ExportGeneratorAdapter,
)

class ExportProvider(Provider):
    scope = Scope.APP

    @provide
    def export_generator(self) -> ExportGenerator:
        return ExportGeneratorAdapter(
            storage_path="/var/exports/conversations"
        )
```

## Performance Considerations

### File Size Limits

- **JSON**: No practical limit (memory-based)
- **Markdown**: No practical limit (memory-based)
- **HTML**: No practical limit (memory-based)
- **PDF**: Large conversations may require pagination

### Memory Usage

All formats generate content in memory before writing to disk. For very large conversations (>10,000 messages), consider:

1. Implementing streaming writes
2. Paginating PDF exports
3. Chunking large exports

### Async Performance

Exports are generated asynchronously with proper locking:

```python
# Multiple exports can run concurrently
tasks = [
    adapter.generate_export(conv1, msgs1, ExportFormat.JSON),
    adapter.generate_export(conv2, msgs2, ExportFormat.PDF),
    adapter.generate_export(conv3, msgs3, ExportFormat.HTML),
]

results = await asyncio.gather(*tasks)
```

## Security Considerations

### PII Protection

Always enable PII redaction for:
- Public exports
- GDPR compliance
- Untrusted storage locations

### File Storage

- Ensure storage path has appropriate permissions (600/700)
- Use encrypted storage for sensitive data
- Implement file expiration policies

### Digital Signatures

Compliance exports include SHA-256 hashes for verification:

```python
metadata = await adapter.get_export_metadata(...)
print(f"Hash: {metadata.hash_value}")
print(f"Signature algorithm: {metadata.signature_algorithm}")
```

## Roadmap

Future enhancements:

- [ ] CSV export format implementation
- [ ] Excel (XLSX) export format
- [ ] Batch export operations
- [ ] Streaming export for large conversations
- [ ] S3/cloud storage integration
- [ ] Email delivery of exports
- [ ] Export scheduling and automation
- [ ] Multi-language support
- [ ] Custom export templates

## Contributing

When extending the export generator:

1. Add new formats to `ExportFormat` enum
2. Implement format generator method in adapter
3. Add compliance validation if needed
4. Create comprehensive tests
5. Update documentation

## License

MIT License - See LICENSE file for details
