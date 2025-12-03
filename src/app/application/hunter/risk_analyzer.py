"""ML-based risk analysis service.

Comprehensive risk scoring for cryptocurrency tokens using 4 factors:
1. Volatility Risk
2. Liquidity Risk
3. Smart Contract Risk
4. Market Correlation Risk

Based on Hunter AI Bot's risk assessment module.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

from app.application.hunter.price_data_service import PriceDataService


@dataclass
class RiskConfig:
    """Configuration for risk analysis."""

    # Volatility settings
    volatility_window: int = 30  # days
    high_volatility_threshold: float = 0.05  # 5% daily
    extreme_volatility_threshold: float = 0.10  # 10% daily

    # Liquidity settings
    min_daily_volume_usd: float = 1000000  # $1M
    liquidity_window: int = 7  # days

    # Smart contract settings
    audit_weight: float = 0.4
    bug_bounty_weight: float = 0.2
    code_quality_weight: float = 0.2
    centralization_weight: float = 0.2

    # Correlation settings
    correlation_window: int = 90  # days
    market_benchmark: str = "BTC"  # Compare against Bitcoin


@dataclass
class RiskScore:
    """Individual risk factor score."""

    factor: str
    score: float  # 0-100 (0 = low risk, 100 = high risk)
    level: str  # "low", "medium", "high", "extreme"
    details: Dict
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "factor": self.factor,
            "score": round(self.score, 2),
            "level": self.level,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CompositeRiskAssessment:
    """Complete risk assessment for a token."""

    token_symbol: str
    overall_risk_score: float  # 0-100
    overall_risk_level: str  # "low", "medium", "high", "extreme"
    risk_factors: Dict[str, RiskScore]
    recommendation: str
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token_symbol": self.token_symbol,
            "overall_risk_score": round(self.overall_risk_score, 2),
            "overall_risk_level": self.overall_risk_level,
            "risk_factors": {k: v.to_dict() for k, v in self.risk_factors.items()},
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class RiskAnalyzer:
    """ML-based risk analysis service.

    Analyzes cryptocurrency tokens across 4 risk dimensions:
    - Volatility (price stability)
    - Liquidity (trading volume)
    - Smart Contract (code security)
    - Market Correlation (systemic risk)
    """

    def __init__(
        self,
        config: RiskConfig = None,
        price_service: PriceDataService = None,
    ):
        """Initialize risk analyzer.

        Args:
            config: Risk analysis configuration
            price_service: Price data service
        """
        self.config = config or RiskConfig()
        self.price_service = price_service or PriceDataService()

    async def analyze_comprehensive_risk(
        self, token_symbol: str
    ) -> CompositeRiskAssessment:
        """Perform comprehensive risk analysis across all factors.

        Args:
            token_symbol: Token to analyze

        Returns:
            Complete risk assessment

        Example:
            >>> analyzer = RiskAnalyzer()
            >>> assessment = await analyzer.analyze_comprehensive_risk("ETH")
            >>> print(f"Overall risk: {assessment.overall_risk_level}")
        """
        # Analyze all risk factors
        volatility_risk = await self.analyze_volatility_risk(token_symbol)
        liquidity_risk = await self.analyze_liquidity_risk(token_symbol)
        smart_contract_risk = await self.analyze_smart_contract_risk(token_symbol)
        correlation_risk = await self.analyze_market_correlation_risk(token_symbol)

        # Combine scores (weighted average)
        weights = {
            "volatility": 0.30,
            "liquidity": 0.25,
            "smart_contract": 0.25,
            "correlation": 0.20,
        }

        overall_score = (
            volatility_risk.score * weights["volatility"]
            + liquidity_risk.score * weights["liquidity"]
            + smart_contract_risk.score * weights["smart_contract"]
            + correlation_risk.score * weights["correlation"]
        )

        overall_level = self._score_to_level(overall_score)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_score, overall_level, volatility_risk, liquidity_risk
        )

        return CompositeRiskAssessment(
            token_symbol=token_symbol,
            overall_risk_score=overall_score,
            overall_risk_level=overall_level,
            risk_factors={
                "volatility": volatility_risk,
                "liquidity": liquidity_risk,
                "smart_contract": smart_contract_risk,
                "correlation": correlation_risk,
            },
            recommendation=recommendation,
            timestamp=datetime.utcnow(),
        )

    async def analyze_volatility_risk(self, token_symbol: str) -> RiskScore:
        """Analyze price volatility risk.

        Measures:
        - Historical volatility (std dev)
        - Average daily range
        - Max drawdown
        - Sharp movements

        Args:
            token_symbol: Token to analyze

        Returns:
            Volatility risk score
        """
        # Fetch historical prices
        prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.volatility_window
        )

        closes = np.array([p.close for p in prices])
        returns = np.diff(closes) / closes[:-1]

        # Calculate volatility metrics
        volatility_std = np.std(returns)
        avg_daily_range = np.mean([p.high - p.low for p in prices]) / np.mean(closes)
        max_drawdown = self._calculate_max_drawdown(closes)
        sharp_moves = np.sum(np.abs(returns) > self.config.high_volatility_threshold)

        # Score calculation (0-100, higher = more risky)
        volatility_score = min(100, volatility_std * 100 * 20)  # Scale volatility
        range_score = min(100, avg_daily_range * 100 * 10)
        drawdown_score = min(100, abs(max_drawdown) * 100)
        sharp_score = min(100, (sharp_moves / len(returns)) * 100 * 5)

        overall_score = (
            volatility_score * 0.40
            + range_score * 0.25
            + drawdown_score * 0.25
            + sharp_score * 0.10
        )

        level = self._score_to_level(overall_score)

        return RiskScore(
            factor="volatility",
            score=overall_score,
            level=level,
            details={
                "historical_volatility": round(volatility_std * 100, 2),
                "avg_daily_range_pct": round(avg_daily_range * 100, 2),
                "max_drawdown_pct": round(max_drawdown * 100, 2),
                "sharp_movements": int(sharp_moves),
                "analysis_period_days": self.config.volatility_window,
            },
            timestamp=datetime.utcnow(),
        )

    async def analyze_liquidity_risk(self, token_symbol: str) -> RiskScore:
        """Analyze liquidity risk.

        Measures:
        - Average daily volume
        - Volume consistency
        - Bid-ask spread (simulated)
        - Slippage risk

        Args:
            token_symbol: Token to analyze

        Returns:
            Liquidity risk score
        """
        # Fetch recent price data
        prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.liquidity_window
        )

        volumes = np.array([p.volume for p in prices])
        avg_volume = np.mean(volumes)
        volume_std = np.std(volumes)
        volume_consistency = 1 - (volume_std / (avg_volume + 1e-8))

        # Score calculation (0-100, higher = more risky)
        # Low volume = high risk
        volume_score = max(
            0, 100 - (avg_volume / self.config.min_daily_volume_usd) * 100
        )
        consistency_score = (1 - volume_consistency) * 100

        # Simulated spread score (in production, fetch from exchange)
        spread_score = 20.0  # Assume moderate spread

        overall_score = (
            volume_score * 0.50 + consistency_score * 0.30 + spread_score * 0.20
        )

        level = self._score_to_level(overall_score)

        return RiskScore(
            factor="liquidity",
            score=overall_score,
            level=level,
            details={
                "avg_daily_volume_usd": round(avg_volume, 2),
                "volume_consistency": round(volume_consistency, 2),
                "estimated_spread_pct": 0.20,
                "analysis_period_days": self.config.liquidity_window,
            },
            timestamp=datetime.utcnow(),
        )

    async def analyze_smart_contract_risk(self, token_symbol: str) -> RiskScore:
        """Analyze smart contract security risk.

        Measures:
        - Security audit status
        - Bug bounty program
        - Code quality metrics
        - Centralization risks

        Args:
            token_symbol: Token to analyze

        Returns:
            Smart contract risk score

        Note:
            In production, this would integrate with:
            - CertiK API for audits
            - Immunefi for bug bounties
            - GitHub for code analysis
            - Blockchain explorers for on-chain metrics
        """
        # Simulated analysis (in production, fetch real data)
        # Major tokens like ETH, BTC have lower smart contract risk
        major_tokens = {"BTC", "ETH", "BNB", "SOL", "AVAX"}

        if token_symbol.upper() in major_tokens:
            audit_score = 10  # Fully audited
            bounty_score = 10  # Active bounty
            code_score = 15  # High quality
            centralization_score = 15  # Decentralized
        else:
            audit_score = 40  # Partial audit
            bounty_score = 30  # Limited bounty
            code_score = 35  # Moderate quality
            centralization_score = 35  # Some centralization

        overall_score = (
            audit_score * self.config.audit_weight
            + bounty_score * self.config.bug_bounty_weight
            + code_score * self.config.code_quality_weight
            + centralization_score * self.config.centralization_weight
        )

        level = self._score_to_level(overall_score)

        return RiskScore(
            factor="smart_contract",
            score=overall_score,
            level=level,
            details={
                "audit_status": "complete"
                if token_symbol.upper() in major_tokens
                else "partial",
                "bug_bounty": "active"
                if token_symbol.upper() in major_tokens
                else "limited",
                "code_quality": "high"
                if token_symbol.upper() in major_tokens
                else "medium",
                "centralization_risk": "low"
                if token_symbol.upper() in major_tokens
                else "medium",
            },
            timestamp=datetime.utcnow(),
        )

    async def analyze_market_correlation_risk(self, token_symbol: str) -> RiskScore:
        """Analyze market correlation risk.

        Measures correlation with market benchmark (BTC) to assess
        systemic risk exposure.

        High correlation = High systemic risk

        Args:
            token_symbol: Token to analyze

        Returns:
            Correlation risk score
        """
        # Fetch price data for token and benchmark
        token_prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.correlation_window
        )
        btc_prices = await self.price_service.fetch_historical_prices(
            self.config.market_benchmark, days=self.config.correlation_window
        )

        # Calculate returns
        token_closes = np.array([p.close for p in token_prices])
        btc_closes = np.array([p.close for p in btc_prices])

        token_returns = np.diff(token_closes) / token_closes[:-1]
        btc_returns = np.diff(btc_closes) / btc_closes[:-1]

        # Calculate correlation
        correlation = np.corrcoef(token_returns, btc_returns)[0, 1]

        # Score calculation (0-100)
        # High correlation = High systemic risk
        correlation_score = abs(correlation) * 100

        level = self._score_to_level(correlation_score)

        return RiskScore(
            factor="correlation",
            score=correlation_score,
            level=level,
            details={
                "correlation_with_btc": round(correlation, 3),
                "beta": round(correlation * (np.std(token_returns) / np.std(btc_returns)), 3),
                "systemic_risk_exposure": "high" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.4 else "low",
                "analysis_period_days": self.config.correlation_window,
            },
            timestamp=datetime.utcnow(),
        )

    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown from peak.

        Args:
            prices: Array of prices

        Returns:
            Max drawdown as decimal (e.g., -0.30 for 30% drop)
        """
        peak = np.maximum.accumulate(prices)
        drawdown = (prices - peak) / peak
        return float(np.min(drawdown))

    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level.

        Args:
            score: Risk score (0-100)

        Returns:
            Risk level string
        """
        if score < 25:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 75:
            return "high"
        else:
            return "extreme"

    def _generate_recommendation(
        self,
        overall_score: float,
        overall_level: str,
        volatility_risk: RiskScore,
        liquidity_risk: RiskScore,
    ) -> str:
        """Generate trading recommendation based on risk.

        Args:
            overall_score: Overall risk score
            overall_level: Overall risk level
            volatility_risk: Volatility risk score
            liquidity_risk: Liquidity risk score

        Returns:
            Recommendation string
        """
        if overall_level == "low":
            return "Low risk profile. Suitable for conservative portfolios with standard position sizing."
        elif overall_level == "medium":
            if volatility_risk.level in ["high", "extreme"]:
                return "Moderate risk with high volatility. Use tighter stop-losses and reduce position size by 30-50%."
            elif liquidity_risk.level in ["high", "extreme"]:
                return "Moderate risk with liquidity concerns. Limit position size and avoid large market orders."
            else:
                return "Moderate risk profile. Suitable for balanced portfolios with standard position sizing."
        elif overall_level == "high":
            return "High risk profile. Reduce position size by 50-70%. Use strict stop-losses and monitor closely."
        else:  # extreme
            return "Extreme risk detected. NOT recommended for most traders. If trading, use minimal position size (<5%) and very tight stops."
