"""
Register New LLM Model Interactors.

Register new models from Vertex AI or DeepInfra with automatic
rank 1 placement for metric collection.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from decimal import Decimal

from app.domain.ports.llm_ranking_repository import LLMRankingRepository

logger = logging.getLogger(__name__)


@dataclass
class RegisterModelResult:
    """Result of model registration."""

    model_id: UUID
    model_name: str
    provider_name: str
    display_name: str
    initial_ranking_score: Decimal
    override_expires_at: datetime
    agent_types_registered: List[str]


class RegisterVertexAIModel:
    """Register new Vertex AI model."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(
        self,
        model_id: str,
        display_name: str,
        description: Optional[str],
        context_window: Optional[int],
        input_cost_per_1k: Decimal,
        output_cost_per_1k: Decimal,
        max_output_tokens: Optional[int],
        supports_streaming: bool,
        agent_types: Optional[List[str]],
        created_by: Optional[UUID] = None,
    ) -> RegisterModelResult:
        """
        Register Vertex AI model.

        Process:
        1. Get or create "vertex_ai" provider
        2. Create model record in llm_models
        3. For each agent_type (or all):
           a. Create ranking entry with score 1.0
           b. Create 24h override with score 1.0
        4. Return registration details

        Args:
            model_id: Vertex AI model ID
            display_name: Human-readable name
            description: Model description
            context_window: Context window size
            input_cost_per_1k: Input cost per 1k tokens
            output_cost_per_1k: Output cost per 1k tokens
            max_output_tokens: Max output tokens
            supports_streaming: Streaming support
            agent_types: Agent types (None = all)
            created_by: Admin user ID

        Returns:
            Registration result
        """
        logger.info(f"Registering Vertex AI model: {model_id}")

        # 1. Get or create Vertex AI provider
        provider_id = await self._get_or_create_provider(
            name="vertex_ai",
            display_name="Google Vertex AI",
        )

        # 2. Create model record
        new_model_id = uuid4()
        await self._create_model(
            model_id=new_model_id,
            provider_id=provider_id,
            model_name=model_id,
            display_name=display_name,
            description=description,
            context_window=context_window,
            input_cost_per_1k=input_cost_per_1k,
            output_cost_per_1k=output_cost_per_1k,
            max_output_tokens=max_output_tokens,
            supports_streaming=supports_streaming,
        )

        # 3. Get agent types to register for
        if agent_types is None:
            agent_types = await self._repository.get_all_agent_types()

        # 4. Create ranking entries with overrides
        initial_score = Decimal("1.0")
        expires_at = datetime.utcnow() + timedelta(hours=24)

        for agent_type in agent_types:
            # Create ranking entry
            await self._repository.update_ranking_score(
                agent_type=agent_type,
                model_id=new_model_id,
                ranking_score=initial_score,
                success_rate=Decimal("0.0"),
                latency_score=Decimal("0.5"),
                cost_score=Decimal("0.5"),
                avg_latency_ms=0,
                avg_cost_per_request=Decimal("0.0"),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )

            # Create 24h override to ensure position 1
            await self._repository.create_override(
                agent_type=agent_type,
                model_id=new_model_id,
                override_score=initial_score,
                reason=f"New model initialization - collecting metrics for 24h",
                created_by=created_by,
                expires_at=expires_at,
            )

        logger.info(
            f"✅ Registered {model_id} for {len(agent_types)} agent types "
            f"with 24h position 1 override"
        )

        return RegisterModelResult(
            model_id=new_model_id,
            model_name=model_id,
            provider_name="vertex_ai",
            display_name=display_name,
            initial_ranking_score=initial_score,
            override_expires_at=expires_at,
            agent_types_registered=agent_types,
        )

    async def _get_or_create_provider(
        self, name: str, display_name: str
    ) -> UUID:
        """Get or create provider."""
        # This would query llm_providers table
        # For now, return a placeholder
        # In real implementation, would use a provider repository
        from sqlalchemy import select, insert
        from app.infrastructure.persistence_sqla.mappings.llm_orchestration import (
            llm_providers,
        )

        # Note: This needs access to session, which should be injected
        # For now, just return a UUID - full implementation would query DB
        return uuid4()

    async def _create_model(
        self,
        model_id: UUID,
        provider_id: UUID,
        model_name: str,
        display_name: str,
        description: Optional[str],
        context_window: Optional[int],
        input_cost_per_1k: Decimal,
        output_cost_per_1k: Decimal,
        max_output_tokens: Optional[int],
        supports_streaming: bool,
    ) -> None:
        """Create model record."""
        # This would insert into llm_models table
        # For now, just log
        logger.info(f"Creating model record: {model_name}")


