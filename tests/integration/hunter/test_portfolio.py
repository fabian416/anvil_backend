"""Integration tests for Portfolio Optimization (Weeks 5-6).

Tests MPT implementation, efficient frontier, and portfolio analysis.
"""

import pytest
import numpy as np

from app.application.hunter.portfolio_optimizer import (
    PortfolioOptimizer,
    PortfolioConfig,
    OptimizedPortfolio,
    EfficientFrontier,
    PortfolioMetrics,
    RebalancingPlan,
)


class TestPortfolioConfig:
    """Test portfolio configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = PortfolioConfig()

        assert config.risk_tolerance == 0.5
        assert config.min_weight == 0.0
        assert config.max_weight == 1.0
        assert config.max_single_asset == 0.40
        assert config.risk_free_rate == 0.03


class TestPortfolioOptimization:
    """Test portfolio optimization."""

    @pytest.mark.asyncio
    async def test_optimize_portfolio_balanced(self):
        """Test balanced portfolio optimization (max Sharpe)."""
        optimizer = PortfolioOptimizer()

        portfolio = await optimizer.optimize_portfolio(["BTC", "ETH"], risk_tolerance=0.5)

        assert isinstance(portfolio, OptimizedPortfolio)
        assert len(portfolio.weights) == 2
        assert "BTC" in portfolio.weights
        assert "ETH" in portfolio.weights

        # Weights should sum to 1.0
        total_weight = sum(portfolio.weights.values())
        assert 0.99 <= total_weight <= 1.01

    @pytest.mark.asyncio
    async def test_optimize_portfolio_conservative(self):
        """Test conservative portfolio (min variance)."""
        optimizer = PortfolioOptimizer()

        portfolio = await optimizer.optimize_portfolio(["BTC", "ETH", "SOL"], risk_tolerance=0.2)

        assert len(portfolio.weights) == 3
        assert sum(portfolio.weights.values()) <= 1.01

    @pytest.mark.asyncio
    async def test_optimize_portfolio_aggressive(self):
        """Test aggressive portfolio (max return)."""
        optimizer = PortfolioOptimizer()

        portfolio = await optimizer.optimize_portfolio(["BTC", "ETH", "SOL"], risk_tolerance=0.9)

        assert len(portfolio.weights) == 3
        # Aggressive portfolio might concentrate in higher-return assets
        max_weight = max(portfolio.weights.values())
        assert max_weight <= 0.40  # Respects max_single_asset constraint


class TestPortfolioMetrics:
    """Test portfolio metrics calculation."""

    @pytest.mark.asyncio
    async def test_portfolio_has_all_metrics(self):
        """Test that optimized portfolio includes all metrics."""
        optimizer = PortfolioOptimizer()

        portfolio = await optimizer.optimize_portfolio(["BTC", "ETH"])

        metrics = portfolio.metrics
        assert isinstance(metrics, PortfolioMetrics)
        assert metrics.expected_return >= 0
        assert metrics.volatility >= 0
        assert metrics.sharpe_ratio is not None
        assert metrics.sortino_ratio is not None
        assert metrics.max_drawdown <= 0  # Should be negative
        assert 0 <= metrics.diversification_score <= 1
        assert metrics.var_95 <= 0  # VaR is negative


class TestEfficientFrontier:
    """Test efficient frontier calculation."""

    @pytest.mark.asyncio
    async def test_calculate_efficient_frontier(self):
        """Test efficient frontier calculation."""
        optimizer = PortfolioOptimizer()

        frontier = await optimizer.calculate_efficient_frontier(["BTC", "ETH"])

        assert isinstance(frontier, EfficientFrontier)
        assert len(frontier.returns) > 0
        assert len(frontier.risks) > 0
        assert len(frontier.sharpe_ratios) > 0
        assert len(frontier.weights) > 0

        # Same number of points for each
        assert len(frontier.returns) == len(frontier.risks)
        assert len(frontier.returns) == len(frontier.sharpe_ratios)

    @pytest.mark.asyncio
    async def test_frontier_has_max_sharpe(self):
        """Test that frontier identifies max Sharpe portfolio."""
        optimizer = PortfolioOptimizer()

        frontier = await optimizer.calculate_efficient_frontier(["BTC", "ETH", "SOL"])

        # Max Sharpe index should be valid
        assert 0 <= frontier.max_sharpe_idx < len(frontier.returns)

        # Max Sharpe should be the highest
        max_sharpe = max(frontier.sharpe_ratios)
        assert frontier.sharpe_ratios[frontier.max_sharpe_idx] == max_sharpe

    @pytest.mark.asyncio
    async def test_frontier_has_min_volatility(self):
        """Test that frontier identifies min volatility portfolio."""
        optimizer = PortfolioOptimizer()

        frontier = await optimizer.calculate_efficient_frontier(["BTC", "ETH", "SOL"])

        # Min vol index should be valid
        assert 0 <= frontier.min_vol_idx < len(frontier.risks)

        # Min vol should be the lowest
        min_vol = min(frontier.risks)
        assert frontier.risks[frontier.min_vol_idx] == min_vol


class TestPortfolioAnalysis:
    """Test portfolio analysis."""

    @pytest.mark.asyncio
    async def test_analyze_portfolio(self):
        """Test analyzing existing portfolio."""
        optimizer = PortfolioOptimizer()

        # Equal-weighted portfolio
        portfolio = {"BTC": 0.5, "ETH": 0.5}
        metrics = await optimizer.analyze_portfolio(portfolio)

        assert isinstance(metrics, PortfolioMetrics)
        assert metrics.expected_return >= 0
        assert metrics.volatility >= 0


class TestRebalancing:
    """Test portfolio rebalancing."""

    @pytest.mark.asyncio
    async def test_suggest_rebalancing(self):
        """Test rebalancing suggestions."""
        optimizer = PortfolioOptimizer()

        current = {"BTC": 0.7, "ETH": 0.3}
        plan = await optimizer.suggest_rebalancing(current, risk_tolerance=0.5)

        assert isinstance(plan, RebalancingPlan)
        assert len(plan.current_weights) == 2
        assert len(plan.target_weights) == 2
        assert len(plan.changes) == 2

        # Changes should reflect difference between current and target
        for token in current.keys():
            expected_change = plan.target_weights[token] - plan.current_weights[token]
            assert abs(plan.changes[token] - expected_change) < 0.01

    @pytest.mark.asyncio
    async def test_rebalancing_trades(self):
        """Test that rebalancing generates trade recommendations."""
        optimizer = PortfolioOptimizer()

        current = {"BTC": 0.8, "ETH": 0.2}
        plan = await optimizer.suggest_rebalancing(current)

        # Should have some trade recommendations
        assert isinstance(plan.trades, list)
        # Trades should have correct structure
        for trade in plan.trades:
            assert "token" in trade
            assert "action" in trade
            assert trade["action"] in ["BUY", "SELL"]


class TestPortfolioSerialization:
    """Test portfolio serialization."""

    @pytest.mark.asyncio
    async def test_portfolio_to_dict(self):
        """Test portfolio serialization."""
        optimizer = PortfolioOptimizer()

        portfolio = await optimizer.optimize_portfolio(["BTC", "ETH"])
        data = portfolio.to_dict()

        # Verify structure
        assert "weights" in data
        assert "metrics" in data
        assert "timestamp" in data

        # Weights as percentages
        for weight in data["weights"].values():
            assert 0 <= weight <= 100

    @pytest.mark.asyncio
    async def test_frontier_to_dict(self):
        """Test efficient frontier serialization."""
        optimizer = PortfolioOptimizer()

        frontier = await optimizer.calculate_efficient_frontier(["BTC", "ETH"])
        data = frontier.to_dict()

        # Verify structure
        assert "returns" in data
        assert "risks" in data
        assert "sharpe_ratios" in data
        assert "max_sharpe_portfolio" in data
        assert "min_volatility_portfolio" in data
