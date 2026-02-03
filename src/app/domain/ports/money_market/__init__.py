"""
Money market domain ports.

Abstract interfaces (protocols) for money market operations following
hexagonal architecture principles. These define the contracts that
infrastructure adapters must implement.
"""

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

__all__ = [
    "MoneyMarketAlertGateway",
    "MoneyMarketCacheGateway",
    "MoneyMarketComparisonGateway",
    "MoneyMarketPreferenceGateway",
]
