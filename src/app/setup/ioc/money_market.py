"""
Money Market Providers for Dependency Injection.

Provides configured money market services following hexagonal architecture:
- Ports → Adapters (Cache, Comparison, Preference, Alert)
- Rate caching with 60s TTL
- Comparison analytics logging
- User preference management
- Rate alert notifications
"""

from dishka import Provider, Scope, provide

from app.domain.ports.money_market.money_market_alert_gateway import (
    MoneyMarketAlertGateway,
)
from app.domain.ports.money_market.money_market_cache_gateway import (
    MoneyMarketCacheGateway,
)
from app.domain.ports.money_market.money_market_comparison_gateway import (
    MoneyMarketComparisonGateway,
)
from app.domain.ports.money_market.money_market_preference_gateway import (
    MoneyMarketPreferenceGateway,
)
from app.infrastructure.adapters.money_market.money_market_alert_adapter_sqla import (
    MoneyMarketAlertAdapterSqla,
)
from app.infrastructure.adapters.money_market.money_market_cache_adapter_sqla import (
    MoneyMarketCacheAdapterSqla,
)
from app.infrastructure.adapters.money_market.money_market_comparison_adapter_sqla import (
    MoneyMarketComparisonAdapterSqla,
)
from app.infrastructure.adapters.money_market.money_market_preference_adapter_sqla import (
    MoneyMarketPreferenceAdapterSqla,
)
from app.infrastructure.adapters.types import MainAsyncSession


class MoneyMarketProvider(Provider):
    """
    Provider for money market rate caching and analytics.

    Configures dependency injection for:
    - Cache gateway (60s TTL rate caching)
    - Comparison gateway (analytics logging)
    - Preference gateway (user settings)
    - Alert gateway (rate change notifications)

    Scopes:
    - All adapters: REQUEST scope (per-request with AsyncSession)

    Architecture:
    - Follows hexagonal architecture (ports → adapters)
    - All methods return protocol interfaces, not concrete types
    - SQLAlchemy adapters injected with AsyncSession from Dishka
    """

    # ===== INFRASTRUCTURE LAYER (Ports → Adapters) =====

    @provide(scope=Scope.REQUEST)
    def provide_cache_gateway(
        self,
        session: MainAsyncSession,
    ) -> MoneyMarketCacheGateway:
        """
        Provide cache gateway for 60s TTL rate caching.

        Implements MoneyMarketCacheGateway port using SQLAlchemy
        for PostgreSQL persistence with automatic TTL validation.

        Args:
            session: MainAsyncSession from Dishka (injected automatically)

        Returns:
            MoneyMarketCacheAdapterSqla implementing MoneyMarketCacheGateway

        Performance:
        - Cache hit: <50ms (index-optimized query)
        - Cache miss: Original RPC latency + insert time
        - TTL: 60 seconds (configurable via entity)
        """
        return MoneyMarketCacheAdapterSqla(session=session)

    @provide(scope=Scope.REQUEST)
    def provide_comparison_gateway(
        self,
        session: MainAsyncSession,
    ) -> MoneyMarketComparisonGateway:
        """
        Provide comparison gateway for analytics logging.

        Implements MoneyMarketComparisonGateway port using SQLAlchemy
        to log every rate comparison for optimization insights.

        Args:
            session: MainAsyncSession from Dishka (injected automatically)

        Returns:
            MoneyMarketComparisonAdapterSqla implementing MoneyMarketComparisonGateway

        Analytics Tracked:
        - Total comparisons per asset/chain
        - Unique users per market
        - Average response latency
        - Cache hit rate
        - Protocol preference trends
        """
        return MoneyMarketComparisonAdapterSqla(session=session)

    @provide(scope=Scope.REQUEST)
    def provide_preference_gateway(
        self,
        session: MainAsyncSession,
    ) -> MoneyMarketPreferenceGateway:
        """
        Provide preference gateway for user settings management.

        Implements MoneyMarketPreferenceGateway port using SQLAlchemy
        with UPSERT pattern for conflict resolution.

        Args:
            session: MainAsyncSession from Dishka (injected automatically)

        Returns:
            MoneyMarketPreferenceAdapterSqla implementing MoneyMarketPreferenceGateway

        Features:
        - Rate alert configuration
        - Watched assets/chains tracking
        - Protocol preferences
        - Notification settings
        - UPSERT on user_id unique constraint
        """
        return MoneyMarketPreferenceAdapterSqla(session=session)

    @provide(scope=Scope.REQUEST)
    def provide_alert_gateway(
        self,
        session: MainAsyncSession,
    ) -> MoneyMarketAlertGateway:
        """
        Provide alert gateway for rate change notifications.

        Implements MoneyMarketAlertGateway port using SQLAlchemy
        to manage rate change alerts and notification history.

        Args:
            session: MainAsyncSession from Dishka (injected automatically)

        Returns:
            MoneyMarketAlertAdapterSqla implementing MoneyMarketAlertGateway

        Features:
        - Alert creation and management
        - Read status tracking
        - Notification delivery status
        - Alert statistics and analytics
        - Time-based filtering
        """
        return MoneyMarketAlertAdapterSqla(session=session)
