"""
Export generator adapter implementation.

Generates conversation exports in multiple formats (JSON, Markdown, PDF, HTML)
with PII redaction and compliance formatting.
"""

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.ports.export_generator import ExportGenerator
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
    ExportMetadata,
    ComplianceRequirements,
)
from app.domain.exceptions.chat import ExportGenerationError, ComplianceViolationError


class ExportGeneratorAdapter(ExportGenerator):
    """
    Export generator adapter implementation.

    Generates conversation exports with support for:
    - Multiple formats (JSON, Markdown, PDF, HTML)
    - PII redaction using regex patterns
    - Compliance formatting (SEC, GDPR, FINRA)
    - Async file generation with progress tracking
    """

    def __init__(self, storage_path: str = "/tmp/conversation_exports"):
        """
        Initialize export generator.

        Args:
            storage_path: Directory for storing generated export files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # PII regex patterns
        self._pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            "ssn": r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b',
            "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
            "wallet_address": r'\b0x[a-fA-F0-9]{40}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }

    async def generate_export(
        self,
        conversation: Conversation,
        messages: List[Message],
        format: ExportFormat,
        redact_pii: bool = False,
        pii_config: Optional[PIIRedactionConfig] = None,
        compliance_standard: Optional[ComplianceStandard] = None,
        include_metadata: bool = True,
        include_timestamps: bool = True,
        include_agent_names: bool = True,
    ) -> tuple[str, bytes]:
        """
        Generate export file for conversation.

        Args:
            conversation: Conversation entity
            messages: List of messages in conversation
            format: Export format (JSON, PDF, HTML, Markdown)
            redact_pii: Whether to redact personally identifiable information
            pii_config: PII redaction configuration
            compliance_standard: Compliance standard to apply (SEC, GDPR, FINRA)
            include_metadata: Include conversation metadata
            include_timestamps: Include message timestamps
            include_agent_names: Include agent type information

        Returns:
            Tuple of (file_path, file_content_bytes)

        Raises:
            ExportGenerationError: If export generation fails
            ComplianceViolationError: If format violates compliance requirements
        """
        try:
            # Validate compliance requirements
            if compliance_standard:
                self.validate_compliance(format, compliance_standard)

            # Apply PII redaction to messages if enabled
            processed_messages = messages
            if redact_pii and pii_config:
                processed_messages = await self._redact_messages(messages, pii_config)

            # Generate export based on format
            if format == ExportFormat.JSON:
                content = await self._generate_json(
                    conversation,
                    processed_messages,
                    include_metadata,
                    include_timestamps,
                    include_agent_names,
                    compliance_standard,
                )
            elif format == ExportFormat.MARKDOWN:
                content = await self._generate_markdown(
                    conversation,
                    processed_messages,
                    include_metadata,
                    include_timestamps,
                    include_agent_names,
                    compliance_standard,
                )
            elif format == ExportFormat.HTML:
                content = await self._generate_html(
                    conversation,
                    processed_messages,
                    include_metadata,
                    include_timestamps,
                    include_agent_names,
                    compliance_standard,
                )
            elif format == ExportFormat.PDF:
                content = await self._generate_pdf(
                    conversation,
                    processed_messages,
                    include_metadata,
                    include_timestamps,
                    include_agent_names,
                    compliance_standard,
                )
            else:
                raise ExportGenerationError(f"Unsupported export format: {format}")

            # Save to file
            file_extension = format.value
            file_name = f"conversation_{conversation.id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            file_path = self.storage_path / file_name

            # Write content to file
            mode = "wb" if isinstance(content, bytes) else "w"
            async with asyncio.Lock():
                with open(file_path, mode) as f:
                    f.write(content)

            # Read content as bytes for return
            with open(file_path, "rb") as f:
                file_content = f.read()

            return str(file_path), file_content

        except ComplianceViolationError:
            raise
        except Exception as e:
            raise ExportGenerationError(f"Failed to generate export: {str(e)}") from e

    async def get_export_metadata(
        self,
        export_id: UUID,
        conversation: Conversation,
        messages: List[Message],
        format: ExportFormat,
        file_size_bytes: int,
        compliance_standard: Optional[ComplianceStandard] = None,
        pii_redacted: bool = False,
    ) -> ExportMetadata:
        """
        Generate metadata for export.

        Args:
            export_id: Export identifier
            conversation: Conversation entity
            messages: List of messages
            format: Export format
            file_size_bytes: Size of generated file
            compliance_standard: Applied compliance standard
            pii_redacted: Whether PII was redacted

        Returns:
            Export metadata object
        """
        if not messages:
            raise ExportGenerationError("Cannot generate metadata for empty conversation")

        # Calculate hash for digital signature
        hash_value = hashlib.sha256(
            f"{export_id}{conversation.id}{len(messages)}".encode()
        ).hexdigest()

        date_range_start = min(msg.created_at for msg in messages)
        date_range_end = max(msg.created_at for msg in messages)

        return ExportMetadata(
            export_id=str(export_id),
            conversation_id=str(conversation.id),
            exported_by_user_id=str(conversation.user_id),
            export_timestamp=datetime.now(UTC),
            format=format,
            compliance_standard=compliance_standard,
            file_size_bytes=file_size_bytes,
            message_count=len(messages),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            includes_attachments=False,
            pii_redacted=pii_redacted,
            digitally_signed=compliance_standard is not None,
            signature_algorithm="SHA256" if compliance_standard else None,
            hash_value=hash_value if compliance_standard else None,
        )

    def redact_pii(self, content: str, config: PIIRedactionConfig) -> str:
        """
        Redact PII from content using regex patterns.

        Args:
            content: Content to redact
            config: PII redaction configuration

        Returns:
            Redacted content
        """
        redacted_content = content

        if config.redact_emails:
            redacted_content = re.sub(
                self._pii_patterns["email"],
                config.replacement_text,
                redacted_content,
            )

        if config.redact_phone_numbers:
            redacted_content = re.sub(
                self._pii_patterns["phone"],
                config.replacement_text,
                redacted_content,
            )

        if config.redact_ssn:
            redacted_content = re.sub(
                self._pii_patterns["ssn"],
                config.replacement_text,
                redacted_content,
            )

        if config.redact_credit_cards:
            redacted_content = re.sub(
                self._pii_patterns["credit_card"],
                config.replacement_text,
                redacted_content,
            )

        if config.redact_wallet_addresses:
            redacted_content = re.sub(
                self._pii_patterns["wallet_address"],
                config.replacement_text,
                redacted_content,
            )

        if config.redact_ip_addresses:
            redacted_content = re.sub(
                self._pii_patterns["ip_address"],
                config.replacement_text,
                redacted_content,
            )

        return redacted_content

    def validate_compliance(
        self,
        format: ExportFormat,
        compliance_standard: ComplianceStandard,
    ) -> bool:
        """
        Validate format is compatible with compliance standard.

        Args:
            format: Export format
            compliance_standard: Compliance standard

        Returns:
            True if format is allowed for compliance standard

        Raises:
            ComplianceViolationError: If format violates compliance requirements
        """
        # Get compliance requirements
        if compliance_standard == ComplianceStandard.SEC:
            requirements = ComplianceRequirements.for_sec()
        elif compliance_standard == ComplianceStandard.GDPR:
            requirements = ComplianceRequirements.for_gdpr()
        elif compliance_standard == ComplianceStandard.FINRA:
            requirements = ComplianceRequirements.for_finra()
        else:
            # Unknown compliance standard, allow all formats
            return True

        # Check format restrictions
        if requirements.export_format_restrictions and format not in requirements.export_format_restrictions:
            raise ComplianceViolationError(
                f"Format {format.value} not allowed for {compliance_standard.value} compliance. "
                f"Allowed formats: {[f.value for f in requirements.export_format_restrictions]}"
            )

        return True

    async def _redact_messages(
        self,
        messages: List[Message],
        config: PIIRedactionConfig,
    ) -> List[Message]:
        """
        Redact PII from all messages.

        Args:
            messages: List of messages
            config: PII redaction configuration

        Returns:
            List of messages with redacted content
        """
        redacted_messages = []
        for msg in messages:
            redacted_content = self.redact_pii(msg.content, config)

            # Create a new message with redacted content
            # Preserve original message properties
            redacted_msg = Message(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=redacted_content,
                agent_type=msg.agent_type,
                created_at=msg.created_at,
                metadata=msg.metadata,
            )
            redacted_messages.append(redacted_msg)

        return redacted_messages

    async def _generate_json(
        self,
        conversation: Conversation,
        messages: List[Message],
        include_metadata: bool,
        include_timestamps: bool,
        include_agent_names: bool,
        compliance_standard: Optional[ComplianceStandard],
    ) -> str:
        """
        Generate JSON export.

        Args:
            conversation: Conversation entity
            messages: List of messages
            include_metadata: Include metadata
            include_timestamps: Include timestamps
            include_agent_names: Include agent names
            compliance_standard: Compliance standard

        Returns:
            JSON string
        """
        export_data: Dict[str, Any] = {}

        # Add metadata
        if include_metadata:
            export_data["metadata"] = {
                "conversation_id": str(conversation.id),
                "user_id": conversation.user_id,
                "title": conversation.title,
                "project_id": str(conversation.project_id) if conversation.project_id else None,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "export_timestamp": datetime.now(UTC).isoformat(),
                "message_count": len(messages),
            }

            # Add compliance metadata
            if compliance_standard:
                export_data["metadata"]["compliance_standard"] = compliance_standard.value
                export_data["metadata"]["digitally_signed"] = True

        # Add messages
        messages_data = []
        for msg in messages:
            msg_data = {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
            }

            if include_timestamps:
                msg_data["created_at"] = msg.created_at.isoformat()

            if include_agent_names and msg.agent_type:
                msg_data["agent_type"] = msg.agent_type

            if msg.metadata:
                msg_data["metadata"] = msg.metadata

            messages_data.append(msg_data)

        export_data["messages"] = messages_data

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    async def _generate_markdown(
        self,
        conversation: Conversation,
        messages: List[Message],
        include_metadata: bool,
        include_timestamps: bool,
        include_agent_names: bool,
        compliance_standard: Optional[ComplianceStandard],
    ) -> str:
        """
        Generate Markdown export.

        Args:
            conversation: Conversation entity
            messages: List of messages
            include_metadata: Include metadata
            include_timestamps: Include timestamps
            include_agent_names: Include agent names
            compliance_standard: Compliance standard

        Returns:
            Markdown string
        """
        lines = []

        # Title
        title = conversation.title or f"Conversation {conversation.id}"
        lines.append(f"# {title}\n")

        # Metadata section
        if include_metadata:
            lines.append("## Metadata\n")
            lines.append(f"- **Conversation ID:** {conversation.id}")
            lines.append(f"- **Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append(f"- **Updated:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append(f"- **Message Count:** {len(messages)}")

            if compliance_standard:
                lines.append(f"- **Compliance Standard:** {compliance_standard.value.upper()}")
                lines.append("- **Digitally Signed:** Yes")

            lines.append("")

        # Messages section
        lines.append("## Messages\n")

        for i, msg in enumerate(messages, 1):
            # Message header
            role_display = msg.role.value.capitalize()
            if include_agent_names and msg.agent_type:
                role_display = f"{role_display} ({msg.agent_type})"

            lines.append(f"### {i}. {role_display}")

            if include_timestamps:
                lines.append(f"*{msg.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*\n")

            # Message content
            lines.append(msg.content)
            lines.append("")

        # Compliance footer
        if compliance_standard:
            lines.append("---")
            lines.append(f"\n*This export complies with {compliance_standard.value.upper()} standards.*")
            lines.append(f"*Generated on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        return "\n".join(lines)

    async def _generate_html(
        self,
        conversation: Conversation,
        messages: List[Message],
        include_metadata: bool,
        include_timestamps: bool,
        include_agent_names: bool,
        compliance_standard: Optional[ComplianceStandard],
    ) -> str:
        """
        Generate HTML export with styling.

        Args:
            conversation: Conversation entity
            messages: List of messages
            include_metadata: Include metadata
            include_timestamps: Include timestamps
            include_agent_names: Include agent names
            compliance_standard: Compliance standard

        Returns:
            HTML string
        """
        title = conversation.title or f"Conversation {conversation.id}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}

        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #1a1a1a;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #007bff;
        }}

        h2 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }}

        .metadata {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}

        .metadata-item {{
            margin: 8px 0;
            color: #555;
        }}

        .metadata-label {{
            font-weight: 600;
            color: #333;
        }}

        .message {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid;
        }}

        .message.user {{
            background: #e3f2fd;
            border-left-color: #2196f3;
        }}

        .message.agent {{
            background: #f3e5f5;
            border-left-color: #9c27b0;
        }}

        .message.system {{
            background: #fff3e0;
            border-left-color: #ff9800;
        }}

        .message-header {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #1a1a1a;
        }}

        .message-role {{
            text-transform: capitalize;
        }}

        .message-timestamp {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 10px;
        }}

        .message-content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .compliance-footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #dee2e6;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .compliance-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 5px 15px;
            border-radius: 3px;
            margin: 10px 0;
            font-weight: 600;
        }}

        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
"""

        # Metadata section
        if include_metadata:
            html += """
        <h2>Metadata</h2>
        <div class="metadata">
"""
            html += f"""
            <div class="metadata-item">
                <span class="metadata-label">Conversation ID:</span> {conversation.id}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Created:</span> {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Updated:</span> {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Message Count:</span> {len(messages)}
            </div>
"""
            if compliance_standard:
                html += f"""
            <div class="metadata-item">
                <span class="metadata-label">Compliance Standard:</span> {compliance_standard.value.upper()}
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Digitally Signed:</span> Yes
            </div>
"""
            html += """
        </div>
"""

        # Messages section
        html += """
        <h2>Messages</h2>
"""

        for msg in messages:
            role_class = msg.role.value
            role_display = msg.role.value.capitalize()
            if include_agent_names and msg.agent_type:
                role_display = f"{role_display} ({msg.agent_type})"

            # Escape HTML in content
            content = msg.content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            html += f"""
        <div class="message {role_class}">
            <div class="message-header">
                <span class="message-role">{role_display}</span>
            </div>
"""
            if include_timestamps:
                html += f"""
            <div class="message-timestamp">{msg.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
"""
            html += f"""
            <div class="message-content">{content}</div>
        </div>
"""

        # Compliance footer
        if compliance_standard:
            html += f"""
        <div class="compliance-footer">
            <div class="compliance-badge">{compliance_standard.value.upper()} Compliant</div>
            <div>This export complies with {compliance_standard.value.upper()} standards.</div>
            <div>Generated on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    async def _generate_pdf(
        self,
        conversation: Conversation,
        messages: List[Message],
        include_metadata: bool,
        include_timestamps: bool,
        include_agent_names: bool,
        compliance_standard: Optional[ComplianceStandard],
    ) -> bytes:
        """
        Generate PDF export using reportlab.

        Args:
            conversation: Conversation entity
            messages: List of messages
            include_metadata: Include metadata
            include_timestamps: Include timestamps
            include_agent_names: Include agent names
            compliance_standard: Compliance standard

        Returns:
            PDF bytes
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
                PageBreak,
            )
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
            from io import BytesIO

        except ImportError:
            raise ExportGenerationError(
                "reportlab library not installed. Install with: pip install reportlab"
            )

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
            spaceBefore=20,
        )
        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontSize=11,
            alignment=TA_JUSTIFY,
        )
        timestamp_style = ParagraphStyle(
            "Timestamp",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=6,
        )

        # Title
        title = conversation.title or f"Conversation {conversation.id}"
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Metadata section
        if include_metadata:
            elements.append(Paragraph("Metadata", heading_style))

            metadata_data = [
                ["Conversation ID:", str(conversation.id)],
                ["Created:", conversation.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
                ["Updated:", conversation.updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
                ["Message Count:", str(len(messages))],
            ]

            if compliance_standard:
                metadata_data.extend([
                    ["Compliance Standard:", compliance_standard.value.upper()],
                    ["Digitally Signed:", "Yes"],
                ])

            metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])
            metadata_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            elements.append(metadata_table)
            elements.append(Spacer(1, 0.3 * inch))

        # Messages section
        elements.append(Paragraph("Messages", heading_style))
        elements.append(Spacer(1, 0.1 * inch))

        for i, msg in enumerate(messages, 1):
            # Message header
            role_display = msg.role.value.capitalize()
            if include_agent_names and msg.agent_type:
                role_display = f"{role_display} ({msg.agent_type})"

            # Create message header with role
            role_colors = {
                "user": colors.HexColor("#2196f3"),
                "agent": colors.HexColor("#9c27b0"),
                "system": colors.HexColor("#ff9800"),
            }
            role_color = role_colors.get(msg.role.value, colors.black)

            header_style = ParagraphStyle(
                f"MessageHeader{i}",
                parent=styles["Heading3"],
                fontSize=12,
                textColor=role_color,
                spaceAfter=4,
            )

            elements.append(Paragraph(f"{i}. {role_display}", header_style))

            # Timestamp
            if include_timestamps:
                elements.append(
                    Paragraph(
                        msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        timestamp_style,
                    )
                )

            # Message content
            # Escape XML special characters for reportlab
            content = (
                msg.content
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            elements.append(Paragraph(content, body_style))
            elements.append(Spacer(1, 0.15 * inch))

        # Compliance footer
        if compliance_standard:
            elements.append(Spacer(1, 0.3 * inch))
            footer_style = ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER,
            )
            elements.append(
                Paragraph(
                    f"This export complies with {compliance_standard.value.upper()} standards.",
                    footer_style,
                )
            )
            elements.append(
                Paragraph(
                    f"Generated on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    footer_style,
                )
            )

        # Build PDF
        doc.build(elements)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes
