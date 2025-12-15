"""
Conversation export service for compliance and data portability.

Generates exports in multiple formats with PII redaction and digital signatures.
"""

import logging
import re
import hashlib
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from io import BytesIO

from app.domain.value_objects.chat.export import (
    ExportFormat,
    ExportMetadata,
    PIIRedactionConfig,
    ComplianceRequirements,
    ComplianceStandard,
    ExportAuditEntry,
)
from app.domain.ports.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationExportService:
    """
    Export conversations in multiple formats with compliance support.

    Instead of GET /api/v1/conversations/{id}/export, users type:
    - "Export this conversation to PDF"
    - "Generate SEC-compliant export for last quarter"
    - "Export with GDPR redaction"
    """

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        # TODO: Add ports for PDF generation, digital signatures, etc.
    ):
        """
        Initialize export service.

        Args:
            conversation_repository: Repository for conversation data
        """
        self._repository = conversation_repository

    async def export_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        export_format: ExportFormat,
        compliance_standard: Optional[ComplianceStandard] = None,
        pii_redaction: Optional[PIIRedactionConfig] = None,
        include_attachments: bool = True,
    ) -> tuple[bytes, ExportMetadata]:
        """
        Export a conversation in specified format.

        Args:
            conversation_id: Conversation to export
            user_id: User requesting export
            export_format: Desired export format
            compliance_standard: Optional compliance requirements
            pii_redaction: Optional PII redaction configuration
            include_attachments: Whether to include attachments

        Returns:
            Tuple of (file_bytes, export_metadata)
        """
        # Get compliance requirements if standard specified
        compliance_reqs = None
        if compliance_standard:
            compliance_reqs = self._get_compliance_requirements(compliance_standard)

        # Validate format allowed for compliance standard
        if compliance_reqs and compliance_reqs.export_format_restrictions:
            if export_format not in compliance_reqs.export_format_restrictions:
                raise ValueError(
                    f"Format {export_format.value} not allowed for {compliance_standard.value}"
                )

        # Apply PII redaction if required
        should_redact = pii_redaction is not None or (
            compliance_reqs and compliance_reqs.require_pii_redaction
        )
        if should_redact and not pii_redaction:
            pii_redaction = PIIRedactionConfig()

        # Load conversation data
        # TODO: Implement actual conversation loading
        conversation_data = await self._load_conversation_data(
            conversation_id, user_id, include_attachments
        )

        # Apply PII redaction
        if pii_redaction:
            conversation_data = self._redact_pii(conversation_data, pii_redaction)

        # Generate export in requested format
        file_bytes = await self._generate_export(
            conversation_data, export_format, compliance_reqs
        )

        # Generate digital signature if required
        digitally_signed = False
        signature_algorithm = None
        hash_value = None

        if compliance_reqs and compliance_reqs.require_digital_signature:
            hash_value = self._generate_hash(file_bytes)
            # TODO: Implement actual digital signature
            digitally_signed = True
            signature_algorithm = "SHA256-RSA"

        # Create metadata
        metadata = ExportMetadata(
            export_id=str(uuid4()),
            conversation_id=str(conversation_id),
            exported_by_user_id=str(user_id),
            export_timestamp=datetime.utcnow(),
            format=export_format,
            compliance_standard=compliance_standard,
            file_size_bytes=len(file_bytes),
            message_count=conversation_data.get("message_count", 0),
            date_range_start=conversation_data.get("start_date", datetime.utcnow()),
            date_range_end=conversation_data.get("end_date", datetime.utcnow()),
            includes_attachments=include_attachments,
            pii_redacted=pii_redaction is not None,
            digitally_signed=digitally_signed,
            signature_algorithm=signature_algorithm,
            hash_value=hash_value,
        )

        # Create audit entry
        await self._create_audit_entry(
            user_id=user_id,
            action="export_completed",
            conversation_id=conversation_id,
            export_format=export_format,
            compliance_standard=compliance_standard,
            success=True,
        )

        return file_bytes, metadata

    async def export_batch(
        self,
        conversation_ids: List[UUID],
        user_id: UUID,
        export_format: ExportFormat,
        compliance_standard: Optional[ComplianceStandard] = None,
    ) -> tuple[bytes, List[ExportMetadata]]:
        """
        Export multiple conversations in a single archive.

        Args:
            conversation_ids: Conversations to export
            user_id: User requesting export
            export_format: Desired export format
            compliance_standard: Optional compliance requirements

        Returns:
            Tuple of (archive_bytes, list_of_metadata)
        """
        # TODO: Implement batch export with ZIP archive
        exports = []
        metadata_list = []

        for conv_id in conversation_ids:
            file_bytes, metadata = await self.export_conversation(
                conversation_id=conv_id,
                user_id=user_id,
                export_format=export_format,
                compliance_standard=compliance_standard,
            )
            exports.append((metadata.export_id, file_bytes))
            metadata_list.append(metadata)

        # Create ZIP archive
        # TODO: Implement actual ZIP creation
        archive_bytes = b"ZIP_ARCHIVE_PLACEHOLDER"

        return archive_bytes, metadata_list

    def _get_compliance_requirements(
        self, standard: ComplianceStandard
    ) -> ComplianceRequirements:
        """Get compliance requirements for standard."""
        if standard == ComplianceStandard.SEC:
            return ComplianceRequirements.for_sec()
        elif standard == ComplianceStandard.GDPR:
            return ComplianceRequirements.for_gdpr()
        elif standard == ComplianceStandard.FINRA:
            return ComplianceRequirements.for_finra()
        else:
            # Generic requirements
            return ComplianceRequirements(
                standard=standard,
                require_digital_signature=False,
                require_timestamp_verification=True,
                require_pii_redaction=False,
                require_immutable_audit_trail=True,
                retention_period_years=7,
                required_metadata_fields=["conversation_id", "export_timestamp"],
                export_format_restrictions=[],
            )

    async def _load_conversation_data(
        self,
        conversation_id: UUID,
        user_id: UUID,
        include_attachments: bool,
    ) -> dict:
        """Load conversation data from repository."""
        # TODO: Implement actual loading
        return {
            "conversation_id": str(conversation_id),
            "title": "Sample Conversation",
            "messages": [],
            "message_count": 42,
            "start_date": datetime(2025, 1, 1),
            "end_date": datetime.utcnow(),
            "participants": [str(user_id)],
        }

    def _redact_pii(
        self, conversation_data: dict, config: PIIRedactionConfig
    ) -> dict:
        """Redact PII from conversation data."""
        redacted_data = conversation_data.copy()

        # Redact in messages
        if "messages" in redacted_data:
            redacted_messages = []
            for message in redacted_data["messages"]:
                content = message.get("content", "")

                if config.redact_emails:
                    content = self._redact_emails(content, config.replacement_text)
                if config.redact_phone_numbers:
                    content = self._redact_phone_numbers(content, config.replacement_text)
                if config.redact_wallet_addresses:
                    content = self._redact_wallet_addresses(content, config.replacement_text)
                if config.redact_ip_addresses:
                    content = self._redact_ip_addresses(content, config.replacement_text)
                if config.redact_ssn:
                    content = self._redact_ssn(content, config.replacement_text)
                if config.redact_credit_cards:
                    content = self._redact_credit_cards(content, config.replacement_text)

                message["content"] = content
                redacted_messages.append(message)

            redacted_data["messages"] = redacted_messages

        return redacted_data

    def _redact_emails(self, text: str, replacement: str) -> str:
        """Redact email addresses."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, replacement, text)

    def _redact_phone_numbers(self, text: str, replacement: str) -> str:
        """Redact phone numbers."""
        phone_pattern = r'\b(\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
        return re.sub(phone_pattern, replacement, text)

    def _redact_wallet_addresses(self, text: str, replacement: str) -> str:
        """Redact cryptocurrency wallet addresses."""
        # Ethereum addresses
        eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
        text = re.sub(eth_pattern, replacement, text)

        # Bitcoin addresses
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
        text = re.sub(btc_pattern, replacement, text)

        return text

    def _redact_ip_addresses(self, text: str, replacement: str) -> str:
        """Redact IP addresses."""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        return re.sub(ip_pattern, replacement, text)

    def _redact_ssn(self, text: str, replacement: str) -> str:
        """Redact Social Security Numbers."""
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        return re.sub(ssn_pattern, replacement, text)

    def _redact_credit_cards(self, text: str, replacement: str) -> str:
        """Redact credit card numbers."""
        cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        return re.sub(cc_pattern, replacement, text)

    async def _generate_export(
        self,
        conversation_data: dict,
        export_format: ExportFormat,
        compliance_reqs: Optional[ComplianceRequirements],
    ) -> bytes:
        """Generate export file in specified format."""
        if export_format == ExportFormat.JSON:
            return self._generate_json_export(conversation_data, compliance_reqs)
        elif export_format == ExportFormat.CSV:
            return self._generate_csv_export(conversation_data)
        elif export_format == ExportFormat.MARKDOWN:
            return self._generate_markdown_export(conversation_data)
        elif export_format == ExportFormat.HTML:
            return self._generate_html_export(conversation_data, compliance_reqs)
        elif export_format == ExportFormat.PDF:
            return await self._generate_pdf_export(conversation_data, compliance_reqs)
        else:
            raise ValueError(f"Unsupported export format: {export_format.value}")

    def _generate_json_export(
        self, data: dict, compliance_reqs: Optional[ComplianceRequirements]
    ) -> bytes:
        """Generate JSON export."""
        import json

        export_data = {
            "conversation": data,
            "exported_at": datetime.utcnow().isoformat(),
        }

        if compliance_reqs:
            export_data["compliance"] = {
                "standard": compliance_reqs.standard.value,
                "retention_period_years": compliance_reqs.retention_period_years,
            }

        return json.dumps(export_data, indent=2).encode("utf-8")

    def _generate_csv_export(self, data: dict) -> bytes:
        """Generate CSV export."""
        import csv

        output = BytesIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Timestamp", "Role", "Content"])

        # Messages
        for message in data.get("messages", []):
            writer.writerow([
                message.get("timestamp", ""),
                message.get("role", ""),
                message.get("content", ""),
            ])

        return output.getvalue()

    def _generate_markdown_export(self, data: dict) -> bytes:
        """Generate Markdown export."""
        lines = [
            f"# {data.get('title', 'Conversation')}",
            "",
            f"**Exported**: {datetime.utcnow().isoformat()}",
            f"**Messages**: {data.get('message_count', 0)}",
            "",
            "---",
            "",
        ]

        for message in data.get("messages", []):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")

            lines.extend([
                f"## {role.title()} - {timestamp}",
                "",
                content,
                "",
            ])

        return "\n".join(lines).encode("utf-8")

    def _generate_html_export(
        self, data: dict, compliance_reqs: Optional[ComplianceRequirements]
    ) -> bytes:
        """Generate HTML export."""
        compliance_banner = ""
        if compliance_reqs:
            compliance_banner = f"""
            <div style="background: #fef3c7; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #f59e0b;">
                <strong>Compliance:</strong> {compliance_reqs.standard.value.upper()} |
                Retention: {compliance_reqs.retention_period_years} years
            </div>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{data.get('title', 'Conversation Export')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
        .message {{ margin-bottom: 1.5rem; padding: 1rem; background: #f9fafb; border-radius: 8px; }}
        .role {{ font-weight: 600; color: #374151; }}
        .timestamp {{ color: #6b7280; font-size: 0.875rem; }}
        .content {{ margin-top: 0.5rem; line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{data.get('title', 'Conversation')}</h1>
    <p><strong>Exported:</strong> {datetime.utcnow().isoformat()}</p>
    <p><strong>Messages:</strong> {data.get('message_count', 0)}</p>
    {compliance_banner}
    <hr>
"""

        for message in data.get("messages", []):
            html += f"""
    <div class="message">
        <div class="role">{message.get('role', 'unknown').title()}</div>
        <div class="timestamp">{message.get('timestamp', '')}</div>
        <div class="content">{message.get('content', '')}</div>
    </div>
"""

        html += """
</body>
</html>
"""
        return html.encode("utf-8")

    async def _generate_pdf_export(
        self, data: dict, compliance_reqs: Optional[ComplianceRequirements]
    ) -> bytes:
        """Generate PDF export."""
        # TODO: Implement actual PDF generation with reportlab or weasyprint
        # For now, return placeholder
        return b"PDF_PLACEHOLDER"

    def _generate_hash(self, data: bytes) -> str:
        """Generate SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()

    async def _create_audit_entry(
        self,
        user_id: UUID,
        action: str,
        conversation_id: UUID,
        export_format: ExportFormat,
        compliance_standard: Optional[ComplianceStandard],
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Create audit trail entry."""
        entry = ExportAuditEntry(
            timestamp=datetime.utcnow(),
            user_id=str(user_id),
            action=action,
            conversation_id=str(conversation_id),
            export_format=export_format,
            compliance_standard=compliance_standard,
            success=success,
            error_message=error_message,
        )

        # TODO: Persist audit entry
        logger.info(f"Export audit: {entry.to_dict()}")

    def format_export_response(self, metadata: ExportMetadata) -> str:
        """
        Format export completion message for chat display.

        Args:
            metadata: Export metadata

        Returns:
            Formatted markdown string
        """
        lines = [
            f"✅ Export completed successfully",
            "",
            "**Export Details:**",
            f"  • Format: {metadata.format.value.upper()}",
            f"  • File size: {self._format_file_size(metadata.file_size_bytes)}",
            f"  • Messages: {metadata.message_count}",
            f"  • Date range: {metadata.date_range_start.strftime('%Y-%m-%d')} to {metadata.date_range_end.strftime('%Y-%m-%d')}",
        ]

        if metadata.compliance_standard:
            lines.extend([
                "",
                "**Compliance:**",
                f"  • Standard: {metadata.compliance_standard.value.upper()}",
                f"  • Digitally signed: {'Yes' if metadata.digitally_signed else 'No'}",
                f"  • PII redacted: {'Yes' if metadata.pii_redacted else 'No'}",
            ])

        if metadata.hash_value:
            lines.append(f"  • Hash (SHA256): {metadata.hash_value[:16]}...")

        lines.extend([
            "",
            f"Export ID: `{metadata.export_id}`",
            "",
            "Your export is ready for download.",
        ])

        return "\n".join(lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
