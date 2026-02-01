"""Integration tests for ML Risk Analysis (Week 2).

Tests risk analyzer across 4 factors and comprehensive assessment.
"""

import pytest
import numpy as np

from app.application.hunter.risk_analyzer import (
    RiskAnalyzer,
    RiskConfig,
    RiskScore,
    CompositeRiskAssessment,
)
from app.application.hunter.price_data_service import PriceDataService


class TestRiskConfig:
    """Test risk configuration."""

    def test_risk_config_defaults(self):
        """Test default configuration values."""
        config = RiskConfig()

        assert config.volatility_window == 30
        assert config.liquidity_window == 7
        assert config.correlation_window == 90
        assert config.market_benchmark == "BTC"

    def test_risk_config_custom(self):
        """Test custom configuration."""
        config = RiskConfig(
            volatility_window=60,
            min_daily_volume_usd=5000000,
            correlation_window=120,
        )

        assert config.volatility_window == 60
        assert config.min_daily_volume_usd == 5000000
        assert config.correlation_window == 120


class TestVolatilityRisk:
    """Test volatility risk analysis."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analyze_volatility_risk(self):
        """Test volatility risk analysis."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_volatility_risk("ETH")

        assert risk.factor == "volatility"
        assert 0 <= risk.score <= 100
        assert risk.level in ["low", "medium", "high", "extreme"]
        assert "historical_volatility" in risk.details
        assert "max_drawdown_pct" in risk.details
        assert "sharp_movements" in risk.details

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_volatility_risk_details(self):
        """Test volatility risk details structure."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_volatility_risk("BTC")

        details = risk.details
        assert isinstance(details["historical_volatility"], (int, float))
        assert isinstance(details["avg_daily_range_pct"], (int, float))
        assert isinstance(details["max_drawdown_pct"], (int, float))
        assert isinstance(details["sharp_movements"], int)
        assert details["analysis_period_days"] == 30

    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        analyzer = RiskAnalyzer()

        # Test with known sequence
        prices = np.array([100, 110, 105, 90, 95, 100])
        max_dd = analyzer._calculate_max_drawdown(prices)

        # Max drawdown should be from 110 to 90 = -18.18%
        assert -0.20 < max_dd < -0.15


class TestLiquidityRisk:
    """Test liquidity risk analysis."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analyze_liquidity_risk(self):
        """Test liquidity risk analysis."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_liquidity_risk("ETH")

        assert risk.factor == "liquidity"
        assert 0 <= risk.score <= 100
        assert risk.level in ["low", "medium", "high", "extreme"]
        assert "avg_daily_volume_usd" in risk.details
        assert "volume_consistency" in risk.details

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_liquidity_risk_volume_metrics(self):
        """Test liquidity volume metrics."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_liquidity_risk("BTC")

        details = risk.details
        assert details["avg_daily_volume_usd"] > 0
        assert 0 <= details["volume_consistency"] <= 1
        assert details["analysis_period_days"] == 7

class TestSmartContractRisk:
    """Test smart contract risk analysis."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analyze_smart_contract_risk(self):
        """Test smart contract risk analysis."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_smart_contract_risk("ETH")

        assert risk.factor == "smart_contract"
        assert 0 <= risk.score <= 100
        assert risk.level in ["low", "medium", "high", "extreme"]
        assert "audit_status" in risk.details
        assert "bug_bounty" in risk.details
        assert "code_quality" in risk.details

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_smart_contract_major_token(self):
        """Test that major tokens have lower smart contract risk."""
        analyzer = RiskAnalyzer()

        eth_risk = await analyzer.analyze_smart_contract_risk("ETH")
        btc_risk = await analyzer.analyze_smart_contract_risk("BTC")

        # Major tokens should have low risk
        assert eth_risk.level in ["low", "medium"]
        assert btc_risk.level in ["low", "medium"]
        assert eth_risk.score < 40
        assert btc_risk.score < 40

class TestMarketCorrelationRisk:
    """Test market correlation risk analysis."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analyze_correlation_risk(self):
        """Test market correlation risk analysis."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_market_correlation_risk("ETH")

        assert risk.factor == "correlation"
        assert 0 <= risk.score <= 100
        assert risk.level in ["low", "medium", "high", "extreme"]
        assert "correlation_with_btc" in risk.details
        assert "beta" in risk.details
        assert "systemic_risk_exposure" in risk.details

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_correlation_metrics(self):
        """Test correlation metrics validity."""
        analyzer = RiskAnalyzer()

        risk = await analyzer.analyze_market_correlation_risk("SOL")

        details = risk.details
        # Correlation should be between -1 and 1
        assert -1 <= details["correlation_with_btc"] <= 1
        assert details["analysis_period_days"] == 90
        assert details["systemic_risk_exposure"] in ["low", "moderate", "high"]

