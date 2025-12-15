"""
Chat export value objects.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ExportFormat(Enum):
    """Export format options."""

    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"


class ComplianceStandard(Enum):
    """Compliance standards for exports."""

    SEC = "sec"  # Securities and Exchange Commission
    FINCEN = "fincen"  # Financial Crimes Enforcement Network
    IRS = "irs"  # Internal Revenue Service
    GDPR = "gdpr"  # General Data Protection Regulation
    SOX = "sox"  # Sarbanes-Oxley Act
    FINRA = "finra"  # Financial Industry Regulatory Authority


@dataclass(frozen=True)
class ExportMetadata:
    """Metadata for conversation export."""

    export_id: str
    conversation_id: str
    exported_by_user_id: str
    export_timestamp: datetime
    format: ExportFormat
    compliance_standard: Optional[ComplianceStandard]
    file_size_bytes: int
    message_count: int
    date_range_start: datetime
    date_range_end: datetime
    includes_attachments: bool
    pii_redacted: bool
    digitally_signed: bool
    signature_algorithm: Optional[str] = None
    hash_value: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "export_id": self.export_id,
            "conversation_id": self.conversation_id,
            "exported_by_user_id": self.exported_by_user_id,
            "export_timestamp": self.export_timestamp.isoformat(),
            "format": self.format.value,
            "compliance_standard": self.compliance_standard.value if self.compliance_standard else None,
            "file_size_bytes": self.file_size_bytes,
            "message_count": self.message_count,
            "date_range_start": self.date_range_start.isoformat(),
            "date_range_end": self.date_range_end.isoformat(),
            "includes_attachments": self.includes_attachments,
            "pii_redacted": self.pii_redacted,
            "digitally_signed": self.digitally_signed,
            "signature_algorithm": self.signature_algorithm,
            "hash_value": self.hash_value,
        }


@dataclass(frozen=True)
class PIIRedactionConfig:
    """Configuration for PII redaction."""

    redact_names: bool = True
    redact_emails: bool = True
    redact_phone_numbers: bool = True
    redact_wallet_addresses: bool = True
    redact_ip_addresses: bool = True
    redact_ssn: bool = True
    redact_credit_cards: bool = True
    replacement_text: str = "[REDACTED]"
    preserve_message_structure: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "redact_names": self.redact_names,
            "redact_emails": self.redact_emails,
            "redact_phone_numbers": self.redact_phone_numbers,
            "redact_wallet_addresses": self.redact_wallet_addresses,
            "redact_ip_addresses": self.redact_ip_addresses,
            "redact_ssn": self.redact_ssn,
            "redact_credit_cards": self.redact_credit_cards,
            "replacement_text": self.replacement_text,
            "preserve_message_structure": self.preserve_message_structure,
        }


@dataclass(frozen=True)
class ComplianceRequirements:
    """Requirements for compliance-ready exports."""

    standard: ComplianceStandard
    require_digital_signature: bool
    require_timestamp_verification: bool
    require_pii_redaction: bool
    require_immutable_audit_trail: bool
    retention_period_years: int
    required_metadata_fields: List[str]
    export_format_restrictions: List[ExportFormat]

    @classmethod
    def for_sec(cls) -> "ComplianceRequirements":
        """SEC compliance requirements."""
        return cls(
            standard=ComplianceStandard.SEC,
            require_digital_signature=True,
            require_timestamp_verification=True,
            require_pii_redaction=False,  # SEC may need unredacted data
            require_immutable_audit_trail=True,
            retention_period_years=7,
            required_metadata_fields=[
                "conversation_id",
                "export_timestamp",
                "participants",
                "date_range",
            ],
            export_format_restrictions=[ExportFormat.PDF, ExportFormat.JSON],
        )

    @classmethod
    def for_gdpr(cls) -> "ComplianceRequirements":
        """GDPR compliance requirements."""
        return cls(
            standard=ComplianceStandard.GDPR,
            require_digital_signature=False,
            require_timestamp_verification=True,
            require_pii_redaction=True,  # GDPR requires PII protection
            require_immutable_audit_trail=True,
            retention_period_years=2,  # Right to erasure
            required_metadata_fields=[
                "export_timestamp",
                "pii_redaction_applied",
                "data_subject_consent",
            ],
            export_format_restrictions=[],  # Any format allowed
        )

    @classmethod
    def for_finra(cls) -> "ComplianceRequirements":
        """FINRA compliance requirements."""
        return cls(
            standard=ComplianceStandard.FINRA,
            require_digital_signature=True,
            require_timestamp_verification=True,
            require_pii_redaction=False,
            require_immutable_audit_trail=True,
            retention_period_years=6,
            required_metadata_fields=[
                "conversation_id",
                "export_timestamp",
                "participants",
                "agent_invocations",
            ],
            export_format_restrictions=[ExportFormat.PDF, ExportFormat.JSON],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "standard": self.standard.value,
            "require_digital_signature": self.require_digital_signature,
            "require_timestamp_verification": self.require_timestamp_verification,
            "require_pii_redaction": self.require_pii_redaction,
            "require_immutable_audit_trail": self.require_immutable_audit_trail,
            "retention_period_years": self.retention_period_years,
            "required_metadata_fields": self.required_metadata_fields,
            "export_format_restrictions": [fmt.value for fmt in self.export_format_restrictions],
        }


@dataclass(frozen=True)
class ExportAuditEntry:
    """Audit trail entry for export operations."""

    timestamp: datetime
    user_id: str
    action: str  # "export_requested", "export_completed", "export_failed", "export_accessed"
    conversation_id: str
    export_format: ExportFormat
    compliance_standard: Optional[ComplianceStandard]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "conversation_id": self.conversation_id,
            "export_format": self.export_format.value,
            "compliance_standard": self.compliance_standard.value if self.compliance_standard else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
        }
