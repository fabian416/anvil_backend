"""
Recalculate Rankings for Single Agent Type.

Interactor for recalculating model rankings for a specific agent type
based on recent telemetry data.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, UTC
from uuid import UUID

from app.domain.ports.llm_ranking_repository import LLMRankingRepository
from app.domain.services.llm.ranking_engine import RankingEngine, WeightProfile

logger = logging.getLogger(__name__)


@dataclass
class RankingChange:
    """Represents a change in ranking."""

    model_id: UUID
    model_name: str
    old_score: Decimal
    new_score: Decimal
    old_position: int
    new_position: int
    reason: str


@dataclass
class RecalculateAgentRankingsResult:
    """Result of recalculating rankings for an agent type."""

    agent_type: str
    models_evaluated: int
    models_updated: int
    changes: List[RankingChange]
    recalculated_at: datetime


class RecalculateAgentRankings:
    """
    Recalculate rankings for a single agent type.

    This interactor:
    1. Gets telemetry metrics for the agent type
    2. Gets weight profile for the agent type
    3. Calculates new ranking scores using the formula
    4. Updates database with new scores
    5. Returns summary of changes
    """

    def __init__(
        self,
        repository: LLMRankingRepository,
        ranking_engine: RankingEngine,
    ):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
            ranking_engine: Ranking calculation engine
        """
        self._repository = repository
        self._ranking_engine = ranking_engine

    async def execute(
        self,
        agent_type: str,
        hours_to_analyze: int = 24,
    ) -> RecalculateAgentRankingsResult:
        """
        Recalculate rankings for an agent type.

        Args:
            agent_type: Agent type to recalculate
            hours_to_analyze: Hours of telemetry to analyze (default: 24)

        Returns:
            Result with changes made
        """
        logger.info(
            f"Recalculating rankings for {agent_type} "
            f"(analyzing last {hours_to_analyze}h)"
        )

        # 1. Get current rankings
        current_rankings = await self._repository.get_rankings_for_agent(agent_type)
        current_rankings_map = {r.model_id: r for r in current_rankings}

        # 2. Get telemetry metrics
        telemetry_metrics = await self._repository.get_telemetry_metrics(
            agent_type, hours=hours_to_analyze
        )

        if not telemetry_metrics:
            logger.warning(
                f"No telemetry data for {agent_type} in last {hours_to_analyze}h"
            )
            return RecalculateAgentRankingsResult(
                agent_type=agent_type,
                models_evaluated=0,
                models_updated=0,
                changes=[],
                recalculated_at=datetime.now(UTC),
            )

        # 3. Get weight profile
        weight_profile_data = await self._repository.get_weight_profile(agent_type)

        if weight_profile_data:
            weight_profile = WeightProfile(
                agent_type=weight_profile_data.agent_type,
                success_weight=weight_profile_data.success_weight,
                latency_weight=weight_profile_data.latency_weight,
                cost_weight=weight_profile_data.cost_weight,
                recency_weight=weight_profile_data.recency_weight,
                min_requests_for_ranking=weight_profile_data.min_requests_for_ranking,
                recency_decay_hours=weight_profile_data.recency_decay_hours,
            )
        else:
            # Use default from ranking engine
            weight_profile = self._ranking_engine.get_weight_profile(agent_type)
            logger.info(f"Using default weight profile for {agent_type}")

        # 4. Get normalization values (max latency, max cost)
        max_latency_ms = await self._repository.get_max_latency(agent_type)
        max_cost = await self._repository.get_max_cost(agent_type)

        if max_latency_ms == 0:
            max_latency_ms = 10000  # Default 10s
        if max_cost == Decimal("0"):
            max_cost = Decimal("0.01")  # Default $0.01

        # 5. Calculate new scores for each model
        changes: List[RankingChange] = []
        models_evaluated = 0
        models_updated = 0

        for model_id, metrics in telemetry_metrics.items():
            models_evaluated += 1

            # Check minimum requests threshold
            if metrics.total_requests < weight_profile.min_requests_for_ranking:
                logger.debug(
                    f"Model {model_id} has only {metrics.total_requests} requests "
                    f"(need {weight_profile.min_requests_for_ranking}), skipping"
                )
                continue

            # Check for override
            override = await self._repository.get_override(agent_type, model_id)
            if override and not override.is_expired:
                logger.info(
                    f"Model {model_id} has active override "
                    f"(score={override.override_score}), skipping calculation"
                )
                continue

            # Calculate component scores
            success_rate = metrics.success_rate

            latency_score = self._ranking_engine.calculate_latency_score(
                metrics.avg_latency_ms, max_latency_ms
            )

            cost_score = self._ranking_engine.calculate_cost_score(
                metrics.avg_cost_per_request, max_cost
            )

            recency_bonus = self._ranking_engine.calculate_recency_bonus(
                metrics.last_used_at, weight_profile.recency_decay_hours
            )

            # Calculate final ranking score
            new_ranking_score = self._ranking_engine.calculate_ranking_score(
                agent_type=agent_type,
                success_rate=success_rate,
                latency_score=latency_score,
                cost_score=cost_score,
                recency_bonus=recency_bonus,
            )

            # Get old score
            old_ranking = current_rankings_map.get(model_id)
            old_score = old_ranking.ranking_score if old_ranking else Decimal("0.0")

            # Check if score changed significantly (>1% change)
            if abs(new_ranking_score - old_score) > Decimal("0.01"):
                # Update database
                await self._repository.update_ranking_score(
                    agent_type=agent_type,
                    model_id=model_id,
                    ranking_score=new_ranking_score,
                    success_rate=success_rate,
                    latency_score=latency_score,
                    cost_score=cost_score,
                    avg_latency_ms=metrics.avg_latency_ms,
                    avg_cost_per_request=metrics.avg_cost_per_request,
                    total_requests=metrics.total_requests,
                    successful_requests=metrics.successful_requests,
                    failed_requests=metrics.failed_requests,
                )

                models_updated += 1

                # Calculate position change (if we have old ranking)
                if old_ranking:
                    # Simplified position calculation
                    # In reality, positions change based on all models' scores
                    change_reason = self._generate_change_reason(
                        old_score,
                        new_ranking_score,
                        success_rate,
                        latency_score,
                        cost_score,
                    )

                    changes.append(
                        RankingChange(
                            model_id=model_id,
                            model_name=old_ranking.model_name,
                            old_score=old_score,
                            new_score=new_ranking_score,
                            old_position=0,  # Would need to query all rankings for accurate positions
                            new_position=0,
                            reason=change_reason,
                        )
                    )

                logger.info(
                    f"Updated {model_id}: {old_score:.4f} → {new_ranking_score:.4f}"
                )

        result = RecalculateAgentRankingsResult(
            agent_type=agent_type,
            models_evaluated=models_evaluated,
            models_updated=models_updated,
            changes=changes,
            recalculated_at=datetime.now(UTC),
        )

        logger.info(
            f"Recalculation complete for {agent_type}: "
            f"{models_evaluated} evaluated, {models_updated} updated"
        )

        return result

    def _generate_change_reason(
        self,
        old_score: Decimal,
        new_score: Decimal,
        success_rate: Decimal,
        latency_score: Decimal,
        cost_score: Decimal,
    ) -> str:
        """
        Generate human-readable reason for score change.

        Args:
            old_score: Old ranking score
            new_score: New ranking score
            success_rate: Success rate
            latency_score: Latency score
            cost_score: Cost score

        Returns:
            Reason string
        """
        diff = new_score - old_score

        if diff > Decimal("0.1"):
            direction = "Significant improvement"
        elif diff > Decimal("0.01"):
            direction = "Improved"
        elif diff < Decimal("-0.1"):
            direction = "Significant degradation"
        elif diff < Decimal("-0.01"):
            direction = "Degraded"
        else:
            direction = "Stable"

        # Identify main factor
        factors = []
        if success_rate > Decimal("0.95"):
            factors.append("high success rate")
        elif success_rate < Decimal("0.90"):
            factors.append("low success rate")

        if latency_score > Decimal("0.80"):
            factors.append("fast latency")
        elif latency_score < Decimal("0.50"):
            factors.append("slow latency")

        if cost_score > Decimal("0.80"):
            factors.append("low cost")

        if factors:
            return f"{direction}: {', '.join(factors)}"
        return direction
