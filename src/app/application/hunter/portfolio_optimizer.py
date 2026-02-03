"""Portfolio optimization using Modern Portfolio Theory (MPT).

Implements mean-variance optimization, efficient frontier calculation,
and portfolio analysis based on Markowitz's MPT.

Based on Hunter AI Bot's portfolio optimization module.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from app.domain.common.datetime_utils import utc_now
import numpy as np
from scipy.optimize import minimize
import warnings

from app.application.hunter.price_data_service import PriceDataService

# Suppress optimization warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


@dataclass
class PortfolioConfig:
    """Configuration for portfolio optimization."""

    # Risk tolerance (0-1, where 0=conservative, 1=aggressive)
    risk_tolerance: float = 0.5

    # Constraints
    min_weight: float = 0.0  # Minimum asset weight (no short selling)
    max_weight: float = 1.0  # Maximum asset weight
    max_single_asset: float = 0.40  # Max 40% in any single asset

    # Risk-free rate (annual)
    risk_free_rate: float = 0.03  # 3% annual

    # Historical data window
    history_days: int = 365  # 1 year of data

    # Efficient frontier points
    frontier_points: int = 50


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""

    expected_return: float  # Annual expected return
    volatility: float  # Annual volatility (std dev)
    sharpe_ratio: float  # Risk-adjusted return
    sortino_ratio: float  # Downside risk-adjusted return
    max_drawdown: float  # Maximum peak-to-trough decline
    diversification_score: float  # 0-1, portfolio diversification
    var_95: float  # Value at Risk (95% confidence)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "expected_return": round(self.expected_return * 100, 2),  # As %
            "volatility": round(self.volatility * 100, 2),  # As %
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "max_drawdown": round(self.max_drawdown * 100, 2),  # As %
            "diversification_score": round(self.diversification_score, 2),
            "var_95": round(self.var_95 * 100, 2),  # As %
        }


@dataclass
class OptimizedPortfolio:
    """Optimized portfolio allocation."""

    weights: Dict[str, float]  # Asset weights
    metrics: PortfolioMetrics
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "weights": {k: round(v * 100, 2) for k, v in self.weights.items()},  # As %
            "metrics": self.metrics.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EfficientFrontier:
    """Efficient frontier data."""

    returns: List[float]  # Expected returns
    risks: List[float]  # Volatilities
    sharpe_ratios: List[float]  # Sharpe ratios
    weights: List[Dict[str, float]]  # Portfolio weights for each point
    max_sharpe_idx: int  # Index of max Sharpe ratio portfolio
    min_vol_idx: int  # Index of minimum volatility portfolio

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "returns": [round(r * 100, 2) for r in self.returns],
            "risks": [round(r * 100, 2) for r in self.risks],
            "sharpe_ratios": [round(s, 2) for s in self.sharpe_ratios],
            "max_sharpe_portfolio": {
                "return": round(self.returns[self.max_sharpe_idx] * 100, 2),
                "risk": round(self.risks[self.max_sharpe_idx] * 100, 2),
                "sharpe": round(self.sharpe_ratios[self.max_sharpe_idx], 2),
                "weights": {
                    k: round(v * 100, 2)
                    for k, v in self.weights[self.max_sharpe_idx].items()
                },
            },
            "min_volatility_portfolio": {
                "return": round(self.returns[self.min_vol_idx] * 100, 2),
                "risk": round(self.risks[self.min_vol_idx] * 100, 2),
                "sharpe": round(self.sharpe_ratios[self.min_vol_idx], 2),
                "weights": {
                    k: round(v * 100, 2)
                    for k, v in self.weights[self.min_vol_idx].items()
                },
            },
        }


@dataclass
class RebalancingPlan:
    """Portfolio rebalancing recommendations."""

    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    changes: Dict[str, float]  # Weight changes needed
    trades: List[Dict]  # Specific trade recommendations
    estimated_cost: float  # Estimated trading costs
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "current_weights": {
                k: round(v * 100, 2) for k, v in self.current_weights.items()
            },
            "target_weights": {
                k: round(v * 100, 2) for k, v in self.target_weights.items()
            },
            "changes": {k: round(v * 100, 2) for k, v in self.changes.items()},
            "trades": self.trades,
            "estimated_cost": round(self.estimated_cost * 100, 2),  # As %
            "timestamp": self.timestamp.isoformat(),
        }


class PortfolioOptimizer:
    """Modern Portfolio Theory optimizer.

    Implements:
    - Mean-variance optimization
    - Efficient frontier calculation
    - Risk-adjusted portfolio metrics
    - Portfolio rebalancing recommendations
    """

    def __init__(
        self,
        config: PortfolioConfig = None,
        price_service: PriceDataService = None,
    ):
        """Initialize portfolio optimizer.

        Args:
            config: Portfolio optimization configuration
            price_service: Price data service
        """
        self.config = config or PortfolioConfig()
        self.price_service = price_service or PriceDataService()

    async def optimize_portfolio(
        self,
        tokens: List[str],
        risk_tolerance: Optional[float] = None,
    ) -> OptimizedPortfolio:
        """Optimize portfolio allocation.

        Args:
            tokens: List of token symbols
            risk_tolerance: Risk tolerance (0-1), uses config default if None

        Returns:
            Optimized portfolio with weights and metrics

        Example:
            >>> optimizer = PortfolioOptimizer()
            >>> portfolio = await optimizer.optimize_portfolio(["BTC", "ETH", "SOL"])
            >>> print(portfolio.weights)
        """
        risk_tol = (
            risk_tolerance if risk_tolerance is not None else self.config.risk_tolerance
        )

        # Fetch historical data
        returns, cov_matrix = await self._get_returns_and_covariance(tokens)

        # Calculate expected returns (simple historical mean)
        expected_returns = returns.mean(axis=0)

        # Optimize based on risk tolerance
        if risk_tol < 0.33:
            # Conservative: Minimize variance
            weights = self._optimize_min_variance(expected_returns, cov_matrix)
        elif risk_tol > 0.67:
            # Aggressive: Maximize return with risk constraint
            weights = self._optimize_max_return(expected_returns, cov_matrix, risk_tol)
        else:
            # Balanced: Maximize Sharpe ratio
            weights = self._optimize_max_sharpe(expected_returns, cov_matrix)

        # Create weight dictionary
        weight_dict = {token: float(w) for token, w in zip(tokens, weights)}

        # Calculate portfolio metrics
        metrics = self._calculate_portfolio_metrics(
            weights, expected_returns, cov_matrix, returns
        )

        return OptimizedPortfolio(
            weights=weight_dict,
            metrics=metrics,
            timestamp=utc_now(),
        )

    async def calculate_efficient_frontier(
        self, tokens: List[str]
    ) -> EfficientFrontier:
        """Calculate efficient frontier.

        Args:
            tokens: List of token symbols

        Returns:
            Efficient frontier data

        Example:
            >>> optimizer = PortfolioOptimizer()
            >>> frontier = await optimizer.calculate_efficient_frontier(["BTC", "ETH"])
            >>> print(f"Max Sharpe return: {frontier.returns[frontier.max_sharpe_idx]}")
        """
        # Fetch historical data
        returns, cov_matrix = await self._get_returns_and_covariance(tokens)
        expected_returns = returns.mean(axis=0)

        # Generate frontier
        target_returns = np.linspace(
            expected_returns.min(), expected_returns.max(), self.config.frontier_points
        )

        frontier_returns = []
        frontier_risks = []
        frontier_sharpes = []
        frontier_weights = []

        for target_return in target_returns:
            try:
                weights = self._optimize_for_target_return(
                    expected_returns, cov_matrix, target_return
                )

                port_return = np.dot(weights, expected_returns)
                port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                sharpe = (port_return - self.config.risk_free_rate) / port_vol

                frontier_returns.append(float(port_return))
                frontier_risks.append(float(port_vol))
                frontier_sharpes.append(float(sharpe))
                frontier_weights.append({
                    token: float(w) for token, w in zip(tokens, weights)
                })
            except:
                # Skip infeasible points
                continue

        # Find max Sharpe and min volatility
        max_sharpe_idx = int(np.argmax(frontier_sharpes))
        min_vol_idx = int(np.argmin(frontier_risks))

        return EfficientFrontier(
            returns=frontier_returns,
            risks=frontier_risks,
            sharpe_ratios=frontier_sharpes,
            weights=frontier_weights,
            max_sharpe_idx=max_sharpe_idx,
            min_vol_idx=min_vol_idx,
        )

    async def analyze_portfolio(self, portfolio: Dict[str, float]) -> PortfolioMetrics:
        """Analyze existing portfolio.

        Args:
            portfolio: Current portfolio weights (token: weight)

        Returns:
            Portfolio metrics

        Example:
            >>> optimizer = PortfolioOptimizer()
            >>> metrics = await optimizer.analyze_portfolio({"BTC": 0.6, "ETH": 0.4})
            >>> print(f"Sharpe ratio: {metrics.sharpe_ratio}")
        """
        tokens = list(portfolio.keys())
        weights = np.array([portfolio[token] for token in tokens])

        # Fetch historical data
        returns, cov_matrix = await self._get_returns_and_covariance(tokens)
        expected_returns = returns.mean(axis=0)

        # Calculate metrics
        return self._calculate_portfolio_metrics(
            weights, expected_returns, cov_matrix, returns
        )

    async def suggest_rebalancing(
        self,
        current_portfolio: Dict[str, float],
        risk_tolerance: Optional[float] = None,
    ) -> RebalancingPlan:
        """Suggest portfolio rebalancing.

        Args:
            current_portfolio: Current portfolio weights
            risk_tolerance: Risk tolerance (0-1)

        Returns:
            Rebalancing plan

        Example:
            >>> optimizer = PortfolioOptimizer()
            >>> plan = await optimizer.suggest_rebalancing({"BTC": 0.7, "ETH": 0.3})
            >>> print(plan.changes)
        """
        tokens = list(current_portfolio.keys())

        # Optimize for target allocation
        optimized = await self.optimize_portfolio(tokens, risk_tolerance)

        # Calculate changes needed
        changes = {
            token: optimized.weights[token] - current_portfolio[token]
            for token in tokens
        }

        # Generate trade recommendations
        trades = []
        for token, change in changes.items():
            if abs(change) > 0.01:  # Only recommend if >1% change
                action = "BUY" if change > 0 else "SELL"
                trades.append({
                    "token": token,
                    "action": action,
                    "change_pct": round(change * 100, 2),
                })

        # Estimate trading costs (assume 0.1% per trade)
        estimated_cost = sum(abs(change) for change in changes.values()) * 0.001

        return RebalancingPlan(
            current_weights=current_portfolio,
            target_weights=optimized.weights,
            changes=changes,
            trades=trades,
            estimated_cost=estimated_cost,
            timestamp=utc_now(),
        )

    async def _get_returns_and_covariance(
        self, tokens: List[str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Get returns and covariance matrix.

        Args:
            tokens: List of tokens

        Returns:
            (returns matrix, covariance matrix)
        """
        # Fetch price data for all tokens
        all_returns = []
        for token in tokens:
            prices = await self.price_service.fetch_historical_prices(
                token, days=self.config.history_days
            )
            closes = np.array([p.close for p in prices])
            returns = np.diff(closes) / closes[:-1]
            all_returns.append(returns)

        # Stack returns (pad to same length)
        min_length = min(len(r) for r in all_returns)
        returns_matrix = np.column_stack([r[:min_length] for r in all_returns])

        # Calculate covariance matrix (annualized)
        cov_matrix = np.cov(returns_matrix.T) * 252  # Annualize (252 trading days)

        return returns_matrix, cov_matrix

    def _optimize_max_sharpe(
        self, expected_returns: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """Optimize for maximum Sharpe ratio.

        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix

        Returns:
            Optimal weights
        """
        n_assets = len(expected_returns)

        def neg_sharpe(weights):
            port_return = np.dot(weights, expected_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(port_return - self.config.risk_free_rate) / port_vol

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        # Only apply max_single_asset if we have 3+ assets
        max_per_asset = self.config.max_single_asset if n_assets >= 3 else 1.0
        bounds = tuple((self.config.min_weight, max_per_asset) for _ in range(n_assets))
        initial_guess = np.array([1 / n_assets] * n_assets)

        result = minimize(
            neg_sharpe,
            initial_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x

    def _optimize_min_variance(
        self, expected_returns: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """Optimize for minimum variance.

        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix

        Returns:
            Optimal weights
        """
        n_assets = len(expected_returns)

        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        # Only apply max_single_asset if we have 3+ assets
        max_per_asset = self.config.max_single_asset if n_assets >= 3 else 1.0
        bounds = tuple((self.config.min_weight, max_per_asset) for _ in range(n_assets))
        initial_guess = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_variance,
            initial_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x

    def _optimize_max_return(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        risk_tolerance: float,
    ) -> np.ndarray:
        """Optimize for maximum return with risk constraint.

        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            risk_tolerance: Risk tolerance level

        Returns:
            Optimal weights
        """
        n_assets = len(expected_returns)

        def neg_return(weights):
            return -np.dot(weights, expected_returns)

        # Risk constraint based on tolerance
        max_volatility = 0.20 + (risk_tolerance * 0.30)  # 20-50% vol range

        def risk_constraint(weights):
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return max_volatility - port_vol

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "ineq", "fun": risk_constraint},
        ]
        # Only apply max_single_asset if we have 3+ assets
        max_per_asset = self.config.max_single_asset if n_assets >= 3 else 1.0
        bounds = tuple((self.config.min_weight, max_per_asset) for _ in range(n_assets))
        initial_guess = np.array([1 / n_assets] * n_assets)

        result = minimize(
            neg_return,
            initial_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x

    def _optimize_for_target_return(
        self, expected_returns: np.ndarray, cov_matrix: np.ndarray, target_return: float
    ) -> np.ndarray:
        """Optimize for target return (efficient frontier point).

        Args:
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            target_return: Target portfolio return

        Returns:
            Optimal weights
        """
        n_assets = len(expected_returns)

        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {
                "type": "eq",
                "fun": lambda w: np.dot(w, expected_returns) - target_return,
            },
        ]
        # Only apply max_single_asset if we have 3+ assets
        max_per_asset = self.config.max_single_asset if n_assets >= 3 else 1.0
        bounds = tuple((self.config.min_weight, max_per_asset) for _ in range(n_assets))
        initial_guess = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_variance,
            initial_guess,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x

    def _calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        returns_matrix: np.ndarray,
    ) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics.

        Args:
            weights: Portfolio weights
            expected_returns: Expected returns vector
            cov_matrix: Covariance matrix
            returns_matrix: Historical returns matrix

        Returns:
            Portfolio metrics
        """
        # Portfolio return and volatility
        port_return = float(np.dot(weights, expected_returns))
        port_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))

        # Sharpe ratio
        sharpe = (port_return - self.config.risk_free_rate) / port_vol

        # Sortino ratio (downside deviation)
        portfolio_returns = returns_matrix @ weights
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_dev = (
            np.std(downside_returns) * np.sqrt(252)
            if len(downside_returns) > 0
            else port_vol
        )
        sortino = (
            (port_return - self.config.risk_free_rate) / downside_dev
            if downside_dev > 0
            else 0.0
        )

        # Maximum drawdown
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_dd = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

        # Diversification score (effective number of assets)
        herfindahl = np.sum(weights**2)
        diversification = (
            (1 - herfindahl) / (1 - 1 / len(weights)) if len(weights) > 1 else 0.0
        )

        # Value at Risk (95% confidence)
        var_95 = float(np.percentile(portfolio_returns, 5))

        return PortfolioMetrics(
            expected_return=port_return,
            volatility=port_vol,
            sharpe_ratio=float(sharpe),
            sortino_ratio=float(sortino),
            max_drawdown=max_dd,
            diversification_score=float(diversification),
            var_95=var_95,
        )
