"""
Portfolio Handler for Chat - User portfolio and balance operations.

Provides real-time portfolio data using:
- PortfolioService for on-chain balance fetching
- DeFiLlama for USD pricing
- Multi-chain support (Ethereum, Base, Arbitrum, etc.)
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.application.portfolio.portfolio_service import PortfolioService, PortfolioDTO
from app.domain.enums.chain_type import ChainType


@dataclass
class PortfolioHandlerResult:
    """Result from portfolio handler."""

    content: str
    portfolio: Optional[dict]
    total_usd: float
    chain: str
    latency_ms: int
    handler: str = "portfolio_handler"


@dataclass
class BalanceHandlerResult:
    """Result from balance handler."""

    content: str
    total_usd: float
    tokens: list[dict]
    native_balance: float
    native_symbol: str
    chain: str
    latency_ms: int
    handler: str = "balance_handler"


class PortfolioHandler:
    """
    Handler for portfolio-related chat intents.

    Uses PortfolioService to fetch real on-chain balances
    and USD prices from DeFiLlama.

    Features:
    - Real-time balance fetching via RPC
    - Multi-chain support
    - USD value calculation
    - Token breakdown
    """

    def __init__(self, portfolio_service: PortfolioService):
        """
        Initialize portfolio handler.

        Args:
            portfolio_service: Service for fetching portfolio data
        """
        self._portfolio_service = portfolio_service

    async def get_portfolio(
        self,
        wallet_address: str,
        chain: str = "base",
    ) -> PortfolioHandlerResult:
        """
        Get full portfolio for a wallet address.

        Args:
            wallet_address: User's wallet address
            chain: Blockchain (ethereum, base, etc.)

        Returns:
            PortfolioHandlerResult with formatted content and data
        """
        start_time = time.time()

        # Map chain string to ChainType
        chain_type = self._get_chain_type(chain)

        # Fetch portfolio from service
        portfolio = await self._portfolio_service.get_portfolio_by_address(
            address=wallet_address,
            chain=chain_type,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        if not portfolio:
            return PortfolioHandlerResult(
                content=self._format_no_portfolio_response(wallet_address, chain),
                portfolio=None,
                total_usd=0.0,
                chain=chain,
                latency_ms=latency_ms,
            )

        # Format response
        content = self._format_portfolio_response(portfolio)

        return PortfolioHandlerResult(
            content=content,
            portfolio=self._portfolio_to_dict(portfolio),
            total_usd=portfolio.total_usd,
            chain=portfolio.chain,
            latency_ms=latency_ms,
        )

    async def get_balance(
        self,
        wallet_address: str,
        chain: str = "base",
    ) -> BalanceHandlerResult:
        """
        Get balance summary for a wallet address.

        Args:
            wallet_address: User's wallet address
            chain: Blockchain (ethereum, base, etc.)

        Returns:
            BalanceHandlerResult with formatted content and data
        """
        start_time = time.time()

        chain_type = self._get_chain_type(chain)

        portfolio = await self._portfolio_service.get_portfolio_by_address(
            address=wallet_address,
            chain=chain_type,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        if not portfolio:
            return BalanceHandlerResult(
                content=self._format_no_balance_response(wallet_address, chain),
                total_usd=0.0,
                tokens=[],
                native_balance=0.0,
                native_symbol="ETH",
                chain=chain,
                latency_ms=latency_ms,
            )

        content = self._format_balance_response(portfolio)

        return BalanceHandlerResult(
            content=content,
            total_usd=portfolio.total_usd,
            tokens=portfolio.tokens,
            native_balance=portfolio.native_balance,
            native_symbol=portfolio.native_symbol,
            chain=portfolio.chain,
            latency_ms=latency_ms,
        )

    def _get_chain_type(self, chain: str) -> ChainType:
        """Convert chain string to ChainType enum."""
        chain_map = {
            "ethereum": ChainType.ETHEREUM,
            "base": ChainType.BASE,
            "arbitrum": ChainType.ARBITRUM,
            "polygon": ChainType.POLYGON,
            "optimism": ChainType.OPTIMISM,
        }
        return chain_map.get(chain.lower(), ChainType.BASE)

    def _format_portfolio_response(self, portfolio: PortfolioDTO) -> str:
        """Format portfolio data as chat response."""
        chain_emoji = self._get_chain_emoji(portfolio.chain)

        response = f"""{chain_emoji} **Your Portfolio on {portfolio.chain.upper()}**

