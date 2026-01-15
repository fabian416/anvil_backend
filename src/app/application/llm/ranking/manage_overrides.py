"""
Manage Ranking Overrides Interactor.

Set and remove manual ranking overrides.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from uuid import UUID

from app.domain.ports.llm_ranking_repository import LLMRankingRepository

logger = logging.getLogger(__name__)


@dataclass
class SetOverrideResult:
    """Result of setting override."""

    agent_type: str
    model_id: UUID
    model_name: str
    override_score: float
    expires_at: Optional[datetime]
    action: str  # "created" or "updated"


@dataclass
class RemoveOverrideResult:
    """Result of removing override."""

    agent_type: str
    model_id: UUID
    model_name: str
    action: str = "removed"


class SetRankingOverride:
    """Set manual ranking override for model."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(
        self,
        agent_type: str,
        model_id: UUID,
        override_score: float,
        reason: Optional[str] = None,
        expires_in_hours: Optional[int] = None,
        created_by: Optional[UUID] = None,
    ) -> SetOverrideResult:
        """
        Set ranking override.

        Args:
            agent_type: Agent type
            model_id: Model ID
            override_score: Override score (0.0-1.0)
            reason: Reason for override
            expires_in_hours: Expiry in hours (None = permanent)
            created_by: Admin user ID

        Returns:
            Result
        """
        from decimal import Decimal

        logger.info(
            f"Setting override for {agent_type}/{model_id}: "
            f"score={override_score}, expires_in={expires_in_hours}h"
        )

        # Calculate expiry
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)

        # Check if override already exists
        existing_override = await self._repository.get_override(agent_type, model_id)
        action = "updated" if existing_override else "created"

        # Get model name
        rankings = await self._repository.get_rankings_for_agent(agent_type)
        model_name = next(
            (r.model_name for r in rankings if r.model_id == model_id),
            str(model_id),
        )

        # Create override
        await self._repository.create_override(
            agent_type=agent_type,
            model_id=model_id,
            override_score=Decimal(str(override_score)),
            reason=reason,
            created_by=created_by,
            expires_at=expires_at,
        )

        logger.info(f"Override {action} for {model_name}")

        return SetOverrideResult(
            agent_type=agent_type,
            model_id=model_id,
            model_name=model_name,
            override_score=override_score,
            expires_at=expires_at,
            action=action,
        )


class RemoveRankingOverride:
    """Remove manual ranking override."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(
        self,
        agent_type: str,
        model_id: UUID,
    ) -> RemoveOverrideResult:
        """
        Remove ranking override.

        Args:
            agent_type: Agent type
            model_id: Model ID

        Returns:
            Result
        """
        logger.info(f"Removing override for {agent_type}/{model_id}")

        # Get model name
        rankings = await self._repository.get_rankings_for_agent(agent_type)
        model_name = next(
            (r.model_name for r in rankings if r.model_id == model_id),
            str(model_id),
        )

        # Remove override
        await self._repository.delete_override(agent_type, model_id)

        logger.info(f"Override removed for {model_name}")

        return RemoveOverrideResult(
            agent_type=agent_type,
            model_id=model_id,
            model_name=model_name,
        )
