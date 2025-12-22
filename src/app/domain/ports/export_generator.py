"""
Export generator port for conversation exports.

Domain-defined interface for generating conversation exports in multiple formats.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
    ExportMetadata,
)


class ExportGenerator(ABC):
    """
    Port for generating conversation exports.

    Abstracts export generation in multiple formats with compliance
    and PII redaction support.
    """

    @abstractmethod
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
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def redact_pii(
        self,
        content: str,
        config: PIIRedactionConfig,
    ) -> str:
        """
        Redact PII from content using regex patterns.

        Args:
            content: Content to redact
            config: PII redaction configuration

        Returns:
            Redacted content
        """
        pass

    @abstractmethod
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
        pass