class TestCompositeRiskAssessment:
    """Test comprehensive risk assessment."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_comprehensive_risk_analysis(self):
        """Test complete risk assessment."""
        analyzer = RiskAnalyzer()

        assessment = await analyzer.analyze_comprehensive_risk("ETH")

        assert isinstance(assessment, CompositeRiskAssessment)
        assert assessment.token_symbol == "ETH"
        assert 0 <= assessment.overall_risk_score <= 100
        assert assessment.overall_risk_level in ["low", "medium", "high", "extreme"]
        assert len(assessment.risk_factors) == 4

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_risk_factors_present(self):
        """Test that all 4 risk factors are analyzed."""
        analyzer = RiskAnalyzer()

        assessment = await analyzer.analyze_comprehensive_risk("BTC")

        assert "volatility" in assessment.risk_factors
        assert "liquidity" in assessment.risk_factors
        assert "smart_contract" in assessment.risk_factors
        assert "correlation" in assessment.risk_factors

        # Verify each factor is a RiskScore
        for factor in assessment.risk_factors.values():
            assert isinstance(factor, RiskScore)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_recommendation_generation(self):
        """Test risk recommendation generation."""
        analyzer = RiskAnalyzer()

        assessment = await analyzer.analyze_comprehensive_risk("SOL")

        assert isinstance(assessment.recommendation, str)
        assert len(assessment.recommendation) > 20  # Should be meaningful text

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_score_weighting(self):
        """Test that risk scores are properly weighted."""
        analyzer = RiskAnalyzer()

        assessment = await analyzer.analyze_comprehensive_risk("ETH")

        # Overall score should be reasonable combination of factors
        factor_scores = [f.score for f in assessment.risk_factors.values()]
        avg_score = sum(factor_scores) / len(factor_scores)

        # Overall should be within 20 points of average (accounting for weights)
        assert abs(assessment.overall_risk_score - avg_score) < 20

    def test_score_to_level_conversion(self):
        """Test score to level conversion logic."""
        analyzer = RiskAnalyzer()

        assert analyzer._score_to_level(10) == "low"
        assert analyzer._score_to_level(30) == "medium"
        assert analyzer._score_to_level(60) == "high"
        assert analyzer._score_to_level(90) == "extreme"


class TestRiskAnalysisIntegration:
    """Integration tests for complete risk analysis flow."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multiple_token_risk_analysis(self):
        """Test analyzing multiple tokens."""
        analyzer = RiskAnalyzer()

        tokens = ["ETH", "BTC", "SOL"]
        assessments = {}

        for token in tokens:
            assessment = await analyzer.analyze_comprehensive_risk(token)
            assessments[token] = assessment

        # Verify all assessments completed
        assert len(assessments) == 3
        for token, assessment in assessments.items():
            assert assessment.token_symbol == token
            assert assessment.overall_risk_score >= 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_assessment_consistency(self):
        """Test that multiple runs produce consistent results."""
        analyzer = RiskAnalyzer()

        # Run analysis twice
        assessment1 = await analyzer.analyze_comprehensive_risk("ETH")
        assessment2 = await analyzer.analyze_comprehensive_risk("ETH")

        # Scores should be identical (deterministic with same data)
        assert assessment1.overall_risk_score == assessment2.overall_risk_score
        assert assessment1.overall_risk_level == assessment2.overall_risk_level

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_serialization(self):
        """Test risk assessment serialization to dict."""
        analyzer = RiskAnalyzer()

        assessment = await analyzer.analyze_comprehensive_risk("BTC")
        data = assessment.to_dict()

        # Verify structure
        assert "token_symbol" in data
        assert "overall_risk_score" in data
        assert "overall_risk_level" in data
        assert "risk_factors" in data
        assert "recommendation" in data
        assert "timestamp" in data

        # Verify nested structure
        for factor_name, factor_data in data["risk_factors"].items():
            assert "factor" in factor_data
            assert "score" in factor_data
            assert "level" in factor_data
