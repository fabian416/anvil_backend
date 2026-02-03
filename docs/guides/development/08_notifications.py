"""
Anvil Platform - SQLAlchemy Models
Section 8: Notification Models

These models handle all types of notifications: push, email, SMS, and in-app.
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


class NotificationType(str, enum.Enum):
    """Notification type categories"""

    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"
    KYC_APPROVED = "kyc_approved"
    KYC_REJECTED = "kyc_rejected"
    ACCOUNT_SUSPENDED = "account_suspended"
    SAVE_EXECUTED = "save_executed"
    SAVE_FAILED = "save_failed"
    EARN_DEPOSIT_CONFIRMED = "earn_deposit_confirmed"
    EARN_WITHDRAWAL_CONFIRMED = "earn_withdrawal_confirmed"
    PERP_LIQUIDATION_WARNING = "perp_liquidation_warning"
    PERP_POSITION_CLOSED = "perp_position_closed"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_FAILED = "payment_failed"
    SECURITY_ALERT = "security_alert"
    PRICE_ALERT = "price_alert"
    GENERAL = "general"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""

    PUSH = "push"  # Firebase Cloud Messaging
    EMAIL = "email"  # SendGrid
    SMS = "sms"  # Twilio
    IN_APP = "in_app"  # In-app notifications


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# Notification Models
# ============================================================================


class Notification(Base):
    """
    User notifications across all channels

    Tracks all notifications sent to users including status, delivery,
    and read receipts.
    """

    __tablename__ = "notifications"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification Classification
    type: Mapped[str] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
        index=True,
        comment="Notification type/category",
    )
    channel: Mapped[str] = mapped_column(
        SQLEnum(NotificationChannel),
        nullable=False,
        index=True,
        comment="Delivery channel",
    )
    priority: Mapped[str] = mapped_column(
        SQLEnum(NotificationPriority),
        nullable=False,
        default=NotificationPriority.MEDIUM,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Notification title/subject"
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Notification body/content"
    )

    # Rich Data
    data_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: Additional data (transaction ID, amounts, links, etc.)",
    )
    action_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Deep link or URL for user action"
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Optional image/icon URL"
    )

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )

    # Channel-Specific IDs
    fcm_message_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Firebase Cloud Messaging message ID"
    )
    sendgrid_message_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="SendGrid message ID"
    )
    twilio_message_sid: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Twilio message SID"
    )

    # Delivery Information
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )

    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="When notification expires (for in-app)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    # Indexes
    __table_args__ = (
        Index("idx_notification_user_status", "user_id", "status"),
        Index("idx_notification_user_read", "user_id", "read_at"),
        Index("idx_notification_type", "type"),
        Index("idx_notification_channel", "channel"),
        Index("idx_notification_priority", "priority"),
        Index("idx_notification_created", "created_at"),
        Index("idx_notification_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', channel='{self.channel}', status='{self.status}')>"

    @property
    def is_sent(self) -> bool:
        """Check if notification was sent"""
        return self.status in [
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.READ,
        ]

    @property
    def is_delivered(self) -> bool:
        """Check if notification was delivered"""
        return self.status in [NotificationStatus.DELIVERED, NotificationStatus.READ]

    @property
    def is_read(self) -> bool:
        """Check if notification was read"""
        return self.status == NotificationStatus.READ

    @property
    def is_failed(self) -> bool:
        """Check if notification failed"""
        return self.status == NotificationStatus.FAILED

    @property
    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def time_since_sent(self) -> Optional[str]:
        """Get human-readable time since sent"""
        if not self.sent_at:
            return None

        delta = datetime.utcnow() - self.sent_at

        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"


class NotificationPreference(Base):
    """
    User notification preferences

    Allows users to control which notifications they receive and through
    which channels.
    """

    __tablename__ = "notification_preferences"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One preference set per user
        index=True,
    )

    # Channel Preferences
    push_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Enable push notifications"
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Enable email notifications"
    )
    sms_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Enable SMS notifications"
    )
    in_app_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Enable in-app notifications"
    )

    # Category Preferences
    transaction_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Transaction confirmations and failures",
    )
    security_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Security alerts and account changes",
    )
    marketing_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Marketing and promotional messages",
    )
    product_updates: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Product updates and new features",
    )
    price_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Price alerts and market updates"
    )

    # Quiet Hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Enable quiet hours (no notifications)",
    )
    quiet_hours_start: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Quiet hours start (0-23, user's timezone)"
    )
    quiet_hours_end: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Quiet hours end (0-23, user's timezone)"
    )

    # Digest Options
    daily_digest_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Receive daily summary email"
    )
    daily_digest_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Time for daily digest (0-23, user's timezone)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (Index("idx_notif_pref_user", "user_id"),)

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"

    @property
    def has_any_channel_enabled(self) -> bool:
        """Check if at least one channel is enabled"""
        return any([
            self.push_enabled,
            self.email_enabled,
            self.sms_enabled,
            self.in_app_enabled,
        ])

    def is_quiet_hours_active(self, hour: int) -> bool:
        """Check if given hour falls within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        if start < end:
            return start <= hour < end
        else:  # Crosses midnight
            return hour >= start or hour < end


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

    print("✅ Notification tables created successfully!")
    print("\nTables created:")
    print("- notifications")
    print("- notification_preferences")
