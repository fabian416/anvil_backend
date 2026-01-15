"""
Advanced agent orchestration value objects.

This module provides domain models for:
- Multi-agent voting and consensus
- Agent debate systems
- Fallback agent routing
- Agent performance tracking
- Custom agent configuration
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


# =============================================================================
# VOTING AND CONSENSUS
# =============================================================================


class VotingStrategy(Enum):
    """Voting strategies for multi-agent consensus."""

    MAJORITY = "majority"  # Simple majority wins
    WEIGHTED = "weighted"  # Weight by agent performance history
    UNANIMOUS = "unanimous"  # All agents must agree
    RANKED_CHOICE = "ranked_choice"  # Agents rank options, highest total wins
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Require minimum confidence


class ConsensusStatus(Enum):
    """Status of consensus-building process."""

    ACHIEVED = "achieved"  # Consensus reached
    IN_PROGRESS = "in_progress"  # Still deliberating
    FAILED = "failed"  # Could not reach consensus
    TIMEOUT = "timeout"  # Deliberation exceeded time limit


@dataclass(frozen=True)
class AgentVote:
    """
    A single agent's vote on a response.

    Captures the agent's choice, confidence, and reasoning
    for voting decisions.
    """

    agent_name: str
    response_option: str  # The response text being voted for
    confidence: float  # 0.0 to 1.0
    reasoning: str
    vote_weight: float = 1.0  # For weighted voting
    voted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate vote data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.vote_weight < 0:
            raise ValueError("Vote weight cannot be negative")


@dataclass(frozen=True)
class VotingRound:
    """
    Results from a single voting round.

    Tracks all votes, winner, and voting statistics.
    """

    round_id: UUID = field(default_factory=uuid4)
    query: str = ""
    votes: List[AgentVote] = field(default_factory=list)
    strategy: VotingStrategy = VotingStrategy.MAJORITY
    winning_response: Optional[str] = None
    winning_vote_count: int = 0
    total_votes: int = 0
    consensus_confidence: float = 0.0  # Average confidence in winner
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None

    def calculate_winner(self) -> Optional[str]:
        """
        Determine winning response based on voting strategy.

        Returns:
            Winning response text or None if no clear winner
        """
        if not self.votes:
            return None

        if self.strategy == VotingStrategy.MAJORITY:
            return self._majority_winner()
        elif self.strategy == VotingStrategy.WEIGHTED:
            return self._weighted_winner()
        elif self.strategy == VotingStrategy.UNANIMOUS:
            return self._unanimous_winner()
        elif self.strategy == VotingStrategy.CONFIDENCE_THRESHOLD:
            return self._confidence_threshold_winner()
        else:
            return self._majority_winner()  # Default fallback

    def _majority_winner(self) -> Optional[str]:
        """Simple majority vote - most votes wins."""
        vote_counts: Dict[str, int] = {}
        for vote in self.votes:
            vote_counts[vote.response_option] = vote_counts.get(vote.response_option, 0) + 1

        if not vote_counts:
            return None

        max_votes = max(vote_counts.values())
        winners = [resp for resp, count in vote_counts.items() if count == max_votes]

        # If tie, use highest confidence
        if len(winners) > 1:
            return self._break_tie_by_confidence(winners)

        return winners[0]

    def _weighted_winner(self) -> Optional[str]:
        """Weighted vote - votes weighted by agent performance."""
        weighted_scores: Dict[str, float] = {}
        for vote in self.votes:
            weighted_scores[vote.response_option] = (
                weighted_scores.get(vote.response_option, 0.0) + vote.vote_weight
            )

        if not weighted_scores:
            return None

        return max(weighted_scores.items(), key=lambda x: x[1])[0]

    def _unanimous_winner(self) -> Optional[str]:
        """Unanimous vote - all agents must agree."""
        if not self.votes:
            return None

        first_choice = self.votes[0].response_option
        if all(vote.response_option == first_choice for vote in self.votes):
            return first_choice

        return None  # No unanimous agreement

    def _confidence_threshold_winner(self, threshold: float = 0.7) -> Optional[str]:
        """Winner must have average confidence above threshold."""
        confidence_by_response: Dict[str, List[float]] = {}
        for vote in self.votes:
            if vote.response_option not in confidence_by_response:
                confidence_by_response[vote.response_option] = []
            confidence_by_response[vote.response_option].append(vote.confidence)

        # Find response with highest average confidence above threshold
        best_response = None
        best_avg_confidence = 0.0

        for response, confidences in confidence_by_response.items():
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence >= threshold and avg_confidence > best_avg_confidence:
                best_avg_confidence = avg_confidence
                best_response = response

        return best_response

    def _break_tie_by_confidence(self, tied_responses: List[str]) -> str:
        """Break voting tie by selecting response with highest confidence."""
        confidence_by_response: Dict[str, float] = {}
        for response in tied_responses:
            votes_for_response = [v for v in self.votes if v.response_option == response]
            avg_confidence = sum(v.confidence for v in votes_for_response) / len(
                votes_for_response
            )
            confidence_by_response[response] = avg_confidence

        return max(confidence_by_response.items(), key=lambda x: x[1])[0]


# =============================================================================
# AGENT DEBATE
# =============================================================================


class DebatePhase(Enum):
    """Phases of structured agent debate."""

    OPENING_STATEMENTS = "opening_statements"
    ARGUMENTS = "arguments"
    REBUTTALS = "rebuttals"
    SYNTHESIS = "synthesis"
    FINAL_VOTE = "final_vote"


@dataclass(frozen=True)
class DebateStatement:
    """
    A statement made by an agent during debate.

    Can be an argument, rebuttal, or synthesis.
    """

    statement_id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    phase: DebatePhase = DebatePhase.OPENING_STATEMENTS
    content: str = ""
    position: str = ""  # The position being argued
    confidence: float = 0.0
    references_statement_ids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_rebuttal_to(self, other_statement_id: UUID) -> bool:
        """Check if this statement rebuts another."""
        return other_statement_id in self.references_statement_ids


@dataclass
class AgentDebate:
    """
    Structured debate between multiple agents.

    Agents present arguments, rebut each other, and synthesize
    consensus through structured deliberation.
    """

    debate_id: UUID = field(default_factory=uuid4)
    query: str = ""
    participating_agents: List[str] = field(default_factory=list)
    statements: List[DebateStatement] = field(default_factory=list)
    current_phase: DebatePhase = DebatePhase.OPENING_STATEMENTS
    consensus_status: ConsensusStatus = ConsensusStatus.IN_PROGRESS
    final_consensus: Optional[str] = None
    consensus_confidence: float = 0.0
    max_rounds: int = 3
    current_round: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None

    def add_statement(self, statement: DebateStatement) -> None:
        """Add a debate statement."""
        self.statements.append(statement)

    def advance_phase(self) -> None:
        """Advance to next debate phase."""
        phase_order = [
            DebatePhase.OPENING_STATEMENTS,
            DebatePhase.ARGUMENTS,
            DebatePhase.REBUTTALS,
            DebatePhase.SYNTHESIS,
            DebatePhase.FINAL_VOTE,
        ]

        current_index = phase_order.index(self.current_phase)
        if current_index < len(phase_order) - 1:
            self.current_phase = phase_order[current_index + 1]

    def is_complete(self) -> bool:
        """Check if debate has reached conclusion."""
        return (
            self.consensus_status != ConsensusStatus.IN_PROGRESS
            or self.current_phase == DebatePhase.FINAL_VOTE
            or self.current_round >= self.max_rounds
        )

    def get_statements_by_phase(self, phase: DebatePhase) -> List[DebateStatement]:
        """Get all statements from a specific phase."""
        return [s for s in self.statements if s.phase == phase]


# =============================================================================
# FALLBACK ROUTING
# =============================================================================


class AgentPriority(Enum):
    """Priority levels for fallback routing."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    FALLBACK = "fallback"


