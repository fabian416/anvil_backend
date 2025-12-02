"""
Unit tests for Ranking Engine.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.domain.services.llm.ranking_engine import (
    RankingEngine,
    WeightProfile,
)


class TestWeightProfile:
    """Test WeightProfile validation."""

    def test_valid_weights(self):
        """Test valid weight profile."""
        profile = WeightProfile(
            agent_type="test",
            success_weight=Decimal("0.50"),
            latency_weight=Decimal("0.25"),
            cost_weight=Decimal("0.15"),
            recency_weight=Decimal("0.10"),
        )

        assert profile.agent_type == "test"

    def test_weights_must_sum_to_one(self):
        """Test weights must sum to 1.0."""
        with pytest.raises(ValueError):
            WeightProfile(
                agent_type="test",
                success_weight=Decimal("0.40"),
                latency_weight=Decimal("0.30"),
                cost_weight=Decimal("0.20"),
                recency_weight=Decimal("0.20"),  # Sums to 1.10
            )


class TestRankingEngine:
    """Test RankingEngine functionality."""

    def test_default_profiles_exist(self):
        """Test default weight profiles exist."""
        engine = RankingEngine()

        assert "swap_agent" in engine._weight_profiles
        assert "trading_agent" in engine._weight_profiles
        assert "portfolio_agent" in engine._weight_profiles
        assert "default" in engine._weight_profiles

    def test_get_weight_profile(self):
        """Test getting weight profile."""
        engine = RankingEngine()

        profile = engine.get_weight_profile("swap_agent")
        assert profile.agent_type == "swap_agent"
        assert profile.success_weight == Decimal("0.60")

        # Unknown agent uses default
        default = engine.get_weight_profile("unknown_agent")
        assert default.agent_type == "default"

    def test_set_weight_profile(self):
        """Test setting custom weight profile."""
        engine = RankingEngine()

        custom = WeightProfile(
            agent_type="custom",
            success_weight=Decimal("0.70"),
            latency_weight=Decimal("0.20"),
            cost_weight=Decimal("0.05"),
            recency_weight=Decimal("0.05"),
        )

        engine.set_weight_profile(custom)

        retrieved = engine.get_weight_profile("custom")
        assert retrieved.success_weight == Decimal("0.70")

    def test_calculate_ranking_score(self):
        """Test ranking score calculation."""
        engine = RankingEngine()

        score = engine.calculate_ranking_score(
            agent_type="swap_agent",
            success_rate=Decimal("0.95"),
            latency_score=Decimal("0.80"),
            cost_score=Decimal("0.90"),
            recency_bonus=Decimal("0.50"),
        )

        # swap_agent weights: 0.60, 0.25, 0.10, 0.05
        # Expected: 0.60*0.95 + 0.25*0.80 + 0.10*0.90 + 0.05*0.50
        #         = 0.57 + 0.20 + 0.09 + 0.025 = 0.885
        assert score == pytest.approx(Decimal("0.885"), rel=0.01)

    def test_calculate_latency_score(self):
        """Test latency score calculation."""
        engine = RankingEngine()

        # Lower latency = higher score
        score_fast = engine.calculate_latency_score(avg_latency_ms=1000, max_latency_ms=2000)
        score_slow = engine.calculate_latency_score(avg_latency_ms=1800, max_latency_ms=2000)

        assert score_fast > score_slow
        assert score_fast == Decimal("0.5")  # 1 - (1000 / 2000) = 0.5
        assert score_slow == Decimal("0.1")  # 1 - (1800 / 2000) = 0.1

    def test_calculate_cost_score(self):
        """Test cost score calculation."""
        engine = RankingEngine()

        # Lower cost = higher score
        score_cheap = engine.calculate_cost_score(
            avg_cost=Decimal("0.005"), max_cost=Decimal("0.01")
        )
        score_expensive = engine.calculate_cost_score(
            avg_cost=Decimal("0.009"), max_cost=Decimal("0.01")
        )

        assert score_cheap > score_expensive
        assert score_cheap == Decimal("0.5")  # 1 - (0.005 / 0.01) = 0.5
        assert score_expensive == Decimal("0.1")  # 1 - (0.009 / 0.01) = 0.1

    def test_calculate_recency_bonus(self):
        """Test recency bonus calculation."""
        engine = RankingEngine()

        now = datetime.utcnow()

        # Recent usage (within 24 hours)
        recent = now - timedelta(hours=12)
        bonus_recent = engine.calculate_recency_bonus(recent, recency_hours=24)
        assert bonus_recent == Decimal("0.5")

        # Old usage (outside 24 hours)
        old = now - timedelta(hours=48)
        bonus_old = engine.calculate_recency_bonus(old, recency_hours=24)
        assert bonus_old == Decimal("0")

        # No usage
        bonus_none = engine.calculate_recency_bonus(None, recency_hours=24)
        assert bonus_none == Decimal("0")
