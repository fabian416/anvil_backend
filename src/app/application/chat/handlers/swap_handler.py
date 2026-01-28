"""
Swap Handler for Chat - Token swap operations via DEX aggregators.

Provides swap quotes and transaction data using:
- 1inch: Best routing for single-chain swaps
- LiFi: Cross-chain swaps and bridges
- Hyperliquid: Perpetuals and spot trading

Per CEO spec: Hyperliquid/LiFi + 1inch for swaps
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.infrastructure.adapters.external.oneinch_client import OneInchClient
from app.infrastructure.adapters.external.lifi_client import LiFiClient
from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


@dataclass
class SwapHandlerResult:
    """Result from swap handler."""

    content: str
    quote: Optional[dict]
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    price_impact: float
    chain: str
    aggregator: str  # Which DEX aggregator was used
    latency_ms: int
    language: str = "en"
    handler: str = "swap_handler"


# Common token addresses by chain
TOKEN_ADDRESSES = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EesdeAC495271d0F",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    },
    "base": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
    },
    "arbitrum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    },
}


class SwapHandler:
    """
    Handler for swap-related chat intents.

    Uses multiple aggregators per CEO spec:
    - 1inch: Best rates for single-chain swaps
    - LiFi: Cross-chain bridges and swaps
    - Hyperliquid: Perpetuals and spot trading

    Features:
    - Multi-chain support
    - Cross-chain bridging
    - Best route selection
    - Price impact calculation
    """

    def __init__(
        self,
        oneinch_client: Optional[OneInchClient] = None,
        lifi_client: Optional[LiFiClient] = None,
        hyperliquid_client: Optional[HyperliquidClient] = None,
    ):
        """
        Initialize swap handler.

        Args:
            oneinch_client: 1inch API client for single-chain swaps
            lifi_client: LiFi API client for cross-chain swaps
            hyperliquid_client: Hyperliquid client for perpetuals
        """
        self._oneinch = oneinch_client
        self._lifi = lifi_client
        self._hyperliquid = hyperliquid_client

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_chain: str = "base",
        to_chain: Optional[str] = None,
        slippage: float = 1.0,
    ) -> SwapHandlerResult:
        """
        Get swap quote for token exchange.

        Automatically selects best aggregator:
        - Cross-chain: Uses LiFi
        - Same-chain: Uses 1inch (or LiFi fallback)

        Args:
            from_token: Source token symbol or address
            to_token: Destination token symbol or address
            amount: Amount to swap (human readable)
            from_chain: Source blockchain
            to_chain: Destination chain (if cross-chain)
            slippage: Slippage tolerance (percent)

        Returns:
            SwapHandlerResult with quote and formatted content
        """
        start_time = time.time()
        to_chain = to_chain or from_chain  # Default to same chain

        # Determine if cross-chain swap
        is_cross_chain = from_chain.lower() != to_chain.lower()

        # Try aggregators in order of preference
        if is_cross_chain and self._lifi:
            return await self._get_lifi_quote(
                from_token, to_token, amount, from_chain, to_chain, slippage, start_time
            )
        elif self._oneinch:
            return await self._get_oneinch_quote(
                from_token, to_token, amount, from_chain, slippage, start_time
            )
        elif self._lifi:
            # Fallback to LiFi for same-chain
            return await self._get_lifi_quote(
                from_token, to_token, amount, from_chain, from_chain, slippage, start_time
            )
        else:
            # No aggregators configured - return informational response
            return self._get_fallback_response(
                from_token, to_token, amount, from_chain, start_time
            )

    async def _get_oneinch_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str,
        slippage: float,
        start_time: float,
    ) -> SwapHandlerResult:
        """Get quote from 1inch."""
        from_address = self._resolve_token_address(from_token, chain)
        to_address = self._resolve_token_address(to_token, chain)
        amount_wei = self._to_wei(amount, from_token)

        try:
            quote = await self._oneinch.get_swap_quote(
                from_token=from_address,
                to_token=to_address,
                amount=amount_wei,
                slippage=slippage,
            )

            to_amount = self._from_wei(quote.to_amount, to_token)
            price_impact = quote.price_impact

            content = self._format_quote_response(
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=to_amount,
                price_impact=price_impact,
                chain=chain,
                aggregator="1inch",
                gas_estimate=quote.estimated_gas,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return SwapHandlerResult(
                content=content,
                quote={
                    "from_token": from_address,
                    "to_token": to_address,
                    "from_amount": amount_wei,
                    "to_amount": quote.to_amount,
                    "estimated_gas": quote.estimated_gas,
                    "protocols": quote.protocols,
                    "aggregator": "1inch",
                },
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=to_amount,
                price_impact=price_impact,
                chain=chain,
                aggregator="1inch",
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.warning(f"1inch quote failed: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            return SwapHandlerResult(
                content=f"⚠️ **Error Getting 1inch Quote**\n\n{str(e)}\n\nTrying alternative routes...",
                quote=None,
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount="0",
                price_impact=0.0,
                chain=chain,
                aggregator="1inch",
                latency_ms=latency_ms,
            )

    async def _get_lifi_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_chain: str,
        to_chain: str,
        slippage: float,
        start_time: float,
    ) -> SwapHandlerResult:
        """Get quote from LiFi (supports cross-chain)."""
        amount_wei = self._to_wei(amount, from_token)

        try:
            quote = await self._lifi.get_quote(
                from_chain=from_chain,
                to_chain=to_chain,
                from_token=from_token,
                to_token=to_token,
                from_amount=amount_wei,
                slippage=slippage,
            )

            to_amount = self._from_wei(quote.to_amount, to_token)
            is_cross_chain = from_chain.lower() != to_chain.lower()

            content = self._format_lifi_response(
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=to_amount,
                from_chain=from_chain,
                to_chain=to_chain,
                bridge=quote.bridge_name,
                duration=quote.execution_duration,
                is_cross_chain=is_cross_chain,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return SwapHandlerResult(
                content=content,
                quote={
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "from_token": from_token,
                    "to_token": to_token,
                    "from_amount": amount_wei,
                    "to_amount": quote.to_amount,
                    "to_amount_min": quote.to_amount_min,
                    "bridge": quote.bridge_name,
                    "duration_seconds": quote.execution_duration,
                    "aggregator": "lifi",
                },
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=to_amount,
                price_impact=0.0,  # LiFi doesn't provide this directly
                chain=from_chain,
                aggregator="lifi",
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.warning(f"LiFi quote failed: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            return SwapHandlerResult(
                content=f"⚠️ **Error Getting LiFi Quote**\n\n{str(e)}\n\nPlease try again.",
                quote=None,
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount="0",
                price_impact=0.0,
                chain=from_chain,
                aggregator="lifi",
                latency_ms=latency_ms,
            )

    def _get_fallback_response(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str,
        start_time: float,
    ) -> SwapHandlerResult:
        """Generate fallback response when no aggregators configured."""
        content = f"""🔄 **Token Swap**