class FallbackReason(Enum):
    """Reasons for falling back to next agent."""

    TIMEOUT = "timeout"
    ERROR = "error"
    LOW_CONFIDENCE = "low_confidence"
    UNAVAILABLE = "unavailable"
    OVERLOADED = "overloaded"


@dataclass(frozen=True)
class FallbackAgent:
    """
    Agent configuration for fallback chain.

    Defines priority, timeout, and confidence thresholds.
    """

    agent_name: str
    priority: AgentPriority
    timeout_seconds: int = 30
    min_confidence_threshold: float = 0.5
    max_retries: int = 2
    is_available: bool = True

    def should_fallback(self, confidence: Optional[float], error: bool) -> bool:
        """
        Determine if should fallback to next agent.

        Args:
            confidence: Response confidence (if available)
            error: Whether an error occurred

        Returns:
            True if should fallback
        """
        if error:
            return True
        if confidence is not None and confidence < self.min_confidence_threshold:
            return True
        return False


@dataclass
class FallbackChain:
    """
    Chain of fallback agents for resilient routing.

    Attempts agents in priority order until successful response.
    """

    chain_id: UUID = field(default_factory=uuid4)
    agents: List[FallbackAgent] = field(default_factory=list)
    current_agent_index: int = 0
    attempts: List[str] = field(default_factory=list)  # Agent names attempted
    fallback_reasons: List[FallbackReason] = field(default_factory=list)
    final_agent_used: Optional[str] = None
    total_time_ms: int = 0

    def get_next_agent(self) -> Optional[FallbackAgent]:
        """Get next available agent in chain."""
        while self.current_agent_index < len(self.agents):
            agent = self.agents[self.current_agent_index]
            if agent.is_available:
                return agent
            self.current_agent_index += 1

        return None  # No more agents available

    def record_attempt(self, agent_name: str, reason: Optional[FallbackReason] = None) -> None:
        """Record agent attempt and fallback reason."""
        self.attempts.append(agent_name)
        if reason:
            self.fallback_reasons.append(reason)
        self.current_agent_index += 1

    def has_more_agents(self) -> bool:
        """Check if more fallback agents are available."""
        return self.current_agent_index < len(self.agents)


