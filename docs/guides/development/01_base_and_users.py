"""
Anvil Platform - SQLAlchemy Models
Section 1: Base Configuration and User Models

Database: MySQL 8.0+
ORM: SQLAlchemy 2.0+
Python: 3.11+
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum


# ============================================================================
# Base Configuration
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Database connection configuration
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/anvil"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)


# ============================================================================
# Enums
# ============================================================================

class UserRole(enum.IntEnum):
    """User role enum"""
    ADMIN = 0
    AUDITOR = 1
    CLIENT = 2


class UserStatus(enum.IntEnum):
    """User status enum"""
    INACTIVE = 0
    ACTIVE = 1
    DELETED = 2


class KYCStatus(str, enum.Enum):
    """KYC verification status"""
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# User Models
# ============================================================================

class User(Base):
    """
    Main user table for all user types (CLIENT, ADMIN, AUDITOR)
    
    Roles:
    - 0 (ADMIN): Platform administrators with full access
    - 1 (AUDITOR): Compliance officers with read-only access
    - 2 (CLIENT): End users using the mobile app
    """
    
    __tablename__ = "users"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # External Identifiers
    uid: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="External UUID for API exposure (e.g., usr_abc123)"
    )
    privy_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Privy DID (e.g., did:privy:clk1abc123)"
    )
    
    # Authentication (for ADMIN/AUDITOR)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Bcrypt hash - only for ADMIN/AUDITOR"
    )
    
    # Personal Information
    firstname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="E.164 format (e.g., +12345678900)"
    )
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Must be 18+ years old"
    )
    
    # Role and Status
    role: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=UserRole.CLIENT,
        index=True,
        comment="0=ADMIN, 1=AUDITOR, 2=CLIENT"
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True,
        comment="0=INACTIVE, 1=ACTIVE, 2=DELETED"
    )
    
    # Verification Flags
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # KYC Information
    kyc_status: Mapped[str] = mapped_column(
        SQLEnum(KYCStatus),
        nullable=False,
        default=KYCStatus.NONE,
        index=True,
        comment="KYC verification status"
    )
    kyc_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    kyc_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    kyc_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="e.g., 'persona', 'onfido'"
    )
    kyc_provider_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="External KYC provider reference ID"
    )
    
    # Terms and Compliance
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    terms_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="e.g., 'v1.0', 'v2.1'"
    )
    
    # Activity Tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    wallets = relationship("Wallet", back_populates="user", lazy="select")
    transactions = relationship("Transaction", back_populates="user", lazy="select")
    earn_positions = relationship("EarnPosition", back_populates="user", lazy="select")
    save_schedules = relationship("SaveSchedule", back_populates="user", lazy="select")
    hyperliquid_positions = relationship("HyperliquidPosition", back_populates="user", lazy="select")
    subscriptions = relationship("Subscription", back_populates="user", lazy="select")
    llm_conversations = relationship("LLMConversation", back_populates="user", lazy="select")
    agent_executions = relationship("AgentExecution", back_populates="user", lazy="select")
    notifications = relationship("Notification", back_populates="user", lazy="select")
    funding_transactions = relationship("FundingTransaction", back_populates="user", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_role_status", "role", "status"),
        Index("idx_user_kyc_status", "kyc_status"),
        Index("idx_user_created_at", "created_at"),
        Index("idx_user_email_status", "email", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, uid='{self.uid}', email='{self.email}', role={self.role})>"
    
    @property
    def role_label(self) -> str:
        """Get human-readable role label"""
        role_map = {0: "ADMIN", 1: "AUDITOR", 2: "CLIENT"}
        return role_map.get(self.role, "UNKNOWN")
    
    @property
    def status_label(self) -> str:
        """Get human-readable status label"""
        status_map = {0: "INACTIVE", 1: "ACTIVE", 2: "DELETED"}
        return status_map.get(self.status, "UNKNOWN")
    
    @property
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_kyc_approved(self) -> bool:
        """Check if user KYC is approved"""
        return self.kyc_status == KYCStatus.APPROVED
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.firstname and self.lastname:
            return f"{self.firstname} {self.lastname}"
        elif self.firstname:
            return self.firstname
        elif self.lastname:
            return self.lastname
        return self.email.split("@")[0]


class UserProfile(Base):
    """
    Extended user profile information (optional additional data)
    
    This table stores additional profile data that doesn't fit in the main
    users table, such as preferences, settings, and metadata.
    """
    
    __tablename__ = "user_profiles"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True
    )
    
    # Profile Data
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="UTC",
        comment="e.g., 'America/New_York'"
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default="en",
        comment="ISO 639-1 code (e.g., 'en', 'es')"
    )
    currency_preference: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        default="USD",
        comment="ISO 4217 code"
    )
    
    # Notification Preferences (JSON stored as text)
    notification_preferences: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON: {email: true, push: true, sms: false, in_app: true}"
    )
    
    # Privacy Settings
    profile_visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="private",
        comment="'public', 'private', 'friends'"
    )
    data_sharing_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    marketing_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Referral
    referral_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True
    )
    referred_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("✅ User tables created successfully!")
    print("\nTables created:")
    print("- users")
    print("- user_profiles")
