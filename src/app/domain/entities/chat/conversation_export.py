"""
Conversation Export domain entity.

Enterprise-grade conversation export with compliance support.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)


@dataclass
class ConversationExport:
    """
    Conversation export entity.

    Represents an export request and its processing status.
    Supports multiple formats with compliance and PII redaction.
    """

    id: UUID
    conversation_id: UUID
    user_id: UUID
    format: ExportFormat
    status: str  # "pending", "processing", "completed", "failed"

    # Configuration
    include_metadata: bool = True
    include_timestamps: bool = True
    include_agent_names: bool = True
    redact_pii: bool = False
    pii_redaction_config: Optional[PIIRedactionConfig] = None
    compliance_standard: Optional[ComplianceStandard] = None

    # Output
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Timestamps
    requested_at: datetime = None  # type: ignore
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.requested_at is None:
            self.requested_at = datetime.utcnow()

    def is_pending(self) -> bool:
        """Check if export is pending."""
        return self.status == "pending"

    def is_processing(self) -> bool:
        """Check if export is being processed."""
        return self.status == "processing"

    def is_completed(self) -> bool:
        """Check if export is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if export failed."""
        return self.status == "failed"

    def is_expired(self) -> bool:
        """Check if download URL has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def mark_as_processing(self) -> None:
        """Mark export as being processed."""
        self.status = "processing"

    def mark_as_completed(
        self,
        file_path: str,
        file_size_bytes: int,
        download_url: str,
        expires_at: datetime,
    ) -> None:
        """
        Mark export as completed.

        Args:
            file_path: Path to exported file
            file_size_bytes: File size in bytes
            download_url: URL for downloading
            expires_at: Expiration timestamp
        """
        self.status = "completed"
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes
        self.download_url = download_url
        self.expires_at = expires_at
        self.completed_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """
        Mark export as failed.

        Args:
            error_message: Error description
        """
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "format": self.format.value,
            "status": self.status,
            "include_metadata": self.include_metadata,
            "include_timestamps": self.include_timestamps,
            "include_agent_names": self.include_agent_names,
            "redact_pii": self.redact_pii,
            "compliance_standard": (
                self.compliance_standard.value if self.compliance_standard else None
            ),
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "download_url": self.download_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