# =============================================================================
# AGENT PERFORMANCE TRACKING
# =============================================================================


@dataclass
class AgentPerformanceMetrics:
    """
    Performance metrics for an individual agent.

    Tracks accuracy, speed, cost, and reliability over time.
    """

    agent_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    avg_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    uptime_percentage: float = 100.0
    last_24h_requests: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_with_result(
        self,
        success: bool,
        response_time_ms: int,
        confidence: Optional[float],
        cost_usd: float,
        error: Optional[str] = None,
    ) -> None:
        """
        Update metrics with new result.

        Args:
            success: Whether request was successful
            response_time_ms: Response time in milliseconds
            confidence: Response confidence (0.0 to 1.0)
            cost_usd: Cost of this request
            error: Error message if failed
        """
        self.total_requests += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            self.last_error = error
            self.last_error_at = datetime.now(UTC)

        # Update rolling averages
        self.avg_response_time_ms = self._update_average(
            self.avg_response_time_ms, response_time_ms, self.total_requests
        )

        if confidence is not None:
            self.avg_confidence = self._update_average(
                self.avg_confidence, confidence, self.total_requests
            )

        self.avg_cost_usd = self._update_average(self.avg_cost_usd, cost_usd, self.total_requests)
        self.total_cost_usd += cost_usd

        self.uptime_percentage = (self.successful_requests / self.total_requests) * 100
        self.updated_at = datetime.now(UTC)

    def _update_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Update rolling average with new value."""
        return ((current_avg * (count - 1)) + new_value) / count

    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def get_efficiency_score(self) -> float:
        """
        Calculate overall efficiency score (0-100).

        Combines success rate, speed, and confidence.
        """
        if self.total_requests == 0:
            return 0.0

        success_score = self.get_success_rate()
        speed_score = max(0, 100 - (self.avg_response_time_ms / 100))  # Penalty for slow responses
        confidence_score = self.avg_confidence * 100

        return (success_score * 0.4) + (speed_score * 0.3) + (confidence_score * 0.3)


# =============================================================================
# CUSTOM AGENT CONFIGURATION
# =============================================================================


class AgentCapability(Enum):
    """Agent capabilities for custom configuration."""

    GENERAL_QA = "general_qa"
    DEFI_ANALYSIS = "defi_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    MARKET_RESEARCH = "market_research"
    CODE_REVIEW = "code_review"
    CREATIVE_WRITING = "creative_writing"


@dataclass
class CustomAgentConfig:
    """
    User-defined custom agent configuration.

    Allows users to create agents with specific personalities,
    expertise, and behavior patterns.
    """

    config_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 1000
    personality_traits: Dict[str, float] = field(default_factory=dict)  # e.g., {"formal": 0.8}
    expertise_areas: List[str] = field(default_factory=list)
    response_style: str = "balanced"  # concise, balanced, detailed
    preferred_llm_provider: str = "openai"
    fallback_llm_provider: Optional[str] = None
    is_active: bool = True
    created_by_user_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_llm_prompt(self) -> str:
        """
        Convert configuration to LLM system prompt.

        Returns:
            Formatted system prompt for LLM
        """
        prompt_parts = [f"You are {self.name}.", f"{self.description}"]

        if self.expertise_areas:
            prompt_parts.append(f"Your areas of expertise: {', '.join(self.expertise_areas)}")

        if self.personality_traits:
            traits_str = ", ".join(
                f"{trait} ({score:.1%})" for trait, score in self.personality_traits.items()
            )
            prompt_parts.append(f"Personality traits: {traits_str}")

        prompt_parts.append(f"Response style: {self.response_style}")
        prompt_parts.append(self.system_prompt)

        return "\n\n".join(prompt_parts)

    def validate(self) -> List[str]:
        """
        Validate agent configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.name or len(self.name) < 3:
            errors.append("Agent name must be at least 3 characters")

        if not self.description:
            errors.append("Agent description is required")

        if not self.system_prompt:
            errors.append("System prompt is required")

        if not 0.0 <= self.temperature <= 2.0:
            errors.append("Temperature must be between 0.0 and 2.0")

        if self.max_tokens < 100 or self.max_tokens > 8000:
            errors.append("Max tokens must be between 100 and 8000")

        return errors
