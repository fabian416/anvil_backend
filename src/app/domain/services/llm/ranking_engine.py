"""
Adaptive Ranking Engine.

Dynamically scores models based on real-world performance.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class WeightProfile:
    """Ranking weight profile for an agent type."""

    agent_type: str
    success_weight: Decimal = Decimal("0.50")
    latency_weight: Decimal = Decimal("0.25")
    cost_weight: Decimal = Decimal("0.15")
    recency_weight: Decimal = Decimal("0.10")
    min_requests_for_ranking: int = 10
    recency_decay_hours: int = 24

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.success_weight
            + self.latency_weight
            + self.cost_weight
            + self.recency_weight
        )
        if abs(total - Decimal("1.00")) > Decimal("0.01"):
            raise ValueError(f"Weights must sum to 1.00, got {total}")


@dataclass
class ModelRanking:
    """Ranking data for a model."""

    model_id: UUID
    model_name: str
    provider_name: str
    display_name: str
    ranking_score: Decimal
    success_rate: Decimal
    latency_score: Decimal
    cost_score: Decimal
    total_requests: int
    avg_latency_ms: int
    avg_cost_per_request: Decimal


class RankingEngine:
    """
    Adaptive model ranking based on performance.

    Calculates dynamic rankings using:
    - Success rate (50% weight by default)
    - Latency (25% weight)
    - Cost efficiency (15% weight)
    - Recency bonus (10% weight)

    Rankings are agent-specific for optimal selection.
    """

    # Default weight profiles
    DEFAULT_PROFILES = {
        "swap_agent": WeightProfile(
            agent_type="swap_agent",
            success_weight=Decimal("0.60"),
            latency_weight=Decimal("0.25"),
            cost_weight=Decimal("0.10"),
            recency_weight=Decimal("0.05"),
        ),
        "trading_agent": WeightProfile(
            agent_type="trading_agent",
            success_weight=Decimal("0.55"),
            latency_weight=Decimal("0.30"),
            cost_weight=Decimal("0.10"),
            recency_weight=Decimal("0.05"),
        ),
        "portfolio_agent": WeightProfile(
            agent_type="portfolio_agent",
            success_weight=Decimal("0.45"),
            latency_weight=Decimal("0.20"),
            cost_weight=Decimal("0.25"),
            recency_weight=Decimal("0.10"),
        ),
        "researcher": WeightProfile(
            agent_type="researcher",
            success_weight=Decimal("0.40"),
            latency_weight=Decimal("0.15"),
            cost_weight=Decimal("0.30"),
            recency_weight=Decimal("0.15"),
        ),
        "risk_analyzer": WeightProfile(
            agent_type="risk_analyzer",
            success_weight=Decimal("0.65"),
            latency_weight=Decimal("0.20"),
            cost_weight=Decimal("0.10"),
            recency_weight=Decimal("0.05"),
        ),
        "default": WeightProfile(
            agent_type="default",
            success_weight=Decimal("0.50"),
            latency_weight=Decimal("0.25"),
            cost_weight=Decimal("0.15"),
            recency_weight=Decimal("0.10"),
        ),
    }

    def __init__(self):
        """Initialize ranking engine."""
        self._weight_profiles: Dict[str, WeightProfile] = self.DEFAULT_PROFILES.copy()

    def get_weight_profile(self, agent_type: str) -> WeightProfile:
        """
        Get weight profile for agent type.

        Args:
            agent_type: Agent type

        Returns:
            Weight profile (uses default if not found)
        """
        return self._weight_profiles.get(agent_type, self._weight_profiles["default"])

    def set_weight_profile(self, profile: WeightProfile):
        """
        Set weight profile for agent type.

        Args:
            profile: Weight profile
        """
        self._weight_profiles[profile.agent_type] = profile
        logger.info(f"Updated weight profile for {profile.agent_type}")

    def calculate_ranking_score(
        self,
        agent_type: str,
        success_rate: Decimal,
        latency_score: Decimal,
        cost_score: Decimal,
        recency_bonus: Decimal,
    ) -> Decimal:
        """
        Calculate ranking score.

        Args:
            agent_type: Agent type
            success_rate: Success rate (0-1)
            latency_score: Latency score (0-1, higher is better)
            cost_score: Cost score (0-1, higher is better)
            recency_bonus: Recency bonus (0-0.5)

        Returns:
            Ranking score (0-1)
        """
        profile = self.get_weight_profile(agent_type)

        score = (
            profile.success_weight * success_rate
            + profile.latency_weight * latency_score
            + profile.cost_weight * cost_score
            + profile.recency_weight * recency_bonus
        )

        return Decimal(str(score))

    def calculate_latency_score(
        self, avg_latency_ms: int, max_latency_ms: int
    ) -> Decimal:
        """
        Calculate latency score.

        Args:
            avg_latency_ms: Average latency
            max_latency_ms: Maximum latency for normalization

        Returns:
            Latency score (0-1, higher is better/faster)
        """
        if max_latency_ms == 0:
            return Decimal("0.5")

        # Normalized: 1 - (avg / max)
        # Lower latency = higher score
        score = 1 - min(Decimal(avg_latency_ms) / Decimal(max_latency_ms), Decimal("1.0"))
        return Decimal(str(score))

    def calculate_cost_score(
        self, avg_cost: Decimal, max_cost: Decimal
    ) -> Decimal:
        """
        Calculate cost score.

        Args:
            avg_cost: Average cost per request
            max_cost: Maximum cost for normalization

        Returns:
            Cost score (0-1, higher is better/cheaper)
        """
        if max_cost == 0:
            return Decimal("0.5")

        # Normalized: 1 - (avg / max)
        # Lower cost = higher score
        score = 1 - min(avg_cost / max_cost, Decimal("1.0"))
        return Decimal(str(score))

    def calculate_recency_bonus(
        self, last_used_at: Optional[datetime], recency_hours: int
    ) -> Decimal:
        """
        Calculate recency bonus.

        Args:
            last_used_at: Last usage timestamp
            recency_hours: Hours for recency bonus

        Returns:
            Recency bonus (0-0.5)
        """
        if not last_used_at:
            return Decimal("0")

        from datetime import timedelta

        now = datetime.utcnow()
        cutoff = now - timedelta(hours=recency_hours)

        if last_used_at >= cutoff:
            return Decimal("0.5")

        return Decimal("0")


# Global ranking engine instance
_ranking_engine: Optional[RankingEngine] = None


def get_ranking_engine() -> RankingEngine:
    """Get global ranking engine instance."""
    global _ranking_engine
    if _ranking_engine is None:
        _ranking_engine = RankingEngine()
    return _ranking_engine
