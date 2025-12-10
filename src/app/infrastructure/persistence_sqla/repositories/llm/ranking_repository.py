"""
SQLAlchemy implementation of LLM Ranking Repository.

Handles all database operations for model rankings, weight profiles,
overrides, and telemetry aggregation.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc

from app.infrastructure.adapters.types import MainAsyncSession
from app.domain.ports.llm_ranking_repository import (
    LLMRankingRepository,
    ModelRankingData,
    WeightProfileData,
    TelemetryMetrics,
    RankingOverride,
)
from app.infrastructure.persistence_sqla.mappings.llm_orchestration import (
    agent_model_rankings,
    ranking_weight_profiles,
    ranking_overrides,
    llm_models,
    llm_providers,
    llm_telemetry_hourly,
)

logger = logging.getLogger(__name__)


class SqlaLLMRankingRepository:
    """SQLAlchemy implementation of LLM ranking repository."""

    def __init__(self, session: MainAsyncSession):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_all_agent_types(self) -> List[str]:
        """Get all unique agent types from telemetry."""
        query = (
            select(llm_telemetry_hourly.c.agent_type)
            .distinct()
            .where(llm_telemetry_hourly.c.agent_type.isnot(None))
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [row[0] for row in rows]

    async def get_rankings_for_agent(
        self, agent_type: str
    ) -> List[ModelRankingData]:
        """Get current rankings for an agent type."""
        query = (
            select(
                agent_model_rankings.c.model_id,
                llm_models.c.model_id.label("model_name"),
                llm_models.c.display_name,
                llm_providers.c.name.label("provider_name"),
                agent_model_rankings.c.ranking_score,
                agent_model_rankings.c.success_rate,
                agent_model_rankings.c.avg_latency_ms,
                agent_model_rankings.c.avg_cost_per_request,
                agent_model_rankings.c.total_requests,
                agent_model_rankings.c.successful_requests,
                agent_model_rankings.c.failed_requests,
                agent_model_rankings.c.last_used_at,
            )
            .select_from(agent_model_rankings)
            .join(llm_models, agent_model_rankings.c.model_id == llm_models.c.id)
            .join(llm_providers, llm_models.c.provider_id == llm_providers.c.id)
            .where(agent_model_rankings.c.agent_type == agent_type)
            .where(llm_models.c.is_enabled == True)
            .order_by(desc(agent_model_rankings.c.ranking_score))
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [
            ModelRankingData(
                model_id=row.model_id,
                model_name=row.model_name,
                provider_name=row.provider_name,
                display_name=row.display_name,
                ranking_score=row.ranking_score,
                success_rate=row.success_rate,
                avg_latency_ms=row.avg_latency_ms,
                avg_cost_per_request=row.avg_cost_per_request,
                total_requests=row.total_requests,
                successful_requests=row.successful_requests,
                failed_requests=row.failed_requests,
                last_used_at=row.last_used_at,
            )
            for row in rows
        ]

    async def get_weight_profile(
        self, agent_type: str
    ) -> Optional[WeightProfileData]:
        """Get weight profile for agent type."""
        query = select(ranking_weight_profiles).where(
            ranking_weight_profiles.c.agent_type == agent_type
        )

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        return WeightProfileData(
            agent_type=row.agent_type,
            success_weight=row.success_weight,
            latency_weight=row.latency_weight,
            cost_weight=row.cost_weight,
            recency_weight=row.recency_weight,
            min_requests_for_ranking=row.min_requests_for_ranking,
            recency_decay_hours=row.recency_decay_hours,
        )

    async def get_telemetry_metrics(
        self, agent_type: str, hours: int = 24
    ) -> Dict[UUID, TelemetryMetrics]:
        """Get aggregated telemetry metrics for agent type."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(
                llm_telemetry_hourly.c.model_id,
                func.sum(llm_telemetry_hourly.c.total_requests).label("total_requests"),
                func.sum(llm_telemetry_hourly.c.successful_requests).label(
                    "successful_requests"
                ),
                func.sum(llm_telemetry_hourly.c.failed_requests).label("failed_requests"),
                func.round(
                    func.avg(llm_telemetry_hourly.c.avg_latency_ms), 0
                ).label("avg_latency_ms"),
                func.round(
                    func.avg(llm_telemetry_hourly.c.avg_cost_per_request), 6
                ).label("avg_cost_per_request"),
                func.max(llm_telemetry_hourly.c.hour_bucket).label("last_used_at"),
            )
            .where(llm_telemetry_hourly.c.agent_type == agent_type)
            .where(llm_telemetry_hourly.c.hour_bucket >= cutoff_time)
            .group_by(llm_telemetry_hourly.c.model_id)
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        metrics_map = {}
        for row in rows:
            metrics_map[row.model_id] = TelemetryMetrics(
                model_id=row.model_id,
                total_requests=row.total_requests or 0,
                successful_requests=row.successful_requests or 0,
                failed_requests=row.failed_requests or 0,
                avg_latency_ms=int(row.avg_latency_ms or 0),
                avg_cost_per_request=Decimal(str(row.avg_cost_per_request or 0)),
                last_used_at=row.last_used_at,
            )

        return metrics_map

    async def get_override(
        self, agent_type: str, model_id: UUID
    ) -> Optional[RankingOverride]:
        """Get active override for agent type + model."""
        now = datetime.utcnow()

        query = (
            select(ranking_overrides)
            .where(ranking_overrides.c.agent_type == agent_type)
            .where(ranking_overrides.c.model_id == model_id)
            .where(
                or_(
                    ranking_overrides.c.expires_at.is_(None),
                    ranking_overrides.c.expires_at > now,
                )
            )
        )

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        return RankingOverride(
            agent_type=row.agent_type,
            model_id=row.model_id,
            override_score=row.override_score,
            reason=row.reason,
            created_by=row.created_by,
            created_at=row.created_at,
            expires_at=row.expires_at,
        )

    async def update_ranking_score(
        self,
        agent_type: str,
        model_id: UUID,
        ranking_score: Decimal,
        success_rate: Decimal,
        latency_score: Decimal,
        cost_score: Decimal,
        avg_latency_ms: int,
        avg_cost_per_request: Decimal,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
    ) -> None:
        """Update ranking score for agent type + model."""
        from sqlalchemy.dialects.postgresql import insert

        # Use upsert (INSERT ... ON CONFLICT DO UPDATE)
        stmt = insert(agent_model_rankings).values(
            agent_type=agent_type,
            model_id=model_id,
            ranking_score=ranking_score,
            success_rate=success_rate,
            latency_score=latency_score,
            cost_score=cost_score,
            avg_latency_ms=avg_latency_ms,
            avg_cost_per_request=avg_cost_per_request,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            last_recalculated_at=datetime.utcnow(),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["agent_type", "model_id"],
            set_=dict(
                ranking_score=stmt.excluded.ranking_score,
                success_rate=stmt.excluded.success_rate,
                latency_score=stmt.excluded.latency_score,
                cost_score=stmt.excluded.cost_score,
                avg_latency_ms=stmt.excluded.avg_latency_ms,
                avg_cost_per_request=stmt.excluded.avg_cost_per_request,
                total_requests=stmt.excluded.total_requests,
                successful_requests=stmt.excluded.successful_requests,
                failed_requests=stmt.excluded.failed_requests,
                last_recalculated_at=stmt.excluded.last_recalculated_at,
            ),
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def create_override(
        self,
        agent_type: str,
        model_id: UUID,
        override_score: Decimal,
        reason: Optional[str] = None,
        created_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Create ranking override."""
        from sqlalchemy.dialects.postgresql import insert

        stmt = insert(ranking_overrides).values(
            agent_type=agent_type,
            model_id=model_id,
            override_score=override_score,
            reason=reason,
            created_by=created_by,
            expires_at=expires_at,
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def delete_override(self, agent_type: str, model_id: UUID) -> None:
        """Delete ranking override."""
        from sqlalchemy import delete

        stmt = delete(ranking_overrides).where(
            and_(
                ranking_overrides.c.agent_type == agent_type,
                ranking_overrides.c.model_id == model_id,
            )
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def get_max_latency(self, agent_type: str) -> int:
        """Get maximum latency for normalization."""
        query = (
            select(func.max(agent_model_rankings.c.avg_latency_ms))
            .where(agent_model_rankings.c.agent_type == agent_type)
        )

        result = await self._session.execute(query)
        max_val = result.scalar()

        return int(max_val) if max_val else 10000  # Default 10s

    async def get_max_cost(self, agent_type: str) -> Decimal:
        """Get maximum cost for normalization."""
        query = (
            select(func.max(agent_model_rankings.c.avg_cost_per_request))
            .where(agent_model_rankings.c.agent_type == agent_type)
        )

        result = await self._session.execute(query)
        max_val = result.scalar()

        return Decimal(str(max_val)) if max_val else Decimal("0.01")  # Default $0.01
