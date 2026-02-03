"""
Swap tools for SwapAgent.
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from app.infrastructure.defi.providers.oneinch import OneInchClient

logger = logging.getLogger(__name__)


# Common token addresses on Ethereum mainnet
COMMON_TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # Native ETH
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}


async def get_swap_quote_tool(
    src_token: str,
    dst_token: str,
    amount: str,
    oneinch_client: OneInchClient,
) -> str:
    """
    Get a swap quote from 1inch.

    Args:
        src_token: Source token symbol (e.g., "USDC")
        dst_token: Destination token symbol (e.g., "ETH")
        amount: Amount in human-readable format (e.g., "100")
        oneinch_client: 1inch API client

    Returns:
        Human-readable quote string
    """
    try:
        # Resolve token addresses
        src_address = COMMON_TOKENS.get(src_token.upper())
        dst_address = COMMON_TOKENS.get(dst_token.upper())

        if not src_address or not dst_address:
            return f"Error: Unsupported token. Supported tokens: {', '.join(COMMON_TOKENS.keys())}"

        # Convert amount to smallest unit (assuming 6 decimals for stablecoins, 18 for others)
        decimals = 6 if src_token.upper() in ["USDC", "USDT"] else 18
        amount_wei = str(int(Decimal(amount) * Decimal(10**decimals)))

        # Get quote
        quote = await oneinch_client.get_quote(
            src=src_address,
            dst=dst_address,
            amount=amount_wei,
        )

        # Parse response
        to_amount_wei = quote.get("toAmount", "0")
        dst_decimals = 18 if dst_token.upper() not in ["USDC", "USDT"] else 6
        to_amount = Decimal(to_amount_wei) / Decimal(10**dst_decimals)

        estimated_gas = quote.get("estimatedGas", "unknown")

        return (
            f"Swap Quote:\n"
            f"• From: {amount} {src_token}\n"
            f"• To: ~{to_amount:.6f} {dst_token}\n"
            f"• Rate: 1 {src_token} = {(to_amount / Decimal(amount)):.6f} {dst_token}\n"
            f"• Estimated Gas: {estimated_gas}\n"
            f"• Slippage: 1%\n"
            f"\n"
            f"This is an estimate. Actual amount may vary due to slippage."
        )

    except Exception as e:
        logger.error(f"Error getting swap quote: {e}")
        return f"Error getting quote: {str(e)}"


async def explain_swap_tool(
    src_token: str,
    dst_token: str,
) -> str:
    """
    Explain how a token swap works.

    Args:
        src_token: Source token symbol
        dst_token: Destination token symbol

    Returns:
        Explanation string
    """
    return (
        f"How {src_token} → {dst_token} Swap Works:\n"
        f"\n"
        f"1. **Token Approval**: First, you must approve the 1inch contract to spend your {src_token}\n"
        f"2. **Quote Aggregation**: 1inch queries multiple DEXs (Uniswap, Sushiswap, etc.) for best rates\n"
        f"3. **Route Optimization**: Finds optimal path, potentially splitting across multiple DEXs\n"
        f"4. **Execution**: Executes swap atomically - all or nothing\n"
        f"5. **Slippage Protection**: Reverts if price moves beyond tolerance (typically 1%)\n"
        f"\n"
        f"**Important Considerations:**\n"
        f"• Gas Fees: Ethereum transactions cost gas (varies with network congestion)\n"
        f"• Slippage: Price can change between quote and execution\n"
        f"• Approval: One-time gas cost for token approval\n"
        f"• Price Impact: Large trades can move the market\n"
        f"\n"
        f"**Safety:**\n"
        f"• 1inch is a trusted aggregator (used by millions)\n"
        f"• Smart contracts are audited\n"
        f"• Non-custodial (you keep control of your funds)\n"
    )


async def get_token_info_tool(
    token: str,
    oneinch_client: OneInchClient,
) -> str:
    """
    Get information about a token.

    Args:
        token: Token symbol
        oneinch_client: 1inch API client

    Returns:
        Token information string
    """
    try:
        token_address = COMMON_TOKENS.get(token.upper())

        if not token_address:
            return (
                f"Token {token} not found.\n"
                f"Supported tokens: {', '.join(COMMON_TOKENS.keys())}"
            )

        return (
            f"Token Information: {token.upper()}\n"
            f"• Address: {token_address}\n"
            f"• Network: Ethereum Mainnet\n"
            f"• Type: {'Native' if token.upper() == 'ETH' else 'ERC-20'}\n"
        )

    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return f"Error: {str(e)}"
