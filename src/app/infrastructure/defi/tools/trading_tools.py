"""
Trading tools for TradingAgent.
"""

import logging
from typing import Dict, Any
from decimal import Decimal

from app.infrastructure.defi.providers.hyperliquid import HyperliquidClient

logger = logging.getLogger(__name__)


async def get_position_info_tool(
    symbol: str,
    leverage: int,
    collateral: str,
    is_long: bool,
    hyperliquid_client: HyperliquidClient,
) -> str:
    """
    Get information about opening a position.

    Args:
        symbol: Trading pair (BTC, ETH, etc.)
        leverage: Leverage multiplier (1-100)
        collateral: Collateral amount in USD
        is_long: True for long, False for short
        hyperliquid_client: Hyperliquid API client

    Returns:
        Position information string
    """
    try:
        # Get current price
        price_data = await hyperliquid_client.get_market_price(symbol)
        # Simplified - in production would parse actual orderbook
        current_price = Decimal("50000")  # Mock price

        # Calculate position size
        collateral_dec = Decimal(collateral)
        position_size = collateral_dec * Decimal(leverage)

        # Calculate liquidation price
        liq_price = await hyperliquid_client.calculate_liquidation_price(
            entry_price=current_price,
            leverage=leverage,
            is_long=is_long,
        )

        # Get funding rate
        funding = await hyperliquid_client.get_funding_rate(symbol)
        funding_rate = funding.get("funding_rate", "0")

        direction = "LONG" if is_long else "SHORT"

        return (
            f"Position Preview: {leverage}x {direction} {symbol}\n"
            f"\n"
            f"**Position Details:**\n"
            f"• Direction: {direction}\n"
            f"• Leverage: {leverage}x\n"
            f"• Collateral: ${collateral}\n"
            f"• Position Size: ${position_size:,.2f}\n"
            f"• Current Price: ${current_price:,.2f}\n"
            f"\n"
            f"**Risk Metrics:**\n"
            f"• Liquidation Price: ${liq_price:,.2f}\n"
            f"• Distance to Liquidation: {abs((liq_price - current_price) / current_price * 100):.2f}%\n"
            f"• Funding Rate: {funding_rate}%/8h\n"
            f"\n"
            f"**⚠️ Risk Warning:**\n"
            f"• High leverage = high risk of liquidation\n"
            f"• Market can be volatile\n"
            f"• Always use stop losses\n"
            f"• Don't trade more than you can afford to lose\n"
        )

    except Exception as e:
        logger.error(f"Error getting position info: {e}")
        return f"Error: {str(e)}"


async def explain_perp_trading_tool(
    symbol: str,
) -> str:
    """
    Explain perpetual futures trading.

    Args:
        symbol: Trading pair symbol

    Returns:
        Explanation string
    """
    return (
        f"Perpetual Futures Trading Explained ({symbol}):\n"
        f"\n"
        f"**What are Perpetuals?**\n"
        f"• Futures contracts with no expiry date\n"
        f"• Trade with leverage (1x-100x)\n"
        f"• Can go long (bet on price increase) or short (bet on price decrease)\n"
        f"• Settled in USDC or other stablecoins\n"
        f"\n"
        f"**Key Concepts:**\n"
        f"\n"
        f"1. **Leverage**: Amplifies both gains and losses\n"
        f"   - 10x leverage: 1% price move = 10% gain/loss\n"
        f"   - Higher leverage = closer liquidation price\n"
        f"\n"
        f"2. **Liquidation**: Forced closure when losses approach collateral\n"
        f"   - Happens when mark price hits liquidation price\n"
        f"   - You lose your collateral\n"
        f"   - Always monitor your position!\n"
        f"\n"
        f"3. **Funding Rate**: Payment between longs and shorts\n"
        f"   - Paid every 8 hours\n"
        f"   - Positive: longs pay shorts (market is bullish)\n"
        f"   - Negative: shorts pay longs (market is bearish)\n"
        f"\n"
        f"4. **Mark Price**: Fair price used for liquidations\n"
        f"   - Based on spot price + funding\n"
        f"   - Prevents manipulation\n"
        f"\n"
        f"**Risk Management:**\n"
        f"• Start with low leverage (2x-5x)\n"
        f"• Always set stop losses\n"
        f"• Don't over-leverage\n"
        f"• Monitor funding rates\n"
        f"• Have an exit plan\n"
        f"\n"
        f"**Example:**\n"
        f"• Collateral: $1,000\n"
        f"• Leverage: 10x\n"
        f"• Position Size: $10,000\n"
        f"• Entry Price: $50,000\n"
        f"• Liquidation: ~$45,500 (long) or ~$54,500 (short)\n"
        f"• 10% price move = 100% gain or total loss\n"
    )


async def calculate_pnl_tool(
    entry_price: str,
    current_price: str,
    position_size: str,
    is_long: bool,
) -> str:
    """
    Calculate profit/loss for a position.

    Args:
        entry_price: Entry price
        current_price: Current market price
        position_size: Position size in USD
        is_long: True for long, False for short

    Returns:
        PnL calculation string
    """
    try:
        entry = Decimal(entry_price)
        current = Decimal(current_price)
        size = Decimal(position_size)

        # Calculate PnL
        price_change_pct = ((current - entry) / entry) * 100

        if not is_long:
            price_change_pct = -price_change_pct

        pnl_usd = size * (price_change_pct / 100)
        pnl_pct = price_change_pct

        direction = "LONG" if is_long else "SHORT"
        status = "✅ PROFIT" if pnl_usd > 0 else "❌ LOSS"

        return (
            f"PnL Calculation: {direction} Position\n"
            f"\n"
            f"**Position:**\n"
            f"• Entry Price: ${entry:,.2f}\n"
            f"• Current Price: ${current:,.2f}\n"
            f"• Position Size: ${size:,.2f}\n"
            f"• Direction: {direction}\n"
            f"\n"
            f"**Performance:**\n"
            f"• Price Change: {abs(price_change_pct):.2f}% {'↑' if current > entry else '↓'}\n"
            f"• PnL: {'+' if pnl_usd > 0 else ''}{pnl_pct:.2f}% (${pnl_usd:,.2f})\n"
            f"• Status: {status}\n"
        )

    except Exception as e:
        logger.error(f"Error calculating PnL: {e}")
        return f"Error: {str(e)}"
