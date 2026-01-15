"""
Recalculate Rankings for All Agent Types.

Interactor for recalculating model rankings for all agent types.
Used by daily Celery task.
"""

import logging
from typing import List
from dataclasses import dataclass
from datetime import datetime, UTC

from app.domain.ports.llm_ranking_repository import LLMRankingRepository
from app.domain.services.llm.ranking_engine import RankingEngine
from app.application.llm.ranking.recalculate_agent_rankings import (
    RecalculateAgentRankings,
    RecalculateAgentRankingsResult,
)

logger = logging.getLogger(__name__)


@dataclass
class RecalculateAllRankingsResult:
    """Result of recalculating all rankings."""

    total_agent_types: int
    agent_types_processed: int
    agent_types_failed: int
    total_models_evaluated: int
    total_models_updated: int
    total_changes_made: int
    agent_results: List[RecalculateAgentRankingsResult]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    errors: List[str]


class RecalculateAllRankings:
    """
    Recalculate rankings for all agent types.

    This interactor:
    1. Gets all agent types from database
    2. For each agent type, calls RecalculateAgentRankings
    3. Aggregates results
    4. Handles errors gracefully (continues on failure)
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
        self._recalculate_agent = RecalculateAgentRankings(
            repository=repository,
            ranking_engine=ranking_engine,
        )

    async def execute(
        self,
        hours_to_analyze: int = 24,
    ) -> RecalculateAllRankingsResult:
        """
        Recalculate rankings for all agent types.

        Args:
            hours_to_analyze: Hours of telemetry to analyze (default: 24)

        Returns:
            Aggregated result
        """
        started_at = datetime.now(UTC)
        logger.info(
            f"Starting global ranking recalculation "
            f"(analyzing last {hours_to_analyze}h)"
        )

        # 1. Get all agent types
        agent_types = await self._repository.get_all_agent_types()
        total_agent_types = len(agent_types)

        logger.info(f"Found {total_agent_types} agent types to process")

        # 2. Process each agent type
        agent_results: List[RecalculateAgentRankingsResult] = []
        errors: List[str] = []
        agent_types_processed = 0
        agent_types_failed = 0

        for agent_type in agent_types:
            try:
                logger.info(f"Processing {agent_type}...")

                result = await self._recalculate_agent.execute(
                    agent_type=agent_type,
                    hours_to_analyze=hours_to_analyze,
                )

                agent_results.append(result)
                agent_types_processed += 1

                logger.info(
                    f"✓ {agent_type}: {result.models_evaluated} evaluated, "
                    f"{result.models_updated} updated"
                )

            except Exception as e:
                agent_types_failed += 1
                error_msg = f"Failed to process {agent_type}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                # Continue processing other agent types

        # 3. Aggregate results
        completed_at = datetime.now(UTC)
        duration = (completed_at - started_at).total_seconds()

        total_models_evaluated = sum(r.models_evaluated for r in agent_results)
        total_models_updated = sum(r.models_updated for r in agent_results)
        total_changes_made = sum(len(r.changes) for r in agent_results)

        result = RecalculateAllRankingsResult(
            total_agent_types=total_agent_types,
            agent_types_processed=agent_types_processed,
            agent_types_failed=agent_types_failed,
            total_models_evaluated=total_models_evaluated,
            total_models_updated=total_models_updated,
            total_changes_made=total_changes_made,
            agent_results=agent_results,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            errors=errors,
        )

        logger.info(
            f"Global recalculation complete: "
            f"{agent_types_processed}/{total_agent_types} processed, "
            f"{total_models_updated} models updated, "
            f"{total_changes_made} changes made "
            f"in {duration:.1f}s"
        )

        if errors:
            logger.warning(f"Encountered {len(errors)} errors during recalculation")

        return result
