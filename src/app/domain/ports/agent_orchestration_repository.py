"""
Agent orchestration repository port.

Domain-defined interface for storing and retrieving
multi-agent coordination data (voting, debates, performance).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.value_objects.chat.orchestration import (
    VotingRound,
    AgentDebate,
    FallbackChain,
    AgentPerformanceMetrics,
    CustomAgentConfig,
    VotingStrategy,
    DebatePhase,
)


class AgentOrchestrationRepository(ABC):
    """
    Port for agent orchestration data persistence.

    Handles storage of voting rounds, debates, fallback chains,
    performance metrics, and custom agent configurations.
    """

    # =========================================================================
    # VOTING ROUNDS
    # =========================================================================

    @abstractmethod
    async def save_voting_round(self, voting_round: VotingRound) -> bool:
        """
        Save a voting round.

        Args:
            voting_round: VotingRound to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    async def get_voting_round(self, round_id: UUID) -> Optional[VotingRound]:
        """
        Get voting round by ID.

        Args:
            round_id: Round identifier

        Returns:
            VotingRound or None if not found
        """
        pass

    @abstractmethod
    async def get_voting_history(
        self,
        user_id: UUID,
        limit: int = 50,
        strategy: Optional[VotingStrategy] = None,
    ) -> List[VotingRound]:
        """
        Get user's voting history.

        Args:
            user_id: User identifier
            limit: Maximum number of rounds to retrieve
            strategy: Filter by voting strategy

        Returns:
            List of voting rounds
        """
        pass

    # =========================================================================
    # AGENT DEBATES
    # =========================================================================

    @abstractmethod
    async def save_debate(self, debate: AgentDebate) -> bool:
        """
        Save an agent debate.

        Args:
            debate: AgentDebate to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    async def get_debate(self, debate_id: UUID) -> Optional[AgentDebate]:
        """
        Get debate by ID.

        Args:
            debate_id: Debate identifier

        Returns:
            AgentDebate or None if not found
        """
        pass

    @abstractmethod
    async def get_active_debates(self, user_id: UUID) -> List[AgentDebate]:
        """
        Get user's active debates.

        Args:
            user_id: User identifier

        Returns:
            List of in-progress debates
        """
        pass

    @abstractmethod
    async def get_debate_history(
        self,
        user_id: UUID,
        limit: int = 20,
        phase: Optional[DebatePhase] = None,
    ) -> List[AgentDebate]:
        """
        Get user's debate history.

        Args:
            user_id: User identifier
            limit: Maximum number of debates
            phase: Filter by final phase reached

        Returns:
            List of debates
        """
        pass

    # =========================================================================
    # FALLBACK CHAINS
    # =========================================================================

    @abstractmethod
    async def save_fallback_chain(self, chain: FallbackChain) -> bool:
        """
        Save fallback chain execution.

        Args:
            chain: FallbackChain to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    async def get_fallback_chain(self, chain_id: UUID) -> Optional[FallbackChain]:
        """
        Get fallback chain by ID.

        Args:
            chain_id: Chain identifier

        Returns:
            FallbackChain or None if not found
        """
        pass

    @abstractmethod
    async def get_fallback_statistics(
        self,
        user_id: UUID,
        days: int = 7,
    ) -> dict:
        """
        Get fallback statistics for user.

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Dictionary with fallback metrics:
                - total_fallbacks: int
                - fallback_rate: float
                - primary_success_rate: float
                - avg_agents_tried: float
                - most_common_reason: str
        """
        pass

    # =========================================================================
    # PERFORMANCE METRICS
    # =========================================================================

    @abstractmethod
    async def save_performance_metrics(self, metrics: AgentPerformanceMetrics) -> bool:
        """
        Save agent performance metrics.

        Args:
            metrics: AgentPerformanceMetrics to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    async def get_performance_metrics(
        self, agent_name: str
    ) -> Optional[AgentPerformanceMetrics]:
        """
        Get current performance metrics for agent.

        Args:
            agent_name: Agent identifier

        Returns:
            AgentPerformanceMetrics or None if not found
        """
        pass

    @abstractmethod
    async def get_all_performance_metrics(self) -> List[AgentPerformanceMetrics]:
        """
        Get performance metrics for all agents.

        Returns:
            List of AgentPerformanceMetrics
        """
        pass

    @abstractmethod
    async def get_top_performing_agents(
        self,
        limit: int = 10,
        metric: str = "efficiency_score",
    ) -> List[AgentPerformanceMetrics]:
        """
        Get top performing agents.

        Args:
            limit: Number of agents to return
            metric: Metric to sort by (efficiency_score, success_rate, etc.)

        Returns:
            List of top performing agents
        """
        pass

    # =========================================================================
    # CUSTOM AGENT CONFIGURATIONS
    # =========================================================================

    @abstractmethod
    async def save_custom_agent(self, config: CustomAgentConfig) -> bool:
        """
        Save custom agent configuration.

        Args:
            config: CustomAgentConfig to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    async def get_custom_agent(self, config_id: UUID) -> Optional[CustomAgentConfig]:
        """
        Get custom agent by ID.

        Args:
            config_id: Configuration identifier

        Returns:
            CustomAgentConfig or None if not found
        """
        pass

    @abstractmethod
    async def get_custom_agent_by_name(
        self,
        user_id: UUID,
        name: str,
    ) -> Optional[CustomAgentConfig]:
        """
        Get custom agent by name for user.

        Args:
            user_id: User identifier
            name: Agent name

        Returns:
            CustomAgentConfig or None if not found
        """
        pass

    @abstractmethod
    async def get_user_custom_agents(
        self,
        user_id: UUID,
        active_only: bool = True,
    ) -> List[CustomAgentConfig]:
        """
        Get all custom agents created by user.

        Args:
            user_id: User identifier
            active_only: Only return active agents

        Returns:
            List of custom agent configurations
        """
        pass

    @abstractmethod
    async def update_custom_agent(self, config: CustomAgentConfig) -> bool:
        """
        Update existing custom agent.

        Args:
            config: Updated CustomAgentConfig

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def delete_custom_agent(self, config_id: UUID) -> bool:
        """
        Delete custom agent configuration.

        Args:
            config_id: Configuration identifier

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def search_custom_agents(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[CustomAgentConfig]:
        """
        Search custom agents by name or description.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum results

        Returns:
            List of matching custom agents
        """
        pass
