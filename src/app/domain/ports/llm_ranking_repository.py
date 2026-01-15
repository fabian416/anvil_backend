"""
LLM Ranking Repository Port.

Repository interface for LLM model rankings and related data.
"""

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime, UTC
from decimal import Decimal
from uuid import UUID


class ModelRankingData:
    """Model ranking data from database."""

    def __init__(
        self,
        model_id: UUID,
        model_name: str,
        provider_name: str,
        display_name: str,
        ranking_score: Decimal,
        success_rate: Decimal,
        avg_latency_ms: int,
        avg_cost_per_request: Decimal,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        last_used_at: Optional[datetime] = None,
    ):
        self.model_id = model_id
        self.model_name = model_name
        self.provider_name = provider_name
        self.display_name = display_name
        self.ranking_score = ranking_score
        self.success_rate = success_rate
        self.avg_latency_ms = avg_latency_ms
        self.avg_cost_per_request = avg_cost_per_request
        self.total_requests = total_requests
        self.successful_requests = successful_requests
        self.failed_requests = failed_requests
        self.last_used_at = last_used_at


class WeightProfileData:
    """Weight profile data from database."""

    def __init__(
        self,
        agent_type: str,
        success_weight: Decimal,
        latency_weight: Decimal,
        cost_weight: Decimal,
        recency_weight: Decimal,
        min_requests_for_ranking: int,
        recency_decay_hours: int,
    ):
        self.agent_type = agent_type
        self.success_weight = success_weight
        self.latency_weight = latency_weight
        self.cost_weight = cost_weight
        self.recency_weight = recency_weight
        self.min_requests_for_ranking = min_requests_for_ranking
        self.recency_decay_hours = recency_decay_hours


class TelemetryMetrics:
    """Aggregated telemetry metrics for a model."""

    def __init__(
        self,
        model_id: UUID,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        avg_latency_ms: int,
        avg_cost_per_request: Decimal,
        last_used_at: Optional[datetime] = None,
    ):
        self.model_id = model_id
        self.total_requests = total_requests
        self.successful_requests = successful_requests
        self.failed_requests = failed_requests
        self.avg_latency_ms = avg_latency_ms
        self.avg_cost_per_request = avg_cost_per_request
        self.last_used_at = last_used_at

    @property
    def success_rate(self) -> Decimal:
        """Calculate success rate."""
        if self.total_requests == 0:
            return Decimal("0.0")
        return Decimal(self.successful_requests) / Decimal(self.total_requests)


class RankingOverride:
    """Ranking override data."""

    def __init__(
        self,
        agent_type: str,
        model_id: UUID,
        override_score: Decimal,
        reason: Optional[str] = None,
        created_by: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.agent_type = agent_type
        self.model_id = model_id
        self.override_score = override_score
        self.reason = reason
        self.created_by = created_by
        self.created_at = created_at
        self.expires_at = expires_at

    @property
    def is_expired(self) -> bool:
        """Check if override is expired."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at


class LLMRankingRepository(Protocol):
    """
    Repository for LLM ranking data.

    Handles all database operations for model rankings, weight profiles,
    overrides, and telemetry aggregation.
    """

    async def get_all_agent_types(self) -> List[str]:
        """
        Get all unique agent types.

        Returns:
            List of agent type strings
        """
        ...

    async def get_rankings_for_agent(
        self, agent_type: str
    ) -> List[ModelRankingData]:
        """
        Get current rankings for an agent type.

        Args:
            agent_type: Agent type

        Returns:
            List of model rankings (ordered by ranking_score desc)
        """
        ...

    async def get_weight_profile(
        self, agent_type: str
    ) -> Optional[WeightProfileData]:
        """
        Get weight profile for agent type.

        Args:
            agent_type: Agent type

        Returns:
            Weight profile or None if not found
        """
        ...

    async def get_telemetry_metrics(
        self, agent_type: str, hours: int = 24
    ) -> Dict[UUID, TelemetryMetrics]:
        """
        Get aggregated telemetry metrics for agent type.

        Args:
            agent_type: Agent type
            hours: Hours to look back (default: 24)

        Returns:
            Dict of model_id -> TelemetryMetrics
        """
        ...

    async def get_override(
        self, agent_type: str, model_id: UUID
    ) -> Optional[RankingOverride]:
        """
        Get active override for agent type + model.

        Args:
            agent_type: Agent type
            model_id: Model ID

        Returns:
            Override or None if not found/expired
        """
        ...

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
        """
        Update ranking score for agent type + model.

        Args:
            agent_type: Agent type
            model_id: Model ID
            ranking_score: New ranking score
            success_rate: Success rate
            latency_score: Latency score
            cost_score: Cost score
            avg_latency_ms: Average latency
            avg_cost_per_request: Average cost
            total_requests: Total requests
            successful_requests: Successful requests
            failed_requests: Failed requests
        """
        ...

    async def create_override(
        self,
        agent_type: str,
        model_id: UUID,
        override_score: Decimal,
        reason: Optional[str] = None,
        created_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """
        Create ranking override.

        Args:
            agent_type: Agent type
            model_id: Model ID
            override_score: Override score
            reason: Reason for override
            created_by: Admin user ID
            expires_at: Expiration timestamp
        """
        ...

    async def delete_override(self, agent_type: str, model_id: UUID) -> None:
        """
        Delete ranking override.

        Args:
            agent_type: Agent type
            model_id: Model ID
        """
        ...

    async def get_max_latency(self, agent_type: str) -> int:
        """
        Get maximum latency for normalization.

        Args:
            agent_type: Agent type

        Returns:
            Maximum latency in milliseconds
        """
        ...

    async def get_max_cost(self, agent_type: str) -> Decimal:
        """
        Get maximum cost for normalization.

        Args:
            agent_type: Agent type

        Returns:
            Maximum cost per request
        """
        ...
