"""
Agent orchestration repository adapter implementation.

SQLAlchemy implementation of AgentOrchestrationRepository port for PostgreSQL.
Handles voting rounds, debates, performance metrics, and custom agent configurations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Float, Text, DateTime

from app.domain.ports.agent_orchestration_repository import AgentOrchestrationRepository
from app.domain.value_objects.chat.orchestration import (
    VotingRound,
    AgentVote,
    VotingStrategy,
    AgentDebate,
    DebateStatement,
    DebatePhase,
    ConsensusStatus,
    FallbackChain,
    FallbackAgent,
    AgentPerformanceMetrics,
    CustomAgentConfig,
)
from app.infrastructure.persistence_sqla.base import Base


class AgentOrchestrationRepositoryAdapter(AgentOrchestrationRepository):
    """
    SQLAlchemy adapter for agent orchestration data.

    Manages persistence for:
    - Voting rounds and results
    - Agent debates and consensus
    - Performance metrics tracking
    - Custom agent configurations
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    # =========================================================================
    # VOTING ROUNDS
    # =========================================================================

    async def save_voting_round(self, voting_round: VotingRound) -> bool:
        """
        Save voting round results.

        Args:
            voting_round: Voting round to save

        Returns:
            True if saved successfully
        """
        try:
            # Check if exists
            stmt = select(VotingRoundModel).where(
                VotingRoundModel.round_id == voting_round.round_id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_voting_round_model(existing, voting_round)
            else:
                model = self._voting_round_to_model(voting_round)
                self._session.add(model)

            await self._session.commit()
            return True

        except Exception:
            await self._session.rollback()
            return False

    async def get_voting_round(self, round_id: UUID) -> Optional[VotingRound]:
        """
        Get voting round by ID.

        Args:
            round_id: Round identifier

        Returns:
            VotingRound or None if not found
        """
        stmt = select(VotingRoundModel).where(
            VotingRoundModel.round_id == round_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_voting_round(model)

    async def get_voting_rounds_for_conversation(
        self,
        conversation_id: UUID,
    ) -> List[VotingRound]:
        """
        Get all voting rounds for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of voting rounds
        """
        stmt = (
            select(VotingRoundModel)
            .where(VotingRoundModel.conversation_id == conversation_id)
            .order_by(VotingRoundModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_voting_round(model) for model in models]

    # =========================================================================
    # AGENT DEBATES
    # =========================================================================

    async def save_debate(self, debate: AgentDebate) -> bool:
        """
        Save agent debate.

        Args:
            debate: Agent debate to save

        Returns:
            True if saved successfully
        """
        try:
            # Check if exists
            stmt = select(AgentDebateModel).where(
                AgentDebateModel.debate_id == debate.debate_id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_debate_model(existing, debate)
            else:
                model = self._debate_to_model(debate)
                self._session.add(model)

            await self._session.commit()
            return True

        except Exception:
            await self._session.rollback()
            return False

    async def get_debate(self, debate_id: UUID) -> Optional[AgentDebate]:
        """
        Get debate by ID.

        Args:
            debate_id: Debate identifier

        Returns:
            AgentDebate or None if not found
        """
        stmt = select(AgentDebateModel).where(
            AgentDebateModel.debate_id == debate_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_debate(model)

    async def get_debates_for_conversation(
        self,
        conversation_id: UUID,
    ) -> List[AgentDebate]:
        """
        Get all debates for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of debates
        """
        stmt = (
            select(AgentDebateModel)
            .where(AgentDebateModel.conversation_id == conversation_id)
            .order_by(AgentDebateModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_debate(model) for model in models]

    # =========================================================================
    # FALLBACK CHAINS
    # =========================================================================

    async def save_fallback_chain(self, chain: FallbackChain) -> bool:
        """
        Save fallback chain (stored in debates table with metadata).

        Args:
            chain: Fallback chain to save

        Returns:
            True if saved successfully
        """
        # Fallback chains are tracked within debates or can be stored as metadata
        # For now, this is a placeholder - may need separate table
        return True

    async def get_fallback_chain(
        self,
        conversation_id: UUID,
        query: str,
    ) -> Optional[FallbackChain]:
        """
        Get fallback chain for conversation + query.

        Args:
            conversation_id: Conversation identifier
            query: User query

        Returns:
            FallbackChain or None if not found
        """
        # Placeholder - may need separate table
        return None

    # =========================================================================
    # PERFORMANCE METRICS
    # =========================================================================

    async def get_performance_metrics(
        self,
        agent_name: str,
    ) -> Optional[AgentPerformanceMetrics]:
        """
        Get performance metrics for agent.

        Args:
            agent_name: Agent identifier

        Returns:
            AgentPerformanceMetrics or None if not found
        """
        stmt = select(AgentPerformanceMetricsModel).where(
            AgentPerformanceMetricsModel.agent_name == agent_name
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_metrics(model)

    async def update_performance_metrics(
        self,
        metrics: AgentPerformanceMetrics,
    ) -> bool:
        """
        Update agent performance metrics.

        Args:
            metrics: Updated metrics

        Returns:
            True if updated successfully
        """
        try:
            # Check if exists
            stmt = select(AgentPerformanceMetricsModel).where(
                AgentPerformanceMetricsModel.agent_name == metrics.agent_name
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_metrics_model(existing, metrics)
            else:
                model = self._metrics_to_model(metrics)
                self._session.add(model)

            await self._session.commit()
            return True

        except Exception:
            await self._session.rollback()
            return False

    async def get_top_performing_agents(self, limit: int = 10) -> List[AgentPerformanceMetrics]:
        """
        Get top performing agents by success rate.

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of top performing agents
        """
        stmt = (
            select(AgentPerformanceMetricsModel)
            .order_by(
                (
                    AgentPerformanceMetricsModel.successful_requests
                    / AgentPerformanceMetricsModel.total_requests
                ).desc()
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_metrics(model) for model in models]

    # =========================================================================
    # CUSTOM AGENTS
    # =========================================================================

    async def save_custom_agent(self, config: CustomAgentConfig) -> bool:
        """
        Save custom agent configuration.

        Args:
            config: Custom agent config

        Returns:
            True if saved successfully
        """
        try:
            # Check if exists
            stmt = select(CustomAgentConfigModel).where(
                CustomAgentConfigModel.config_id == config.config_id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_custom_agent_model(existing, config)
            else:
                model = self._custom_agent_to_model(config)
                self._session.add(model)

            await self._session.commit()
            return True

        except Exception:
            await self._session.rollback()
            return False

    async def get_custom_agent(self, config_id: UUID) -> Optional[CustomAgentConfig]:
        """
        Get custom agent by ID.

        Args:
            config_id: Config identifier

        Returns:
            CustomAgentConfig or None if not found
        """
        stmt = select(CustomAgentConfigModel).where(
            CustomAgentConfigModel.config_id == config_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_custom_agent(model)

    async def get_custom_agents_by_creator(
        self,
        user_id: UUID,
    ) -> List[CustomAgentConfig]:
        """
        Get custom agents created by user.

        Args:
            user_id: User identifier

        Returns:
            List of custom agents
        """
        stmt = select(CustomAgentConfigModel).where(
            CustomAgentConfigModel.created_by_user_id == user_id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_custom_agent(model) for model in models]

    async def delete_custom_agent(self, config_id: UUID) -> bool:
        """
        Delete custom agent configuration.

        Args:
            config_id: Config identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(CustomAgentConfigModel).where(
                CustomAgentConfigModel.config_id == config_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.commit()
                return True

            return False

        except Exception:
            await self._session.rollback()
            return False

    # =========================================================================
    # CONVERSION METHODS - VOTING ROUNDS
    # =========================================================================

    def _voting_round_to_model(self, voting_round: VotingRound) -> "VotingRoundModel":
        """Convert VotingRound to database model."""
        # Serialize votes
        votes_data = [
            {
                "agent_name": vote.agent_name,
                "response_option": vote.response_option,
                "confidence": vote.confidence,
                "vote_weight": vote.vote_weight,
                "reasoning": vote.reasoning,
                "voted_at": vote.voted_at.isoformat() if vote.voted_at else None,
            }
            for vote in voting_round.votes
        ]

        return VotingRoundModel(
            round_id=voting_round.round_id,
            conversation_id=voting_round.conversation_id,
            user_id=voting_round.user_id,
            query=voting_round.query,
            strategy=voting_round.strategy.value,
            winning_response=voting_round.winning_response,
            winning_vote_count=voting_round.winning_vote_count,
            total_votes=voting_round.total_votes,
            consensus_confidence=voting_round.consensus_confidence,
            votes=votes_data,
            started_at=voting_round.started_at,
            completed_at=voting_round.completed_at,
        )

    def _update_voting_round_model(
        self,
        model: "VotingRoundModel",
        voting_round: VotingRound,
    ) -> None:
        """Update VotingRound model from value object."""
        votes_data = [
            {
                "agent_name": vote.agent_name,
                "response_option": vote.response_option,
                "confidence": vote.confidence,
                "vote_weight": vote.vote_weight,
                "reasoning": vote.reasoning,
                "voted_at": vote.voted_at.isoformat() if vote.voted_at else None,
            }
            for vote in voting_round.votes
        ]

        model.query = voting_round.query
        model.strategy = voting_round.strategy.value
        model.winning_response = voting_round.winning_response
        model.winning_vote_count = voting_round.winning_vote_count
        model.total_votes = voting_round.total_votes
        model.consensus_confidence = voting_round.consensus_confidence
        model.votes = votes_data
        model.completed_at = voting_round.completed_at

    def _model_to_voting_round(self, model: "VotingRoundModel") -> VotingRound:
        """Convert database model to VotingRound."""
        # Deserialize votes
        votes = [
            AgentVote(
                agent_name=vote_data["agent_name"],
                response_option=vote_data["response_option"],
                confidence=vote_data["confidence"],
                vote_weight=vote_data.get("vote_weight", 1.0),
                reasoning=vote_data.get("reasoning"),
                voted_at=datetime.fromisoformat(vote_data["voted_at"])
                if vote_data.get("voted_at")
                else None,
            )
            for vote_data in model.votes
        ]

        return VotingRound(
            round_id=model.round_id,
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            query=model.query,
            votes=votes,
            strategy=VotingStrategy(model.strategy),
            winning_response=model.winning_response,
            winning_vote_count=model.winning_vote_count,
            total_votes=model.total_votes,
            consensus_confidence=model.consensus_confidence,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    # =========================================================================
    # CONVERSION METHODS - DEBATES
    # =========================================================================

    def _debate_to_model(self, debate: AgentDebate) -> "AgentDebateModel":
        """Convert AgentDebate to database model."""
        # Serialize statements
        statements_data = [
            {
                "agent_name": stmt.agent_name,
                "phase": stmt.phase.value,
                "content": stmt.content,
                "confidence": stmt.confidence,
                "references_statement_indices": stmt.references_statement_indices,
                "timestamp": stmt.timestamp.isoformat() if stmt.timestamp else None,
            }
            for stmt in debate.statements
        ]

        return AgentDebateModel(
            debate_id=debate.debate_id,
            conversation_id=debate.conversation_id,
            user_id=debate.user_id,
            query=debate.query,
            participating_agents=debate.participating_agents,
            current_phase=debate.current_phase.value,
            consensus_status=debate.consensus_status.value,
            final_consensus=debate.final_consensus,
            consensus_confidence=debate.consensus_confidence,
            statements=statements_data,
            max_rounds=debate.max_rounds,
            current_round=debate.current_round,
            started_at=debate.started_at,
            completed_at=debate.completed_at,
        )

    def _update_debate_model(
        self,
        model: "AgentDebateModel",
        debate: AgentDebate,
    ) -> None:
        """Update AgentDebate model from value object."""
        statements_data = [
            {
                "agent_name": stmt.agent_name,
                "phase": stmt.phase.value,
                "content": stmt.content,
                "confidence": stmt.confidence,
                "references_statement_indices": stmt.references_statement_indices,
                "timestamp": stmt.timestamp.isoformat() if stmt.timestamp else None,
            }
            for stmt in debate.statements
        ]

        model.current_phase = debate.current_phase.value
        model.consensus_status = debate.consensus_status.value
        model.final_consensus = debate.final_consensus
        model.consensus_confidence = debate.consensus_confidence
        model.statements = statements_data
        model.current_round = debate.current_round
        model.completed_at = debate.completed_at

    def _model_to_debate(self, model: "AgentDebateModel") -> AgentDebate:
        """Convert database model to AgentDebate."""
        # Deserialize statements
        statements = [
            DebateStatement(
                agent_name=stmt_data["agent_name"],
                phase=DebatePhase(stmt_data["phase"]),
                content=stmt_data["content"],
                confidence=stmt_data["confidence"],
                references_statement_indices=stmt_data.get("references_statement_indices", []),
                timestamp=datetime.fromisoformat(stmt_data["timestamp"])
                if stmt_data.get("timestamp")
                else None,
            )
            for stmt_data in model.statements
        ]

        return AgentDebate(
            debate_id=model.debate_id,
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            query=model.query,
            participating_agents=model.participating_agents,
            statements=statements,
            current_phase=DebatePhase(model.current_phase),
            consensus_status=ConsensusStatus(model.consensus_status),
            final_consensus=model.final_consensus,
            consensus_confidence=model.consensus_confidence,
            max_rounds=model.max_rounds,
            current_round=model.current_round,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    # =========================================================================
    # CONVERSION METHODS - METRICS
    # =========================================================================

    def _metrics_to_model(
        self,
        metrics: AgentPerformanceMetrics,
    ) -> "AgentPerformanceMetricsModel":
        """Convert AgentPerformanceMetrics to database model."""
        return AgentPerformanceMetricsModel(
            agent_name=metrics.agent_name,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            avg_response_time_ms=metrics.avg_response_time_ms,
            avg_confidence=metrics.avg_confidence,
            avg_cost_usd=metrics.avg_cost_usd,
            total_cost_usd=metrics.total_cost_usd,
            uptime_percentage=metrics.uptime_percentage,
            last_24h_requests=metrics.last_24h_requests,
            last_error=metrics.last_error,
            last_error_at=metrics.last_error_at,
            created_at=metrics.created_at,
            updated_at=metrics.updated_at,
        )

    def _update_metrics_model(
        self,
        model: "AgentPerformanceMetricsModel",
        metrics: AgentPerformanceMetrics,
    ) -> None:
        """Update AgentPerformanceMetrics model from value object."""
        model.total_requests = metrics.total_requests
        model.successful_requests = metrics.successful_requests
        model.failed_requests = metrics.failed_requests
        model.avg_response_time_ms = metrics.avg_response_time_ms
        model.avg_confidence = metrics.avg_confidence
        model.avg_cost_usd = metrics.avg_cost_usd
        model.total_cost_usd = metrics.total_cost_usd
        model.uptime_percentage = metrics.uptime_percentage
        model.last_24h_requests = metrics.last_24h_requests
        model.last_error = metrics.last_error
        model.last_error_at = metrics.last_error_at
        model.updated_at = metrics.updated_at

    def _model_to_metrics(
        self,
        model: "AgentPerformanceMetricsModel",
    ) -> AgentPerformanceMetrics:
        """Convert database model to AgentPerformanceMetrics."""
        return AgentPerformanceMetrics(
            agent_name=model.agent_name,
            total_requests=model.total_requests,
            successful_requests=model.successful_requests,
            failed_requests=model.failed_requests,
            avg_response_time_ms=model.avg_response_time_ms,
            avg_confidence=model.avg_confidence,
            avg_cost_usd=model.avg_cost_usd,
            total_cost_usd=model.total_cost_usd,
            uptime_percentage=model.uptime_percentage,
            last_24h_requests=model.last_24h_requests,
            last_error=model.last_error,
            last_error_at=model.last_error_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # =========================================================================
    # CONVERSION METHODS - CUSTOM AGENTS
    # =========================================================================

    def _custom_agent_to_model(
        self,
        config: CustomAgentConfig,
    ) -> "CustomAgentConfigModel":
        """Convert CustomAgentConfig to database model."""
        return CustomAgentConfigModel(
            config_id=config.config_id,
            created_by_user_id=config.created_by_user_id,
            name=config.name,
            description=config.description,
            system_prompt=config.system_prompt,
            capabilities=config.capabilities,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            personality_traits=config.personality_traits,
            expertise_areas=config.expertise_areas,
            response_style=config.response_style,
            preferred_llm_provider=config.preferred_llm_provider,
            fallback_llm_provider=config.fallback_llm_provider,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    def _update_custom_agent_model(
        self,
        model: "CustomAgentConfigModel",
        config: CustomAgentConfig,
    ) -> None:
        """Update CustomAgentConfig model from value object."""
        model.name = config.name
        model.description = config.description
        model.system_prompt = config.system_prompt
        model.capabilities = config.capabilities
        model.temperature = config.temperature
        model.max_tokens = config.max_tokens
        model.personality_traits = config.personality_traits
        model.expertise_areas = config.expertise_areas
        model.response_style = config.response_style
        model.preferred_llm_provider = config.preferred_llm_provider
        model.fallback_llm_provider = config.fallback_llm_provider
        model.is_active = config.is_active
        model.updated_at = config.updated_at

    def _model_to_custom_agent(
        self,
        model: "CustomAgentConfigModel",
    ) -> CustomAgentConfig:
        """Convert database model to CustomAgentConfig."""
        return CustomAgentConfig(
            config_id=model.config_id,
            created_by_user_id=model.created_by_user_id,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            capabilities=model.capabilities,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            personality_traits=model.personality_traits,
            expertise_areas=model.expertise_areas,
            response_style=model.response_style,
            preferred_llm_provider=model.preferred_llm_provider,
            fallback_llm_provider=model.fallback_llm_provider,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


# =============================================================================
# DATABASE MODELS
# =============================================================================


class VotingRoundModel(Base):
    """SQLAlchemy model for voting rounds."""

    __tablename__ = "voting_rounds"

    round_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[str] = mapped_column(String(30), nullable=False)

    # Results
    winning_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    winning_vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consensus_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Votes stored as JSONB
    votes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AgentDebateModel(Base):
    """SQLAlchemy model for agent debates."""

    __tablename__ = "agent_debates"

    debate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    participating_agents: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    current_phase: Mapped[str] = mapped_column(String(30), nullable=False)
    consensus_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Results
    final_consensus: Mapped[str | None] = mapped_column(Text, nullable=True)
    consensus_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Debate data
    statements: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AgentPerformanceMetricsModel(Base):
    """SQLAlchemy model for agent performance metrics."""

    __tablename__ = "agent_performance_metrics"

    agent_name: Mapped[str] = mapped_column(String(100), primary_key=True)

    total_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    avg_response_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    uptime_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    last_24h_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CustomAgentConfigModel(Base):
    """SQLAlchemy model for custom agent configurations."""

    __tablename__ = "custom_agent_configs"

    config_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    created_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Configuration
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    personality_traits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expertise_areas: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    response_style: Mapped[str] = mapped_column(String(20), nullable=False, default="balanced")

    # LLM settings
    preferred_llm_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="openai"
    )
    fallback_llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
