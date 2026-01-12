"""Chat domain value objects.

This module defines value objects for the unified chat system that supports
both guest and authenticated users through context abstraction.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class UserContext(ABC):
    """Abstract user context for unified chat system.

    Provides polymorphic interface for both guest and authenticated users,
    allowing the same handler to serve different user types with different
    configurations.
    """

    @abstractmethod
    def get_user_id(self) -> str:
        """Get unique user identifier.

        Returns:
            String identifier with prefix (guest: or auth:)
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True for authenticated users, False for guests
        """
        pass

    @abstractmethod
    def get_rate_limit(self) -> tuple[int, int]:
        """Get rate limit configuration.

        Returns:
            Tuple of (messages_limit, window_seconds)
        """
        pass

    @abstractmethod
    def get_retention_days(self) -> Optional[int]:
        """Get data retention period in days.

        Returns:
            Number of days to retain data, or None for permanent retention
        """
        pass

    @abstractmethod
    def get_storage_prefix(self) -> str:
        """Get database table prefix.

        Returns:
            Table prefix ('guest_' or 'chat_')
        """
        pass


@dataclass(frozen=True)
class GuestContext(UserContext):
    """Guest user context (IP-based identification).

    Immutable context for guest users with:
    - IP-based identification
    - 20 messages/hour rate limit
    - 90-day data retention
    - Basic feature access
    """

    ip_address: str

    def get_user_id(self) -> str:
        """Get guest user identifier."""
        return f"guest:{self.ip_address}"

    def is_authenticated(self) -> bool:
        """Guest users are not authenticated."""
        return False

    def get_rate_limit(self) -> tuple[int, int]:
        """Guest rate limit: 20 messages per hour."""
        return (20, 3600)

    def get_retention_days(self) -> Optional[int]:
        """Guest data retention: 90 days."""
        return 90

    def get_storage_prefix(self) -> str:
        """Guest tables prefix."""
        return "guest_"


@dataclass(frozen=True)
class AuthenticatedContext(UserContext):
    """Authenticated user context (legacy INTEGER user_id).

    Immutable context for authenticated users with:
    - Legacy INTEGER user_id (from users table)
    - Higher rate limits (1000-10000 messages/hour)
    - Permanent data retention
    - Premium feature access based on subscription tier

    Note: This stores the legacy INTEGER user_id from the users table.
    The chat_users table creates a UUID bridge to this legacy ID.
    """

    user_id: int  # Legacy users table ID (INTEGER)
    email: str
    subscription_tier: str = "free"  # free, premium, enterprise

    def get_user_id(self) -> str:
        """Get authenticated user identifier."""
        return f"auth:{self.user_id}"

    def is_authenticated(self) -> bool:
        """Authenticated users return True."""
        return True

    def get_rate_limit(self) -> tuple[int, int]:
        """Rate limit based on subscription tier.

        Returns:
            - premium/enterprise: 10,000 messages/hour
            - free: 1,000 messages/hour
        """
        if self.subscription_tier in ("premium", "enterprise"):
            return (10000, 3600)
        return (1000, 3600)

    def get_retention_days(self) -> Optional[int]:
        """Authenticated user data is retained permanently."""
        return None  # Permanent retention

    def get_storage_prefix(self) -> str:
        """Authenticated user tables prefix."""
        return "chat_"


@dataclass(frozen=True)
class FeatureFlags:
    """Feature availability flags based on user context.

    Immutable feature configuration that determines which Hunter AI tools
    and premium features are available to a user based on their context
    (guest vs authenticated) and subscription tier.
    """

    # Basic features (available to all users)
    hunter_sentiment: bool = True
    hunter_trading_signals: bool = True
    hunter_price_prediction: bool = True

    # Premium features (authenticated users only)
    hunter_patterns: bool = False
    hunter_portfolio: bool = False
    hunter_risk_signals: bool = False

    # Advanced features (premium tier only)
    export_conversations: bool = False
    unlimited_history: bool = False
    advanced_analytics: bool = False
    priority_support: bool = False
    custom_alerts: bool = False
    api_access: bool = False

    # Enterprise features
    team_collaboration: bool = False
    sso_integration: bool = False
    admin_dashboard: bool = False
    dedicated_support: bool = False

    @classmethod
    def from_context(cls, context: UserContext) -> "FeatureFlags":
        """Create feature flags from user context.

        Args:
            context: User context (Guest or Authenticated)

        Returns:
            FeatureFlags instance with appropriate features enabled
        """
        if isinstance(context, GuestContext):
            # Guest users: Basic features only
            return cls(
                # Basic features enabled
                hunter_sentiment=True,
                hunter_trading_signals=True,
                hunter_price_prediction=True,
                # All premium features disabled
                hunter_patterns=False,
                hunter_portfolio=False,
                hunter_risk_signals=False,
                export_conversations=False,
                unlimited_history=False,
                advanced_analytics=False,
                priority_support=False,
                custom_alerts=False,
                api_access=False,
                team_collaboration=False,
                sso_integration=False,
                admin_dashboard=False,
                dedicated_support=False,
            )

        elif isinstance(context, AuthenticatedContext):
            if context.subscription_tier == "enterprise":
                # Enterprise: All features enabled
                return cls(
                    # Basic features
                    hunter_sentiment=True,
                    hunter_trading_signals=True,
                    hunter_price_prediction=True,
                    # Premium features
                    hunter_patterns=True,
                    hunter_portfolio=True,
                    hunter_risk_signals=True,
                    # Advanced features
                    export_conversations=True,
                    unlimited_history=True,
                    advanced_analytics=True,
                    priority_support=True,
                    custom_alerts=True,
                    api_access=True,
                    # Enterprise features
                    team_collaboration=True,
                    sso_integration=True,
                    admin_dashboard=True,
                    dedicated_support=True,
                )

            elif context.subscription_tier == "premium":
                # Premium: All features except enterprise
                return cls(
                    # Basic features
                    hunter_sentiment=True,
                    hunter_trading_signals=True,
                    hunter_price_prediction=True,
                    # Premium features
                    hunter_patterns=True,
                    hunter_portfolio=True,
                    hunter_risk_signals=True,
                    # Advanced features
                    export_conversations=True,
                    unlimited_history=True,
                    advanced_analytics=True,
                    priority_support=True,
                    custom_alerts=True,
                    api_access=True,
                    # Enterprise features disabled
                    team_collaboration=False,
                    sso_integration=False,
                    admin_dashboard=False,
                    dedicated_support=False,
                )

            else:  # free tier
                # Free authenticated: Basic + standard premium features
                return cls(
                    # Basic features
                    hunter_sentiment=True,
                    hunter_trading_signals=True,
                    hunter_price_prediction=True,
                    # Standard premium features
                    hunter_patterns=True,
                    hunter_portfolio=True,
                    hunter_risk_signals=True,
                    # Advanced features disabled
                    export_conversations=False,
                    unlimited_history=False,
                    advanced_analytics=False,
                    priority_support=False,
                    custom_alerts=False,
                    api_access=False,
                    # Enterprise features disabled
                    team_collaboration=False,
                    sso_integration=False,
                    admin_dashboard=False,
                    dedicated_support=False,
                )

        # Default: Basic features only
        return cls()

    def get_enabled_intents(self) -> list[str]:
        """Get list of enabled Hunter AI intents.

        Returns:
            List of intent names that are enabled
        """
        intents = []

        if self.hunter_sentiment:
            intents.append("hunter_sentiment")
        if self.hunter_trading_signals:
            intents.append("hunter_trading_signals")
        if self.hunter_price_prediction:
            intents.append("hunter_price_prediction")
        if self.hunter_patterns:
            intents.append("hunter_patterns")
        if self.hunter_portfolio:
            intents.append("hunter_portfolio")
        if self.hunter_risk_signals:
            intents.append("hunter_risk_signals")

        return intents

    def is_intent_allowed(self, intent: str) -> bool:
        """Check if specific intent is allowed.

        Args:
            intent: Hunter AI intent name

        Returns:
            True if intent is enabled, False otherwise
        """
        intent_feature_map = {
            "hunter_sentiment": self.hunter_sentiment,
            "hunter_trading_signals": self.hunter_trading_signals,
            "hunter_price_prediction": self.hunter_price_prediction,
            "hunter_patterns": self.hunter_patterns,
            "hunter_portfolio": self.hunter_portfolio,
            "hunter_risk_signals": self.hunter_risk_signals,
        }

        return intent_feature_map.get(intent, False)

    def to_dict(self) -> dict:
        """Convert feature flags to dictionary.

        Returns:
            Dictionary representation of all feature flags
        """
        return {
            "basic": {
                "sentiment": self.hunter_sentiment,
                "trading_signals": self.hunter_trading_signals,
                "price_prediction": self.hunter_price_prediction,
            },
            "premium": {
                "patterns": self.hunter_patterns,
                "portfolio": self.hunter_portfolio,
                "risk_signals": self.hunter_risk_signals,
            },
            "advanced": {
                "export": self.export_conversations,
                "unlimited_history": self.unlimited_history,
                "analytics": self.advanced_analytics,
                "priority_support": self.priority_support,
                "custom_alerts": self.custom_alerts,
                "api_access": self.api_access,
            },
            "enterprise": {
                "team_collaboration": self.team_collaboration,
                "sso": self.sso_integration,
                "admin_dashboard": self.admin_dashboard,
                "dedicated_support": self.dedicated_support,
            },
        }
