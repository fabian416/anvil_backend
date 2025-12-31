"""
Chat Handlers - DeFi Shortcut Handlers.

Provides specialized handlers for common DeFi operations:
- LendingHandler: Morpho vault deposits and yield earning
- MoneyMarketHandler: Compare lending rates across protocols
- SwapHandler: Token swaps via DEX aggregators (1inch)
- PortfolioHandler: Full portfolio enumeration
- BalanceHandler: Wallet balance queries (via PortfolioHandler)
- ActivityHandler: Transaction history
- ReceiveHandler: Generate receive address/QR
"""

from app.application.chat.handlers.lending_handler import (
    LendingHandler,
    LendingHandlerResult,
)
from app.application.chat.handlers.portfolio_handler import (
    PortfolioHandler,
    PortfolioHandlerResult,
    BalanceHandlerResult,
)
from app.application.chat.handlers.swap_handler import (
    SwapHandler,
    SwapHandlerResult,
)
from app.application.chat.handlers.activity_handler import (
    ActivityHandler,
    ActivityHandlerResult,
)
from app.application.chat.handlers.receive_handler import (
    ReceiveHandler,
    ReceiveHandlerResult,
)
from app.application.chat.handlers.money_market_handler import (
    MoneyMarketHandler,
    MoneyMarketHandlerResult,
)

__all__ = [
    # Lending
    "LendingHandler",
    "LendingHandlerResult",
    # Money Market
    "MoneyMarketHandler",
    "MoneyMarketHandlerResult",
    # Swap
    "SwapHandler",
    "SwapHandlerResult",
    # Portfolio & Balance
    "PortfolioHandler",
    "PortfolioHandlerResult",
    "BalanceHandlerResult",
    # Activity
    "ActivityHandler",
    "ActivityHandlerResult",
    # Receive
    "ReceiveHandler",
    "ReceiveHandlerResult",
]