**Total Value:** ${portfolio.total_usd:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TOKENS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        # Native token
        if portfolio.native_balance > 0:
            native_usd = portfolio.native_usd_value or 0
            pct = (native_usd / portfolio.total_usd * 100) if portfolio.total_usd > 0 else 0
            response += f"• **{portfolio.native_symbol}**: {portfolio.native_balance:.4f} (${native_usd:,.2f}) - {pct:.1f}%\n"

        # ERC-20 tokens
        for token in sorted(portfolio.tokens, key=lambda t: t.get("usd_value", 0) or 0, reverse=True):
            amount = token.get("amount", 0)
            usd_value = token.get("usd_value", 0) or 0
            symbol = token.get("symbol", "???")
            pct = token.get("percentage", 0)

            if usd_value > 0.01:  # Only show tokens worth more than $0.01
                response += f"• **{symbol}**: {amount:,.4f} (${usd_value:,.2f}) - {pct:.1f}%\n"

        response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Wallet:** `{portfolio.wallet_address[:8]}...{portfolio.wallet_address[-6:]}`
**Last Updated:** {portfolio.captured_at[:19].replace('T', ' ')} UTC

Would you like portfolio optimization recommendations?
"""
        return response

    def _format_balance_response(self, portfolio: PortfolioDTO) -> str:
        """Format balance data as chat response."""
        chain_emoji = self._get_chain_emoji(portfolio.chain)

        response = f"""{chain_emoji} **Your Balance**

**Total Value:** ${portfolio.total_usd:,.2f} USD

**Assets:**
"""
        # Native token
        if portfolio.native_balance > 0:
            native_usd = portfolio.native_usd_value or 0
            response += f"• {portfolio.native_balance:.4f} {portfolio.native_symbol} (${native_usd:,.2f})\n"

        # Top tokens by value
        for token in sorted(portfolio.tokens, key=lambda t: t.get("usd_value", 0) or 0, reverse=True)[:5]:
            amount = token.get("amount", 0)
            usd_value = token.get("usd_value", 0) or 0
            symbol = token.get("symbol", "???")

            if usd_value > 0.01:
                response += f"• {amount:,.2f} {symbol} (${usd_value:,.2f})\n"

        response += f"""
*Last updated: just now*

Would you like to see your full portfolio or transaction history?
"""
        return response

    def _format_no_portfolio_response(self, wallet_address: str, chain: str) -> str:
        """Format response when no portfolio found."""
        return f"""📊 **Portfolio Not Found**

I couldn't find any assets for wallet `{wallet_address[:10]}...` on {chain.upper()}.

This could mean:
• The wallet has no tokens on this chain
• The wallet address is incorrect
• Try a different chain (ethereum, base, arbitrum)

Would you like to check a different chain?
"""

    def _format_no_balance_response(self, wallet_address: str, chain: str) -> str:
        """Format response when no balance found."""
        return f"""💰 **No Balance Found**

I couldn't find any balance for wallet `{wallet_address[:10]}...` on {chain.upper()}.

**Possible reasons:**
• Wallet has no funds on this chain
• Try checking a different chain

Would you like to receive funds? Just say "receive" to get your deposit address.
"""

    def _get_chain_emoji(self, chain: str) -> str:
        """Get emoji for chain."""
        emojis = {
            "ethereum": "⟠",
            "base": "🔵",
            "arbitrum": "🔷",
            "polygon": "💜",
            "optimism": "🔴",
        }
        return emojis.get(chain.lower(), "🔗")

    def _portfolio_to_dict(self, portfolio: PortfolioDTO) -> dict:
        """Convert portfolio DTO to dictionary."""
        return {
            "wallet_address": portfolio.wallet_address,
            "chain": portfolio.chain,
            "total_usd": portfolio.total_usd,
            "native_balance": portfolio.native_balance,
            "native_usd_value": portfolio.native_usd_value,
            "native_symbol": portfolio.native_symbol,
            "tokens": portfolio.tokens,
            "captured_at": portfolio.captured_at,
            "has_value": portfolio.has_value,
        }
