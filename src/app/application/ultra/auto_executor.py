"""Auto-Execution System for ULTRA Arbitrage Bot.

Implements automated arbitrage execution with risk management.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum

from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery
from app.application.ultra.arbitrage_executor import ArbitrageExecutor
from app.application.ultra.risk_manager import RiskManager, RiskProfile


class AutoExecutorStatus(str, Enum):
    """Auto-executor status."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class AutoExecutorConfig:
    """Configuration for auto-executor."""

    # Execution settings
    scan_interval_seconds: int = 5  # Scan every 5 seconds
    min_profit_usd: Decimal = Decimal("50.0")  # Min $50 profit
    max_gas_price_gwei: int = 100  # Max 100 gwei

    # Risk settings
    risk_profile: RiskProfile = None

    # Performance
    enable_mev_protection: bool = True  # Always use MEV protection
    enable_simulation: bool = True  # Simulate before execution

    def __post_init__(self):
        """Initialize risk profile if not provided."""
        if self.risk_profile is None:
            self.risk_profile = RiskProfile()


class AutoExecutor:
    """Automated arbitrage executor.

    Continuously scans for opportunities and executes profitable trades
    with integrated risk management.
    """

    def __init__(
        self,
        config: Optional[AutoExecutorConfig] = None,
        discovery: Optional[ArbitrageDiscovery] = None,
        executor: Optional[ArbitrageExecutor] = None,
        risk_manager: Optional[RiskManager] = None,
    ):
        """Initialize auto-executor.

        Args:
            config: Configuration
            discovery: Arbitrage discovery
            executor: Arbitrage executor
            risk_manager: Risk manager
        """
        self.config = config or AutoExecutorConfig()
        self.discovery = discovery or ArbitrageDiscovery()
        self.executor = executor or ArbitrageExecutor()
        self.risk_manager = risk_manager or RiskManager(self.config.risk_profile)

        self._status = AutoExecutorStatus.STOPPED
        self._execution_count = 0
        self._last_scan_time: Optional[datetime] = None

    async def start(self) -> Dict:
        """Start auto-executor.

        Returns:
            Status message
        """
        if self._status == AutoExecutorStatus.RUNNING:
            return {
                "status": "already_running",
                "message": "Auto-executor already running",
            }

        self._status = AutoExecutorStatus.RUNNING
        return {
            "status": "started",
            "message": "Auto-executor started",
            "config": {
                "scan_interval": self.config.scan_interval_seconds,
                "min_profit": str(self.config.min_profit_usd),
                "mev_protection": self.config.enable_mev_protection,
            },
        }

    async def stop(self) -> Dict:
        """Stop auto-executor.

        Returns:
            Status message
        """
        if self._status == AutoExecutorStatus.STOPPED:
            return {
                "status": "already_stopped",
                "message": "Auto-executor already stopped",
            }

        self._status = AutoExecutorStatus.STOPPED
        return {
            "status": "stopped",
            "message": "Auto-executor stopped",
            "executions": self._execution_count,
        }

    async def pause(self) -> Dict:
        """Pause auto-executor.

        Returns:
            Status message
        """
        if self._status != AutoExecutorStatus.RUNNING:
            return {"status": "not_running", "message": "Auto-executor not running"}

        self._status = AutoExecutorStatus.PAUSED
        return {"status": "paused", "message": "Auto-executor paused"}

    async def resume(self) -> Dict:
        """Resume auto-executor.

        Returns:
            Status message
        """
        if self._status != AutoExecutorStatus.PAUSED:
            return {"status": "not_paused", "message": "Auto-executor not paused"}

        self._status = AutoExecutorStatus.RUNNING
        return {"status": "resumed", "message": "Auto-executor resumed"}

    async def scan_and_execute(self) -> Dict:
        """Scan for opportunities and execute if profitable.

        Returns:
            Scan result
        """
        if self._status != AutoExecutorStatus.RUNNING:
            return {"status": "not_running", "opportunities_found": 0, "executed": 0}

        self._last_scan_time = datetime.now(UTC)

        # Discover opportunities
        opportunities = await self.discovery.discover_all_opportunities(
            Decimal("10000")
        )

        # Filter by profitability
        profitable = [
            opp
            for opp in opportunities
            if opp.expected_profit_usd >= self.config.min_profit_usd
        ]

        executed = 0
        failed = 0

        for opp in profitable:
            # Check risk limits
            allowed, reason = self.risk_manager.validate_trade(
                capital=opp.required_capital,
                expected_profit=opp.expected_profit_usd,
                gas_cost=opp.estimated_gas_cost,
            )

            if not allowed:
                failed += 1
                continue

            # Mark as active
            trade_id = f"AUTO-{self._execution_count:04d}"
            self.risk_manager.start_trade(trade_id)

            # Execute
            try:
                result = await self.executor.execute_opportunity(
                    opp, use_mev_protection=self.config.enable_mev_protection
                )

                # Record result
                self.risk_manager.record_trade(
                    trade_id=trade_id,
                    opportunity_id=opp.opportunity_id,
                    profit=result.realized_profit or Decimal("0"),
                    gas_cost=result.gas_cost,
                    capital=opp.required_capital,
                    success=(result.status.value == "success"),
                )

                executed += 1
                self._execution_count += 1

            except Exception:
                # Record failure
                self.risk_manager.record_trade(
                    trade_id=trade_id,
                    opportunity_id=opp.opportunity_id,
                    profit=Decimal("0"),
                    gas_cost=Decimal("0"),
                    capital=opp.required_capital,
                    success=False,
                )
                failed += 1

        return {
            "status": "completed",
            "opportunities_found": len(opportunities),
            "profitable_opportunities": len(profitable),
            "executed": executed,
            "failed": failed,
            "timestamp": self._last_scan_time.isoformat(),
        }

    def get_status(self) -> Dict:
        """Get current status.

        Returns:
            Status information
        """
        metrics = self.risk_manager.get_metrics()
        risk_score = self.risk_manager.get_risk_score()

        return {
            "status": self._status.value,
            "total_executions": self._execution_count,
            "last_scan": self._last_scan_time.isoformat()
            if self._last_scan_time
            else None,
            "metrics": metrics.to_dict(),
            "risk_score": round(risk_score * 100, 2),
            "config": {
                "scan_interval": self.config.scan_interval_seconds,
                "min_profit": str(self.config.min_profit_usd),
                "mev_protection": self.config.enable_mev_protection,
            },
        }

    def update_config(self, **kwargs) -> Dict:
        """Update configuration.

        Args:
            **kwargs: Configuration parameters

        Returns:
            Updated configuration
        """
        if "min_profit_usd" in kwargs:
            self.config.min_profit_usd = Decimal(str(kwargs["min_profit_usd"]))

        if "scan_interval_seconds" in kwargs:
            self.config.scan_interval_seconds = int(kwargs["scan_interval_seconds"])

        if "max_gas_price_gwei" in kwargs:
            self.config.max_gas_price_gwei = int(kwargs["max_gas_price_gwei"])

        if "enable_mev_protection" in kwargs:
            self.config.enable_mev_protection = bool(kwargs["enable_mev_protection"])

        return {
            "status": "updated",
            "config": {
                "scan_interval": self.config.scan_interval_seconds,
                "min_profit": str(self.config.min_profit_usd),
                "max_gas_price": self.config.max_gas_price_gwei,
                "mev_protection": self.config.enable_mev_protection,
            },
        }