class RegisterDeepInfraModel:
    """Register new DeepInfra model."""

    def __init__(self, repository: LLMRankingRepository):
        """
        Initialize interactor.

        Args:
            repository: Ranking repository
        """
        self._repository = repository

    async def execute(
        self,
        model_id: str,
        display_name: str,
        description: Optional[str],
        context_window: Optional[int],
        input_cost_per_1k: Decimal,
        output_cost_per_1k: Decimal,
        max_output_tokens: Optional[int],
        supports_streaming: bool,
        agent_types: Optional[List[str]],
        created_by: Optional[UUID] = None,
    ) -> RegisterModelResult:
        """
        Register DeepInfra model.

        Same process as Vertex AI but for DeepInfra provider.

        Args:
            model_id: DeepInfra model ID
            display_name: Human-readable name
            description: Model description
            context_window: Context window size
            input_cost_per_1k: Input cost per 1k tokens
            output_cost_per_1k: Output cost per 1k tokens
            max_output_tokens: Max output tokens
            supports_streaming: Streaming support
            agent_types: Agent types (None = all)
            created_by: Admin user ID

        Returns:
            Registration result
        """
        logger.info(f"Registering DeepInfra model: {model_id}")

        # 1. Get or create DeepInfra provider
        provider_id = await self._get_or_create_provider(
            name="deepinfra",
            display_name="DeepInfra",
        )

        # 2. Create model record
        new_model_id = uuid4()
        await self._create_model(
            model_id=new_model_id,
            provider_id=provider_id,
            model_name=model_id,
            display_name=display_name,
            description=description,
            context_window=context_window,
            input_cost_per_1k=input_cost_per_1k,
            output_cost_per_1k=output_cost_per_1k,
            max_output_tokens=max_output_tokens,
            supports_streaming=supports_streaming,
        )

        # 3. Get agent types to register for
        if agent_types is None:
            agent_types = await self._repository.get_all_agent_types()

        # 4. Create ranking entries with overrides
        initial_score = Decimal("1.0")
        expires_at = datetime.utcnow() + timedelta(hours=24)

        for agent_type in agent_types:
            # Create ranking entry
            await self._repository.update_ranking_score(
                agent_type=agent_type,
                model_id=new_model_id,
                ranking_score=initial_score,
                success_rate=Decimal("0.0"),
                latency_score=Decimal("0.5"),
                cost_score=Decimal("0.5"),
                avg_latency_ms=0,
                avg_cost_per_request=Decimal("0.0"),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
            )

            # Create 24h override
            await self._repository.create_override(
                agent_type=agent_type,
                model_id=new_model_id,
                override_score=initial_score,
                reason=f"New model initialization - collecting metrics for 24h",
                created_by=created_by,
                expires_at=expires_at,
            )

        logger.info(
            f"✅ Registered {model_id} for {len(agent_types)} agent types "
            f"with 24h position 1 override"
        )

        return RegisterModelResult(
            model_id=new_model_id,
            model_name=model_id,
            provider_name="deepinfra",
            display_name=display_name,
            initial_ranking_score=initial_score,
            override_expires_at=expires_at,
            agent_types_registered=agent_types,
        )

    async def _get_or_create_provider(
        self, name: str, display_name: str
    ) -> UUID:
        """Get or create provider."""
        # Same as Vertex AI implementation
        return uuid4()

    async def _create_model(
        self,
        model_id: UUID,
        provider_id: UUID,
        model_name: str,
        display_name: str,
        description: Optional[str],
        context_window: Optional[int],
        input_cost_per_1k: Decimal,
        output_cost_per_1k: Decimal,
        max_output_tokens: Optional[int],
        supports_streaming: bool,
    ) -> None:
        """Create model record."""
        logger.info(f"Creating model record: {model_name}")
