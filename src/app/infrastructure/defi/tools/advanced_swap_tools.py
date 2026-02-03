"""
Advanced swap tools including multi-step optimization.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.infrastructure.defi.providers.oneinch import OneInchClient

logger = logging.getLogger(__name__)


async def compare_dex_routes_tool(
    src_token: str,
    dst_token: str,
    amount: str,
    oneinch_client: OneInchClient,
) -> str:
    """
    Compare different DEX routes for best price.

    Args:
        src_token: Source token symbol
        dst_token: Destination token symbol
        amount: Amount to swap
        oneinch_client: 1inch client

    Returns:
        Comparison of different routes
    """
    try:
        from app.infrastructure.defi.tools.swap_tools import COMMON_TOKENS

        # Resolve addresses
        src_address = COMMON_TOKENS.get(src_token.upper())
        dst_address = COMMON_TOKENS.get(dst_token.upper())

        if not src_address or not dst_address:
            return f"Unsupported tokens. Supported: {', '.join(COMMON_TOKENS.keys())}"

        # Convert amount
        decimals = 6 if src_token.upper() in ["USDC", "USDT"] else 18
        amount_wei = str(int(Decimal(amount) * Decimal(10**decimals)))

        # Get 1inch aggregated quote
        quote = await oneinch_client.get_quote(
            src=src_address,
            dst=dst_address,
            amount=amount_wei,
        )

        to_amount_wei = quote.get("toAmount", "0")
        dst_decimals = 18 if dst_token.upper() not in ["USDC", "USDT"] else 6
        to_amount = Decimal(to_amount_wei) / Decimal(10**dst_decimals)

        # Extract protocol info
        protocols = quote.get("protocols", [])

        # Build comparison
        lines = [
            f"DEX Route Comparison: {amount} {src_token} → {dst_token}\n",
            f"**Best Aggregated Route (1inch):**",
            f"• Output: {to_amount:.6f} {dst_token}",
            f"• Rate: 1 {src_token} = {(to_amount / Decimal(amount)):.6f} {dst_token}",
        ]

        if protocols and len(protocols) > 0:
            lines.append(f"\n**Route Details:**")

            # Show protocol breakdown
            for i, protocol_list in enumerate(protocols[:3], 1):
                if protocol_list:
                    protocol_names = [
                        p[0].get("name", "Unknown") for p in protocol_list if p
                    ]
                    lines.append(f"• Route {i}: {' → '.join(protocol_names)}")

        lines.extend([
            f"\n**Why 1inch Aggregation?**",
            f"• Splits trades across multiple DEXs",
            f"• Finds optimal routing automatically",
            f"• Better rates than single DEX",
            f"• Lower price impact",
        ])

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error comparing DEX routes: {e}")
        return f"Error: {str(e)}"


async def estimate_price_impact_tool(
    src_token: str,
    dst_token: str,
    amount: str,
    oneinch_client: OneInchClient,
) -> str:
    """
    Estimate price impact for a swap.

    Args:
        src_token: Source token symbol
        dst_token: Destination token symbol
        amount: Amount to swap
        oneinch_client: 1inch client

    Returns:
        Price impact analysis
    """
    try:
        from app.infrastructure.defi.tools.swap_tools import COMMON_TOKENS

        src_address = COMMON_TOKENS.get(src_token.upper())
        dst_address = COMMON_TOKENS.get(dst_token.upper())

        if not src_address or not dst_address:
            return "Unsupported tokens"

        # Get quotes for different amounts
        decimals = 6 if src_token.upper() in ["USDC", "USDT"] else 18
        dst_decimals = 18 if dst_token.upper() not in ["USDC", "USDT"] else 6

        # Small amount (1 unit)
        small_amount_wei = str(1 * 10**decimals)
        small_quote = await oneinch_client.get_quote(
            src=src_address,
            dst=dst_address,
            amount=small_amount_wei,
        )
        small_output = Decimal(small_quote.get("toAmount", "0")) / Decimal(
            10**dst_decimals
        )
        small_rate = small_output  # Rate per 1 unit

        # Large amount (user's amount)
        large_amount = Decimal(amount)
        large_amount_wei = str(int(large_amount * Decimal(10**decimals)))
        large_quote = await oneinch_client.get_quote(
            src=src_address,
            dst=dst_address,
            amount=large_amount_wei,
        )
        large_output = Decimal(large_quote.get("toAmount", "0")) / Decimal(
            10**dst_decimals
        )
        large_rate = large_output / large_amount

        # Calculate price impact
        price_impact = ((small_rate - large_rate) / small_rate) * 100

        # Risk assessment
        if price_impact < 0.1:
            risk = "✅ Minimal Impact"
        elif price_impact < 1:
            risk = "⚠️ Low Impact"
        elif price_impact < 3:
            risk = "⚠️ Moderate Impact"
        else:
            risk = "❌ High Impact - Consider smaller trade"

        return (
            f"Price Impact Analysis: {amount} {src_token} → {dst_token}\n"
            f"\n"
            f"**Expected Output:** {large_output:.6f} {dst_token}\n"
            f"**Rate:** 1 {src_token} = {large_rate:.6f} {dst_token}\n"
            f"\n"
            f"**Price Impact:** {price_impact:.2f}%\n"
            f"**Risk Level:** {risk}\n"
            f"\n"
            f"**What This Means:**\n"
            f"• Small trades: ~{small_rate:.6f} {dst_token} per {src_token}\n"
            f"• Your trade: ~{large_rate:.6f} {dst_token} per {src_token}\n"
            f"• Difference: {price_impact:.2f}% worse due to liquidity\n"
            f"\n"
            f"**Recommendation:**\n"
            f"{'Consider breaking into smaller trades if impact > 3%' if price_impact > 3 else 'Price impact is acceptable'}\n"
        )

    except Exception as e:
        logger.error(f"Error estimating price impact: {e}")
        return f"Error: {str(e)}"


async def suggest_optimal_swap_time_tool(
    src_token: str,
    dst_token: str,
) -> str:
    """
    Suggest optimal time for swap based on gas and volatility.

    Args:
        src_token: Source token symbol
        dst_token: Destination token symbol

    Returns:
        Timing suggestions
    """
    # This would integrate with gas price APIs in production
    # For now, provide general guidance

    return (
        f"Optimal Swap Timing: {src_token} → {dst_token}\n"
        f"\n"
        f"**Gas Price Considerations:**\n"
        f"• Lowest gas: Weekends, 2-6 AM UTC\n"
        f"• Highest gas: Weekdays, 2-6 PM UTC\n"
        f"• Current network: Monitor etherscan.io/gastracker\n"
        f"\n"
        f"**Market Volatility:**\n"
        f"• Major news events: Wait for stabilization\n"
        f"• High volatility: Consider limit orders\n"
        f"• Low liquidity hours: May have higher slippage\n"
        f"\n"
        f"**Best Practices:**\n"
        f"• Set gas price alerts\n"
        f"• Use 'Fast' gas during low congestion\n"
        f"• Consider Layer 2 (Polygon, Arbitrum) for lower fees\n"
        f"• Monitor 1-5 min before executing\n"
        f"\n"
        f"**Strategy:**\n"
        f"1. Check gas prices\n"
        f"2. Get fresh quote\n"
        f"3. Review price impact\n"
        f"4. Execute if conditions are favorable\n"
    )
