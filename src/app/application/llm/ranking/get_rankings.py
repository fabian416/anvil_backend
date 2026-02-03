"""
Get Rankings Interactor.

Retrieve rankings for specific agent type or all agent types.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from app.domain.ports.llm_ranking_repository import (
    LLMRankingRepository,
    ModelRankingData,
)

logger = logging.getLogger(__name__)


@dataclass
class RankedModel:
    """Model with calculated position."""

    ranking: ModelRankingData
    position: int
    has_override: bool = False
    override_reason: Optional[str] = None


@dataclass
class AgentRankings:
    """Rankings for an agent type."""

    agent_type: str
    models: List[RankedModel]
    last_recalculated_at: Optional[datetime] = None


@dataclass
class AgentTypeOverview:
    """Overview of one agent type."""

    agent_type: str
    total_models: int
    top_model: Optional[str] = None
    top_model_score: Optional[float] = None
    last_recalculated_at: Optional[datetime] = None


class GetRankingsForAgent:
    """Get rankings for a specific agent type."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(self, agent_type: str) -> AgentRankings:
        """
        Get rankings for agent type.

        Args:
            agent_type: Agent type

        Returns:
            Rankings with positions
        """
        logger.info(f"Getting rankings for {agent_type}")

        # Get current rankings (already sorted by score DESC)
        rankings = await self._repository.get_rankings_for_agent(agent_type)

        # Check for overrides
        ranked_models: List[RankedModel] = []
        for position, ranking in enumerate(rankings, start=1):
            override = await self._repository.get_override(agent_type, ranking.model_id)

            has_override = override is not None and not override.is_expired
            override_reason = override.reason if has_override else None

            ranked_models.append(
                RankedModel(
                    ranking=ranking,
                    position=position,
                    has_override=has_override,
                    override_reason=override_reason,
                )
            )

        return AgentRankings(
            agent_type=agent_type,
            models=ranked_models,
            last_recalculated_at=rankings[0].last_used_at if rankings else None,
        )


class GetAllRankingsOverview:
    """Get overview of all agent types."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(self) -> List[AgentTypeOverview]:
        """
        Get overview of all agent types.

        Returns:
            List of agent type overviews
        """
        logger.info("Getting overview of all agent types")

        # Get all agent types
        agent_types = await self._repository.get_all_agent_types()

        overviews: List[AgentTypeOverview] = []

        for agent_type in agent_types:
            rankings = await self._repository.get_rankings_for_agent(agent_type)

            top_model = None
            top_model_score = None
            last_recalculated_at = None

            if rankings:
                top_ranking = rankings[0]
                top_model = top_ranking.model_name
                top_model_score = float(top_ranking.ranking_score)
                last_recalculated_at = top_ranking.last_used_at

            overviews.append(
                AgentTypeOverview(
                    agent_type=agent_type,
                    total_models=len(rankings),
                    top_model=top_model,
                    top_model_score=top_model_score,
                    last_recalculated_at=last_recalculated_at,
                )
            )

        return overviews
