"""
Money market domain entities.

Core business entities for money market protocol rate caching and user preferences.
"""

from app.domain.entities.money_market.alert import MoneyMarketAlert
from app.domain.entities.money_market.protocol_data import (
    MoneyMarketProtocolData,
)
from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)
from app.domain.entities.money_market.user_preference import (
    MoneyMarketUserPreference,
)

__all__ = [
    "MoneyMarketAlert",
    "MoneyMarketProtocolData",
    "MoneyMarketRateComparison",
    "MoneyMarketUserPreference",
]
