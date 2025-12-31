"""
Swap Handler for Chat - Token swap operations via DEX aggregators.

Provides swap quotes and transaction data using:
- 1inch API for best routing and execution
- Multi-chain support (Ethereum, Base, Arbitrum, etc.)
- Slippage protection
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.infrastructure.adapters.external.oneinch_client import (
    OneInchClient,
    SwapQuote,
)


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
    latency_ms: int
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

    Uses 1inch API for:
    - Swap quotes across DEXes
    - Best price routing
    - Transaction data for execution

    Features:
    - Multi-chain support
    - Price impact calculation
    - Gas estimation
    """

    def __init__(self, oneinch_client: Optional[OneInchClient] = None):
        """
        Initialize swap handler.

        Args:
            oneinch_client: 1inch API client (optional)
        """
        self._oneinch = oneinch_client

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str = "base",
        slippage: float = 1.0,
    ) -> SwapHandlerResult:
        """
        Get swap quote for token exchange.

        Args:
            from_token: Source token symbol or address
            to_token: Destination token symbol or address
            amount: Amount to swap (human readable)
            chain: Blockchain (ethereum, base, arbitrum)
            slippage: Slippage tolerance (percent)

        Returns:
            SwapHandlerResult with quote and formatted content
        """
        start_time = time.time()

        # Resolve token addresses
        from_address = self._resolve_token_address(from_token, chain)
        to_address = self._resolve_token_address(to_token, chain)

        # Convert amount to wei (assuming 18 decimals for simplicity)
        amount_wei = self._to_wei(amount, from_token)

        try:
            if self._oneinch:
                # Get real quote from 1inch
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
                    },
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=amount,
                    to_amount=to_amount,
                    price_impact=price_impact,
                    chain=chain,
                    latency_ms=latency_ms,
                )
            else:
                # Fallback: Return informational response
                content = self._format_fallback_response(
                    from_token=from_token,
                    to_token=to_token,
                    amount=amount,
                    chain=chain,
                )

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
                    latency_ms=latency_ms,
                )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            return SwapHandlerResult(
                content=f"⚠️ **Error Getting Swap Quote**\n\n{str(e)}\n\nPlease try again later.",
                quote=None,
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount="0",
                price_impact=0.0,
                chain=chain,
                latency_ms=latency_ms,
            )

    def _resolve_token_address(self, token: str, chain: str) -> str:
        """Resolve token symbol to address."""
        # If already an address, return as-is
        if token.startswith("0x"):
            return token

        # Look up in token addresses
        chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(token.upper(), token)

    def _to_wei(self, amount: str, token: str) -> str:
        """Convert human readable amount to wei."""
        # Determine decimals based on token
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

    def _format_quote_response(
        self,
        from_token: str,
        to_token: str,
        from_amount: str,
        to_amount: str,
        price_impact: float,
        chain: str,
        gas_estimate: int,
    ) -> str:
        """Format swap quote as chat response."""
        chain_emoji = "🔵" if chain == "base" else "⟠"

        # Estimate gas cost in USD (rough estimate)
        gas_usd = gas_estimate * 0.00000001 * 2000  # Rough ETH price

        # Price impact warning
        impact_warning = ""
        if price_impact > 1.0:
            impact_warning = "\n⚠️ **High price impact!** Consider swapping a smaller amount."
        elif price_impact > 0.5:
            impact_warning = "\n⚡ Moderate price impact."

        return f"""{chain_emoji} **Swap Quote on {chain.upper()}**

**{from_amount} {from_token.upper()}** → **{to_amount} {to_token.upper()}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**DETAILS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Rate:** 1 {from_token.upper()} = {float(to_amount)/float(from_amount):.4f} {to_token.upper()}
• **Price Impact:** {price_impact:.2f}%
• **Estimated Gas:** ~${gas_usd:.2f}
• **Aggregator:** 1inch{impact_warning}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Ready to swap?** Reply "confirm swap" to proceed.

💡 *Slippage: 1% | Quote valid for 30 seconds*
"""

    def _format_fallback_response(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str,
    ) -> str:
        """Format fallback response when 1inch not available."""
        return f"""🔄 **Token Swap on {chain.upper()}**

You want to swap:
• **{amount} {from_token.upper()}** → **{to_token.upper()}**

**Available DEX Aggregators:**
• 1inch (best rates for most swaps)
• Hyperliquid (perpetuals & spot)
• UniswapX (gasless swaps)

To get a quote, I need the 1inch API configured.

**Alternative:** You can swap directly on:
• [1inch.io](https://1inch.io)
• [Uniswap](https://app.uniswap.org)

Would you like to try a different operation?
"""

    def parse_swap_from_message(self, message: str) -> tuple[str, str, str, str]:
        """
        Parse swap details from user message.

        Args:
            message: User message like "swap 1 ETH for USDC on base"

        Returns:
            Tuple of (amount, from_token, to_token, chain)
        """
        message_lower = message.lower()

        # Default values
        amount = "1"
        from_token = "ETH"
        to_token = "USDC"
        chain = "base"

        # Extract amount (first number found)
        import re
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

        # Extract chain
        if "ethereum" in message_lower or "mainnet" in message_lower:
            chain = "ethereum"
        elif "arbitrum" in message_lower:
            chain = "arbitrum"
        elif "polygon" in message_lower:
            chain = "polygon"

        return amount, from_token, to_token, chain
