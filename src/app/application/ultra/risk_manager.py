"""Risk Management for ULTRA Arbitrage Bot.

Implements comprehensive risk management:
- Position limits
- Stop-loss mechanisms
- Performance tracking
- Risk scoring
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app.domain.common.datetime_utils import utc_now
from decimal import Decimal


@dataclass
class RiskProfile:
    """Risk management profile."""

    # Position limits
    max_capital_per_trade: Decimal = Decimal("100000")  # $100K max
    max_daily_exposure: Decimal = Decimal("500000")  # $500K max daily
    max_concurrent_trades: int = 5  # Max 5 parallel

    # Profit thresholds
    min_profit_threshold: Decimal = Decimal("50.0")  # Min $50
    max_gas_price_gwei: int = 100  # Max 100 gwei
    max_slippage_percent: Decimal = Decimal("1.0")  # Max 1%

    # Stop-loss
    max_loss_per_trade: Decimal = Decimal("1000")  # Max $1K loss
    max_daily_loss: Decimal = Decimal("5000")  # Max $5K daily loss

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "max_capital_per_trade": str(self.max_capital_per_trade),
            "max_daily_exposure": str(self.max_daily_exposure),
            "max_concurrent_trades": self.max_concurrent_trades,
            "min_profit_threshold": str(self.min_profit_threshold),
            "max_gas_price_gwei": self.max_gas_price_gwei,
            "max_slippage_percent": float(self.max_slippage_percent),
            "max_loss_per_trade": str(self.max_loss_per_trade),
            "max_daily_loss": str(self.max_daily_loss),
        }


@dataclass
class TradeRecord:
    """Record of executed trade."""

    trade_id: str
    opportunity_id: str
    profit: Decimal
    gas_cost: Decimal
    capital_used: Decimal
    timestamp: datetime
    success: bool


@dataclass
class ExecutionMetrics:
    """Performance metrics."""

    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit: Decimal = Decimal("0")
    total_loss: Decimal = Decimal("0")
    total_gas_spent: Decimal = Decimal("0")
    average_profit: Decimal = Decimal("0")
    win_rate: float = 0.0
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "total_profit": str(self.total_profit),
            "total_loss": str(self.total_loss),
            "total_gas_spent": str(self.total_gas_spent),
            "average_profit": str(self.average_profit),
            "win_rate": round(self.win_rate * 100, 2),
            "largest_win": str(self.largest_win),
            "largest_loss": str(self.largest_loss),
        }


class RiskManager:
    """Risk management engine.

    Manages trading risks through:
    - Position sizing
    - Loss limits
    - Performance tracking
    """

    def __init__(self, profile: Optional[RiskProfile] = None):
        """Initialize risk manager.

        Args:
            profile: Risk profile
        """
        self.profile = profile or RiskProfile()
        self._trade_history: List[TradeRecord] = []
        self._active_trades: List[str] = []

    def check_position_limit(self, capital: Decimal) -> tuple[bool, Optional[str]]:
        """Check if position size is within limits.

        Args:
            capital: Capital to use

        Returns:
            (allowed, reason)
        """
        if capital > self.profile.max_capital_per_trade:
            return False, f"Capital ${capital} exceeds max ${self.profile.max_capital_per_trade}"

        # Check concurrent trades
        if len(self._active_trades) >= self.profile.max_concurrent_trades:
            return False, f"Max concurrent trades ({self.profile.max_concurrent_trades}) reached"

        # Check daily exposure
        today_exposure = self._get_daily_exposure()
        if today_exposure + capital > self.profile.max_daily_exposure:
            return False, f"Daily exposure ${today_exposure + capital} exceeds max ${self.profile.max_daily_exposure}"

        return True, None

    def check_stop_loss(self) -> tuple[bool, Optional[str]]:
        """Check if stop-loss limits are hit.

        Returns:
            (trading_allowed, reason)
        """
        # Check daily loss
        today_loss = self._get_daily_loss()
        if today_loss >= self.profile.max_daily_loss:
            return False, f"Daily loss ${today_loss} hit stop-loss ${self.profile.max_daily_loss}"

        return True, None

    def validate_trade(
        self, capital: Decimal, expected_profit: Decimal, gas_cost: Decimal
    ) -> tuple[bool, Optional[str]]:
        """Validate trade against risk limits.

        Args:
            capital: Capital required
            expected_profit: Expected profit
            gas_cost: Gas cost

        Returns:
            (allowed, reason)
        """
        # Check position limits
        allowed, reason = self.check_position_limit(capital)
        if not allowed:
            return False, reason

        # Check stop-loss
        allowed, reason = self.check_stop_loss()
        if not allowed:
            return False, reason

        # Check profitability
        net_profit = expected_profit - gas_cost
        if net_profit < self.profile.min_profit_threshold:
            return False, f"Net profit ${net_profit} below threshold ${self.profile.min_profit_threshold}"

        return True, None

    def record_trade(
        self,
        trade_id: str,
        opportunity_id: str,
        profit: Decimal,
        gas_cost: Decimal,
        capital: Decimal,
        success: bool,
    ) -> None:
        """Record completed trade.

        Args:
            trade_id: Trade ID
            opportunity_id: Opportunity ID
            profit: Realized profit
            gas_cost: Gas cost
            capital: Capital used
            success: Trade success
        """
        record = TradeRecord(
            trade_id=trade_id,
            opportunity_id=opportunity_id,
            profit=profit,
            gas_cost=gas_cost,
            capital_used=capital,
            timestamp=utc_now(),
            success=success,
        )

        self._trade_history.append(record)

        # Remove from active trades
        if trade_id in self._active_trades:
            self._active_trades.remove(trade_id)

    def start_trade(self, trade_id: str) -> None:
        """Mark trade as active.

        Args:
            trade_id: Trade ID
        """
        self._active_trades.append(trade_id)

    def get_metrics(self) -> ExecutionMetrics:
        """Get performance metrics.

        Returns:
            Execution metrics
        """
        if not self._trade_history:
            return ExecutionMetrics()

        metrics = ExecutionMetrics()

        for trade in self._trade_history:
            metrics.total_trades += 1

            if trade.success:
                metrics.successful_trades += 1
                metrics.total_profit += trade.profit
                if trade.profit > metrics.largest_win:
                    metrics.largest_win = trade.profit
            else:
                metrics.failed_trades += 1
                loss = abs(trade.profit) if trade.profit < 0 else Decimal("0")
                metrics.total_loss += loss
                if loss > metrics.largest_loss:
                    metrics.largest_loss = loss

            metrics.total_gas_spent += trade.gas_cost

        # Calculate averages
        if metrics.total_trades > 0:
            metrics.average_profit = metrics.total_profit / metrics.total_trades
            metrics.win_rate = metrics.successful_trades / metrics.total_trades

        return metrics

    def _get_daily_exposure(self) -> Decimal:
        """Get today's total exposure."""
        today = utc_now().date()
        exposure = Decimal("0")

        for trade in self._trade_history:
            if trade.timestamp.date() == today:
                exposure += trade.capital_used

        return exposure

    def _get_daily_loss(self) -> Decimal:
        """Get today's total loss."""
        today = utc_now().date()
        loss = Decimal("0")

        for trade in self._trade_history:
            if trade.timestamp.date() == today and not trade.success:
                loss += abs(trade.profit) if trade.profit < 0 else Decimal("0")

        return loss

    def get_risk_score(self) -> float:
        """Calculate current risk score (0-1, higher = riskier).

        Returns:
            Risk score
        """
        score = 0.0

        # Factor 1: Active trades (0-0.3)
        active_ratio = len(self._active_trades) / self.profile.max_concurrent_trades
        score += active_ratio * 0.3

        # Factor 2: Daily exposure (0-0.3)
        exposure = self._get_daily_exposure()
        exposure_ratio = min(exposure / self.profile.max_daily_exposure, Decimal("1.0"))
        score += float(exposure_ratio) * 0.3

        # Factor 3: Daily loss (0-0.4)
        loss = self._get_daily_loss()
        loss_ratio = min(loss / self.profile.max_daily_loss, Decimal("1.0"))
        score += float(loss_ratio) * 0.4

        return min(score, 1.0)
