"""
Celery Tasks for LLM Ranking System.

Background tasks for automatic ranking recalculation.
"""

import logging
import asyncio
from celery import Task

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.helpers import _run_task

logger = logging.getLogger(__name__)


@celery_app.task(
    name="llm_ranking.recalculate_all_rankings",
    bind=True,
    max_retries=3,
    retry_backoff=True,
)
def recalculate_all_rankings(self: Task):
    """
    Daily task: Recalculate rankings for all agent types.

    Schedule: Daily at 02:00 UTC (low traffic time)

    Process:
    1. Get all unique agent_types from telemetry
    2. For each agent_type:
       a. Aggregate last 24h metrics
       b. Calculate ranking scores
       c. Update agent_model_rankings table
       d. Log changes to audit log
    3. Send notification if major changes (optional)
    """

    async def runner(container):
        from app.application.llm.ranking.recalculate_all_rankings import (
            RecalculateAllRankings,
        )

        interactor = await container.get(RecalculateAllRankings)

        try:
            result = await interactor.execute(hours_to_analyze=24)

            logger.info(
                f"✅ Ranking recalculation complete: "
                f"{result.agent_types_processed}/{result.total_agent_types} types, "
                f"{result.total_models_updated} models updated, "
                f"{result.total_changes_made} changes made "
                f"in {result.duration_seconds:.1f}s"
            )

            if result.errors:
                logger.warning(
                    f"⚠️ Encountered {len(result.errors)} errors: {result.errors}"
                )

            return {
                "success": True,
                "agent_types_processed": result.agent_types_processed,
                "agent_types_failed": result.agent_types_failed,
                "models_updated": result.total_models_updated,
                "changes_made": result.total_changes_made,
                "duration_seconds": result.duration_seconds,
                "errors": result.errors,
            }

        except Exception as e:
            logger.error(f"❌ Ranking recalculation failed: {e}", exc_info=True)

            # Retry with exponential backoff
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

            # Final failure
            return {
                "success": False,
                "error": str(e),
                "retries": self.request.retries,
            }

    return asyncio.run(_run_task(runner))


@celery_app.task(name="llm_ranking.recalculate_agent")
def recalculate_agent_rankings(agent_type: str, hours_to_analyze: int = 24):
    """
    Manual task: Recalculate rankings for a specific agent type.

    Args:
        agent_type: Agent type to recalculate
        hours_to_analyze: Hours of telemetry to analyze

    Returns:
        Result dict
    """

    async def runner(container):
        from app.application.llm.ranking.recalculate_agent_rankings import (
            RecalculateAgentRankings,
        )

        interactor = await container.get(RecalculateAgentRankings)

        try:
            result = await interactor.execute(
                agent_type=agent_type,
                hours_to_analyze=hours_to_analyze,
            )

            logger.info(
                f"✅ Recalculation complete for {agent_type}: "
                f"{result.models_evaluated} evaluated, "
                f"{result.models_updated} updated"
            )

            return {
                "success": True,
                "agent_type": result.agent_type,
                "models_evaluated": result.models_evaluated,
                "models_updated": result.models_updated,
                "changes": [
                    {
                        "model_id": str(c.model_id),
                        "model_name": c.model_name,
                        "old_score": float(c.old_score),
                        "new_score": float(c.new_score),
                        "reason": c.reason,
                    }
                    for c in result.changes
                ],
            }

        except Exception as e:
            logger.error(
                f"❌ Recalculation failed for {agent_type}: {e}", exc_info=True
            )
            return {
                "success": False,
                "agent_type": agent_type,
                "error": str(e),
            }

    return asyncio.run(_run_task(runner))
