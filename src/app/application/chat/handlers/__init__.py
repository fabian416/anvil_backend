"""
Chat Handlers - DeFi Shortcut Handlers.

Provides specialized handlers for common DeFi operations:
- LendingHandler: Morpho vault deposits and yield earning
- MoneyMarketHandler: Compare lending rates across protocols
- SwapHandler: Token swaps via DEX aggregators
- BalanceHandler: Wallet balance queries
- PortfolioHandler: Full portfolio enumeration
- ActivityHandler: Transaction history
- ReceiveHandler: Generate receive address/QR
"""

from app.application.chat.handlers.lending_handler import (
    LendingHandler,
    LendingHandlerResult,
)

__all__ = [
    "LendingHandler",
    "LendingHandlerResult",
]