You want to swap:
• **{amount} {from_token.upper()}** → **{to_token.upper()}**
• Chain: {chain.upper()}

**Available DEX Aggregators:**
• **1inch** - Best rates for single-chain swaps
• **LiFi** - Cross-chain bridges and swaps
• **Hyperliquid** - Perpetuals and spot trading

To get live quotes, configure the aggregator API keys.

**Manual swap options:**
• [1inch.io](https://1inch.io)
• [LiFi](https://li.fi)
• [Hyperliquid](https://hyperliquid.xyz)
"""
        latency_ms = int((time.time() - start_time) * 1000)

        return SwapHandlerResult(
            content=content,
            quote=None,
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            to_amount="0",
            price_impact=0.0,
            chain=chain,
            aggregator="none",
            latency_ms=latency_ms,
        )

    def _format_quote_response(
        self,
        from_token: str,
        to_token: str,
        from_amount: str,
        to_amount: str,
        price_impact: float,
        chain: str,
        aggregator: str,
        gas_estimate: int,
    ) -> str:
        """Format swap quote as chat response."""
        chain_emoji = "🔵" if chain == "base" else "⟠"

        # Estimate gas cost in USD
        gas_usd = gas_estimate * 0.00000001 * 2000  # Rough ETH price

        # Price impact warning
        impact_warning = ""
        if price_impact > 1.0:
            impact_warning = "\n⚠️ **High price impact!** Consider a smaller amount."
        elif price_impact > 0.5:
            impact_warning = "\n⚡ Moderate price impact."

        try:
            rate = float(to_amount) / float(from_amount)
        except (ValueError, ZeroDivisionError):
            rate = 0

        return f"""{chain_emoji} **Swap Quote on {chain.upper()}**

**{from_amount} {from_token.upper()}** → **{to_amount} {to_token.upper()}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Rate:** 1 {from_token.upper()} = {rate:.4f} {to_token.upper()}
• **Price Impact:** {price_impact:.2f}%
• **Estimated Gas:** ~${gas_usd:.2f}
• **Aggregator:** {aggregator.upper()}{impact_warning}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Slippage: 1% | Quote valid for 30 seconds*
"""

    def _format_lifi_response(
        self,
        from_token: str,
        to_token: str,
        from_amount: str,
        to_amount: str,
        from_chain: str,
        to_chain: str,
        bridge: Optional[str],
        duration: int,
        is_cross_chain: bool,
    ) -> str:
        """Format LiFi quote response."""
        if is_cross_chain:
            title = f"🌉 **Cross-Chain Swap**"
            route_info = f"• **Route:** {from_chain.upper()} → {to_chain.upper()}"
            if bridge:
                route_info += f" via {bridge.capitalize()}"
        else:
            title = f"🔄 **Swap Quote on {from_chain.upper()}**"
            route_info = f"• **Chain:** {from_chain.upper()}"

        duration_str = f"{duration // 60}m {duration % 60}s" if duration > 60 else f"{duration}s"

        return f"""{title}

**{from_amount} {from_token.upper()}** → **{to_amount} {to_token.upper()}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{route_info}
• **Estimated Time:** ~{duration_str}
• **Aggregator:** LiFi

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Cross-chain swaps may take longer than single-chain*
"""

    def _resolve_token_address(self, token: str, chain: str) -> str:
        """Resolve token symbol to address."""
        if token.startswith("0x"):
            return token

        chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(token.upper(), token)

    def _to_wei(self, amount: str, token: str) -> str:
        """Convert human readable amount to wei."""
        decimals = 18
        if token.upper() in ["USDC", "USDT"]:
            decimals = 6
        elif token.upper() == "WBTC":
            decimals = 8

        try:
            value = float(amount) * (10 ** decimals)
            return str(int(value))
        except ValueError:
            return "0"

    def _from_wei(self, amount_wei: str, token: str) -> str:
        """Convert wei to human readable amount."""
        decimals = 18
        if token.upper() in ["USDC", "USDT"]:
            decimals = 6
        elif token.upper() == "WBTC":
            decimals = 8

        try:
            value = int(amount_wei) / (10 ** decimals)
            return f"{value:.6f}"
        except (ValueError, ZeroDivisionError):
            return "0"

    def parse_swap_from_message(self, message: str) -> tuple[str, str, str, str, Optional[str]]:
        """
        Parse swap details from user message.

        Args:
            message: User message like "swap 1 ETH for USDC on base"
                     or "bridge 100 USDC from ethereum to base"

        Returns:
            Tuple of (amount, from_token, to_token, from_chain, to_chain)
        """
        import re

        message_lower = message.lower()

        # Default values
        amount = "1"
        from_token = "ETH"
        to_token = "USDC"
        from_chain = "base"
        to_chain: Optional[str] = None

        # Extract amount
        amount_match = re.search(r"(\d+\.?\d*)", message)
        if amount_match:
            amount = amount_match.group(1)

        # Extract tokens
        tokens = ["eth", "usdc", "usdt", "dai", "wbtc", "weth"]
        found_tokens = []
        for token in tokens:
            if token in message_lower:
                found_tokens.append(token.upper())

        if len(found_tokens) >= 2:
            from_token = found_tokens[0]
            to_token = found_tokens[1]
        elif len(found_tokens) == 1:
            from_token = found_tokens[0]

        # Extract chains
        chains = ["ethereum", "base", "arbitrum", "polygon", "optimism"]
        found_chains = []
        for chain in chains:
            if chain in message_lower:
                found_chains.append(chain)

        # Check for cross-chain keywords
        is_bridge = any(word in message_lower for word in ["bridge", "cross-chain", "from", "to"])

        if len(found_chains) >= 2 and is_bridge:
            from_chain = found_chains[0]
            to_chain = found_chains[1]
        elif len(found_chains) == 1:
            from_chain = found_chains[0]

        return amount, from_token, to_token, from_chain, to_chain
