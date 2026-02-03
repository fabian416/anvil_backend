"""
Position management tools for advanced trading.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def calculate_stop_loss_tool(
    entry_price: str,
    position_size: str,
    is_long: bool,
    risk_percentage: float = 2.0,
) -> str:
    """
    Calculate optimal stop loss for a position.

    Args:
        entry_price: Entry price
        position_size: Position size in USD
        is_long: True for long, False for short
        risk_percentage: Risk as % of position (default 2%)

    Returns:
        Stop loss recommendation
    """
    try:
        entry = Decimal(entry_price)
        size = Decimal(position_size)
        risk_pct = Decimal(str(risk_percentage))

        # Calculate stop loss price
        risk_move = risk_pct / 100

        if is_long:
            stop_loss = entry * (1 - risk_move)
        else:
            stop_loss = entry * (1 + risk_move)

        # Calculate loss at stop
        loss_usd = size * risk_move

        # Additional levels
        tight_stop = (
            entry * (1 - risk_move / 2) if is_long else entry * (1 + risk_move / 2)
        )
        wide_stop = (
            entry * (1 - risk_move * 2) if is_long else entry * (1 + risk_move * 2)
        )

        direction = "LONG" if is_long else "SHORT"

        return (
            f"Stop Loss Calculator: {direction} Position\n"
            f"\n"
            f"**Position Details:**\n"
            f"• Entry Price: ${entry:,.2f}\n"
            f"• Position Size: ${size:,.2f}\n"
            f"• Risk Tolerance: {risk_percentage}%\n"
            f"\n"
            f"**Recommended Stop Loss:**\n"
            f"• Price: ${stop_loss:,.2f}\n"
            f"• Distance: {abs((stop_loss - entry) / entry * 100):.2f}%\n"
            f"• Max Loss: ${loss_usd:,.2f}\n"
            f"\n"
            f"**Alternative Levels:**\n"
            f"• Tight Stop (1%): ${tight_stop:,.2f} (${loss_usd / 2:,.2f} loss)\n"
            f"• Wide Stop (4%): ${wide_stop:,.2f} (${loss_usd * 2:,.2f} loss)\n"
            f"\n"
            f"**Stop Loss Strategy:**\n"
            f"• Set immediately after entry\n"
            f"• Move to breakeven when in profit\n"
            f"• Trail stop as position moves favorably\n"
            f"• Never remove or widen stop loss\n"
        )

    except Exception as e:
        logger.error(f"Error calculating stop loss: {e}")
        return f"Error: {str(e)}"


async def calculate_take_profit_tool(
    entry_price: str,
    position_size: str,
    is_long: bool,
    reward_ratio: float = 2.0,
) -> str:
    """
    Calculate take profit levels.

    Args:
        entry_price: Entry price
        position_size: Position size in USD
        is_long: True for long, False for short
        reward_ratio: Reward/risk ratio (default 2:1)

    Returns:
        Take profit recommendations
    """
    try:
        entry = Decimal(entry_price)
        size = Decimal(position_size)

        # Assume 2% risk, so profit target is 2% * reward_ratio
        profit_pct = Decimal("0.02") * Decimal(str(reward_ratio))

        if is_long:
            tp1 = entry * (1 + profit_pct / 2)  # 50% at first target
            tp2 = entry * (1 + profit_pct)  # 50% at second target
        else:
            tp1 = entry * (1 - profit_pct / 2)
            tp2 = entry * (1 - profit_pct)

        profit_usd_1 = size * profit_pct / 2
        profit_usd_2 = size * profit_pct

        direction = "LONG" if is_long else "SHORT"

        return (
            f"Take Profit Strategy: {direction} Position\n"
            f"\n"
            f"**Position Details:**\n"
            f"• Entry Price: ${entry:,.2f}\n"
            f"• Position Size: ${size:,.2f}\n"
            f"• Risk/Reward: 1:{reward_ratio}\n"
            f"\n"
            f"**Profit Targets:**\n"
            f"• TP1 (50% position): ${tp1:,.2f} (+{abs((tp1 - entry) / entry * 100):.2f}%)\n"
            f"  → Profit: ${profit_usd_1:,.2f}\n"
            f"• TP2 (50% position): ${tp2:,.2f} (+{abs((tp2 - entry) / entry * 100):.2f}%)\n"
            f"  → Profit: ${profit_usd_1:,.2f}\n"
            f"• Total Profit: ${profit_usd_2:,.2f}\n"
            f"\n"
            f"**Execution Plan:**\n"
            f"1. Set TP1 at {reward_ratio / 2}:1 ratio\n"
            f"2. Take 50% profit at TP1\n"
            f"3. Move stop to breakeven\n"
            f"4. Let 50% run to TP2\n"
            f"5. Trail stop on remaining position\n"
        )

    except Exception as e:
        logger.error(f"Error calculating take profit: {e}")
        return f"Error: {str(e)}"


async def analyze_position_health_tool(
    entry_price: str,
    current_price: str,
    liquidation_price: str,
    position_size: str,
    is_long: bool,
) -> str:
    """
    Analyze position health and risk.

    Args:
        entry_price: Entry price
        current_price: Current market price
        liquidation_price: Liquidation price
        position_size: Position size in USD
        is_long: True for long, False for short

    Returns:
        Position health analysis
    """
    try:
        entry = Decimal(entry_price)
        current = Decimal(current_price)
        liq = Decimal(liquidation_price)
        size = Decimal(position_size)

        # Calculate PnL
        if is_long:
            pnl_pct = ((current - entry) / entry) * 100
        else:
            pnl_pct = ((entry - current) / entry) * 100

        pnl_usd = size * (pnl_pct / 100)

        # Distance to liquidation
        liq_distance_pct = abs((current - liq) / current) * 100

        # Health assessment
        if liq_distance_pct < 5:
            health = "🔴 CRITICAL - Close position immediately"
        elif liq_distance_pct < 10:
            health = "🟠 DANGER - Reduce leverage or add collateral"
        elif liq_distance_pct < 20:
            health = "🟡 WARNING - Monitor closely"
        else:
            health = "🟢 HEALTHY - Position is safe"

        direction = "LONG" if is_long else "SHORT"
        pnl_status = "✅ PROFIT" if pnl_usd > 0 else "❌ LOSS"

        return (
            f"Position Health Analysis: {direction}\n"
            f"\n"
            f"**Current Status:**\n"
            f"• Entry: ${entry:,.2f}\n"
            f"• Current: ${current:,.2f}\n"
            f"• PnL: {'+' if pnl_usd > 0 else ''}{pnl_pct:.2f}% (${pnl_usd:,.2f}) {pnl_status}\n"
            f"\n"
            f"**Risk Metrics:**\n"
            f"• Liquidation Price: ${liq:,.2f}\n"
            f"• Distance to Liq: {liq_distance_pct:.2f}%\n"
            f"• Health Status: {health}\n"
            f"\n"
            f"**Recommended Actions:**\n"
        )

        if liq_distance_pct < 10:
            return (
                f"Position Health Analysis: {direction}\n"
                f"\n"
                f"**Current Status:**\n"
                f"• Entry: ${entry:,.2f}\n"
                f"• Current: ${current:,.2f}\n"
                f"• PnL: {'+' if pnl_usd > 0 else ''}{pnl_pct:.2f}% (${pnl_usd:,.2f}) {pnl_status}\n"
                f"\n"
                f"**Risk Metrics:**\n"
                f"• Liquidation Price: ${liq:,.2f}\n"
                f"• Distance to Liq: {liq_distance_pct:.2f}%\n"
                f"• Health Status: {health}\n"
                f"\n"
                f"**⚠️ URGENT ACTIONS REQUIRED:**\n"
                f"1. Reduce position size immediately\n"
                f"2. Add more collateral if possible\n"
                f"3. Set emergency stop loss\n"
                f"4. Monitor price every 5-10 minutes\n"
            )
        elif pnl_usd > 0:
            return (
                f"Position Health Analysis: {direction}\n"
                f"\n"
                f"**Current Status:**\n"
                f"• Entry: ${entry:,.2f}\n"
                f"• Current: ${current:,.2f}\n"
                f"• PnL: +{pnl_pct:.2f}% (${pnl_usd:,.2f}) {pnl_status}\n"
                f"\n"
                f"**Risk Metrics:**\n"
                f"• Liquidation Price: ${liq:,.2f}\n"
                f"• Distance to Liq: {liq_distance_pct:.2f}%\n"
                f"• Health Status: {health}\n"
                f"\n"
                f"**Recommended Actions:**\n"
                f"1. Move stop loss to breakeven\n"
                f"2. Consider taking partial profits\n"
                f"3. Trail stop as position improves\n"
            )
        else:
            return (
                f"Position Health Analysis: {direction}\n"
                f"\n"
                f"**Current Status:**\n"
                f"• Entry: ${entry:,.2f}\n"
                f"• Current: ${current:,.2f}\n"
                f"• PnL: {pnl_pct:.2f}% (${pnl_usd:,.2f}) {pnl_status}\n"
                f"\n"
                f"**Risk Metrics:**\n"
                f"• Liquidation Price: ${liq:,.2f}\n"
                f"• Distance to Liq: {liq_distance_pct:.2f}%\n"
                f"• Health Status: {health}\n"
                f"\n"
                f"**Recommended Actions:**\n"
                f"1. Monitor stop loss\n"
                f"2. Review thesis - still valid?\n"
                f"3. Consider cutting loss if thesis broken\n"
                f"4. Wait for reversal confirmation\n"
            )

    except Exception as e:
        logger.error(f"Error analyzing position health: {e}")
        return f"Error: {str(e)}"
