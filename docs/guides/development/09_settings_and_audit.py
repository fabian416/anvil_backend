"""
Anvil Platform - SQLAlchemy Models
Section 9: Settings and Audit Log Models

These models handle system configuration settings and comprehensive audit logging
for compliance and security.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from .base_and_users import Base


# ============================================================================
# Enums
# ============================================================================


class SettingScope(str, enum.Enum):
    """Setting scope/category"""

    GLOBAL = "global"
    SECURITY = "security"
    PAYMENT = "payment"
    AI = "ai"
    BLOCKCHAIN = "blockchain"
    NOTIFICATION = "notification"


class SettingDataType(str, enum.Enum):
    """Setting data type"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


# ============================================================================
# Settings Models
# ============================================================================


class Setting(Base):
    """
    System configuration settings

    Stores all platform-wide configuration parameters including limits,
    API keys, feature flags, and operational parameters.
    """

    __tablename__ = "settings"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Setting Identification
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique setting key (e.g., 'max_daily_trade_limit')",
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Setting value (string representation)"
    )

    # Metadata
    scope: Mapped[str] = mapped_column(
        SQLEnum(SettingScope), nullable=False, index=True, comment="Setting category"
    )
    data_type: Mapped[str] = mapped_column(
        SQLEnum(SettingDataType),
        nullable=False,
        default=SettingDataType.STRING,
        comment="Data type for validation",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Human-readable description"
    )

    # Security
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Contains sensitive data (API keys, passwords)",
    )
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Value is encrypted in database"
    )

    # Validation
    validation_rules: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Validation rules (min, max, regex, etc.)"
    )
    default_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Default value if setting is not set"
    )

    # Audit Trail
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Email of admin who last updated"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    # Indexes
    __table_args__ = (
        Index("idx_setting_scope", "scope"),
        Index("idx_setting_key", "key"),
    )

    def __repr__(self) -> str:
        if self.is_sensitive:
            return f"<Setting(id={self.id}, key='{self.key}', value='***REDACTED***')>"
        return (
            f"<Setting(id={self.id}, key='{self.key}', value='{self.value[:50]}...')>"
        )

    @property
    def display_value(self) -> str:
        """Get display-safe value (masks sensitive data)"""
        if self.is_sensitive:
            if len(self.value) > 8:
                return self.value[:4] + "•" * 8 + self.value[-4:]
            else:
                return "•" * 8
        return self.value


# ============================================================================
# Audit Log Models
# ============================================================================


class AuditLog(Base):
    """
    Comprehensive audit trail

    Records all administrative actions, user activities, and system events
    for compliance, security, and troubleshooting.
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Actor Information
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (null for system actions)",
    )
    actor_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Email of user (cached for deleted users)",
    )
    actor_role: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Role of actor at time of action (0=ADMIN, 1=AUDITOR, 2=CLIENT)",
    )

    # Action Details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (e.g., 'user_created', 'kyc_approved', 'transaction_failed')",
    )
    action_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Action category (e.g., 'user_management', 'transactions', 'configuration')",
    )

    # Target Entity
    entity: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Entity type affected (e.g., 'user', 'transaction', 'setting')",
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="ID of affected entity"
    )

    # Payload
    payload_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Detailed action data (before/after states, parameters, etc.)",
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, index=True, comment="IPv4 or IPv6 address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Browser/client user agent"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="Request ID for correlation"
    )

    # Geolocation
    geo_country: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True, comment="ISO country code"
    )
    geo_city: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="City name"
    )

    # Result
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether action succeeded"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if action failed"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    # Indexes
    __table_args__ = (
        Index("idx_audit_actor", "actor_user_id", "created_at"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity", "entity", "entity_id"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_ip", "ip_address"),
        Index("idx_audit_action_category", "action_category"),
        Index("idx_audit_success", "success"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, actor={self.actor_email}, action='{self.action}', entity='{self.entity}', entity_id='{self.entity_id}')>"

    @property
    def actor_role_label(self) -> Optional[str]:
        """Get human-readable actor role"""
        if self.actor_role is None:
            return "SYSTEM"
        role_map = {0: "ADMIN", 1: "AUDITOR", 2: "CLIENT"}
        return role_map.get(self.actor_role, "UNKNOWN")


class SecurityEvent(Base):
    """
    Security-specific event log

    Tracks security-sensitive events like failed logins, suspicious activities,
    and potential threats.
    """

    __tablename__ = "security_events"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User (if applicable)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Event Details
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Event type (e.g., 'failed_login', 'suspicious_activity', 'brute_force')",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="'low', 'medium', 'high', 'critical'",
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Event description"
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, index=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Details
    details_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON: Additional event details"
    )

    # Response
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Action taken (e.g., 'account_locked', 'ip_blocked', 'alert_sent')",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="When event was resolved/cleared"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    # Indexes
    __table_args__ = (
        Index("idx_security_user", "user_id"),
        Index("idx_security_type", "event_type"),
        Index("idx_security_severity", "severity"),
        Index("idx_security_ip", "ip_address"),
        Index("idx_security_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SecurityEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"

    @property
    def is_resolved(self) -> bool:
        """Check if event has been resolved"""
        return self.resolved_at is not None

    @property
    def is_critical(self) -> bool:
        """Check if event is critical severity"""
        return self.severity == "critical"


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from .base_and_users import Base

    DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/anvil"
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)

    print("✅ Settings and Audit Log tables created successfully!")
    print("\nTables created:")
    print("- settings")
    print("- audit_logs")
    print("- security_events")
