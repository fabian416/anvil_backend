"""
Advanced agent orchestration service.

Comprehensive multi-agent coordination including:
- Multi-agent voting and consensus
- Structured agent debates
- Intelligent fallback routing
- Agent performance tracking
- Custom agent creation and management
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from uuid import UUID

from app.domain.entities.chat import Conversation, Message
from app.domain.ports.agent_orchestration_repository import AgentOrchestrationRepository
from app.domain.ports.llm_gateway import LLMGateway
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
    FallbackReason,
    AgentPriority,
    AgentPerformanceMetrics,
    CustomAgentConfig,
    AgentCapability,
)


class AgentOrchestrationService:
    """
    Advanced multi-agent orchestration service.

    Coordinates multiple agents for improved accuracy, reliability,
    and user control over AI interactions.
    """

    def __init__(
        self,
        orchestration_repository: AgentOrchestrationRepository,
        llm_gateway: LLMGateway,
    ) -> None:
        """
        Initialize orchestration service.

        Args:
            orchestration_repository: Repository for orchestration data
            llm_gateway: Gateway for LLM interactions
        """
        self._repository = orchestration_repository
        self._llm = llm_gateway

    # =========================================================================
    # MULTI-AGENT VOTING
    # =========================================================================

    async def conduct_multi_agent_vote(
        self,
        query: str,
        agent_names: List[str],
        conversation: Optional[Conversation] = None,
        strategy: VotingStrategy = VotingStrategy.WEIGHTED,
    ) -> Tuple[str, VotingRound]:
        """
        Conduct multi-agent voting on query response.

        Multiple agents independently generate responses, then vote
        on the best answer using specified voting strategy.

        Args:
            query: User query
            agent_names: List of agents to participate (3+ recommended)
            conversation: Optional conversation context
            strategy: Voting strategy to use

        Returns:
            Tuple of (winning_response, voting_round)

        Example:
            User: "What's the risk of this Aave position?"
            Agents vote:
              - risk_analyzer: "High risk (IL + liquidation)" (confidence: 0.85)
              - yield_optimizer: "Moderate risk for 12% APY" (confidence: 0.75)
              - portfolio_manager: "High risk (IL + liquidation)" (confidence: 0.90)
            Winner: "High risk" (2 votes, avg confidence 0.875)
        """
        if len(agent_names) < 2:
            raise ValueError("At least 2 agents required for voting")

        # Generate responses from each agent concurrently
        response_tasks = [
            self._get_agent_response(agent_name, query, conversation)
            for agent_name in agent_names
        ]
        agent_responses = await asyncio.gather(*response_tasks)

        # Collect votes
        votes: List[AgentVote] = []
        for agent_name, (response, confidence) in zip(agent_names, agent_responses):
            # Get agent performance metrics for weighted voting
            metrics = await self._repository.get_performance_metrics(agent_name)
            vote_weight = self._calculate_vote_weight(metrics, strategy)

            vote = AgentVote(
                agent_name=agent_name,
                response_option=response,
                confidence=confidence,
                reasoning=f"Agent {agent_name} analysis",
                vote_weight=vote_weight,
            )
            votes.append(vote)

        # Create voting round and determine winner
        voting_round = VotingRound(
            query=query,
            votes=votes,
            strategy=strategy,
            total_votes=len(votes),
        )

        winning_response = voting_round.calculate_winner()

        # Calculate consensus confidence
        if winning_response:
            winning_votes = [v for v in votes if v.response_option == winning_response]
            consensus_confidence = sum(v.confidence for v in winning_votes) / len(winning_votes)

            # Update voting round with results
            object.__setattr__(voting_round, "winning_response", winning_response)
            object.__setattr__(voting_round, "winning_vote_count", len(winning_votes))
            object.__setattr__(voting_round, "consensus_confidence", consensus_confidence)
            object.__setattr__(voting_round, "completed_at", datetime.utcnow())

        # Save voting round
        await self._repository.save_voting_round(voting_round)

        return winning_response or votes[0].response_option, voting_round

    async def _get_agent_response(
        self,
        agent_name: str,
        query: str,
        conversation: Optional[Conversation],
    ) -> Tuple[str, float]:
        """
        Get response and confidence from a single agent.

        Args:
            agent_name: Agent identifier
            query: Query to answer
            conversation: Optional conversation context

        Returns:
            Tuple of (response, confidence)
        """
        start_time = datetime.utcnow()

        try:
            # Get response from LLM with agent-specific prompt
            response = await self._llm.chat(
                messages=[{"role": "user", "content": query}],
                system_prompt=f"You are {agent_name}, a specialized DeFi agent.",
            )

            # Extract confidence from response metadata or estimate
            confidence = self._estimate_confidence(response)

            # Update performance metrics
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._update_agent_metrics(
                agent_name=agent_name,
                success=True,
                response_time_ms=response_time_ms,
                confidence=confidence,
                cost_usd=0.001,  # Estimate based on tokens
            )

            return response, confidence

        except Exception as e:
            # Update metrics with failure
            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._update_agent_metrics(
                agent_name=agent_name,
                success=False,
                response_time_ms=response_time_ms,
                confidence=0.0,
                cost_usd=0.0,
                error=str(e),
            )
            return f"Error: {str(e)}", 0.0

    def _calculate_vote_weight(
        self,
        metrics: Optional[AgentPerformanceMetrics],
        strategy: VotingStrategy,
    ) -> float:
        """
        Calculate vote weight based on agent performance.

        Args:
            metrics: Agent performance metrics
            strategy: Voting strategy

        Returns:
            Vote weight (1.0 for equal weight, higher for better performers)
        """
        if strategy != VotingStrategy.WEIGHTED or not metrics:
            return 1.0

        # Weight based on efficiency score
        efficiency = metrics.get_efficiency_score()
        return 0.5 + (efficiency / 100)  # Weight between 0.5 and 1.5

    def _estimate_confidence(self, response: str) -> float:
        """
        Estimate response confidence from content.

        Args:
            response: Agent response

        Returns:
            Estimated confidence (0.0 to 1.0)
        """
        # Simple heuristic - look for uncertainty markers
        uncertainty_markers = [
            "might",
            "maybe",
            "possibly",
            "unclear",
            "uncertain",
            "not sure",
        ]

        lower_response = response.lower()
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in lower_response)

        # Start at 0.8, reduce by 0.1 per uncertainty marker
        confidence = max(0.3, 0.8 - (uncertainty_count * 0.1))

        return confidence

    # =========================================================================
    # AGENT DEBATES
    # =========================================================================

    async def conduct_agent_debate(
        self,
        query: str,
        agent_names: List[str],
        max_rounds: int = 3,
        conversation: Optional[Conversation] = None,
    ) -> AgentDebate:
        """
        Conduct structured debate between agents.

        Agents present arguments, rebut each other, and synthesize
        consensus through deliberative process.

        Args:
            query: Question to debate
            agent_names: Participating agents (2-5 recommended)
            max_rounds: Maximum debate rounds
            conversation: Optional conversation context

        Returns:
            Completed AgentDebate with consensus

        Example:
            Query: "Should I enter this leveraged farming position?"

            Opening Statements:
              - risk_analyzer: "High risk due to IL and liquidation"
              - yield_optimizer: "High reward (45% APY) worth calculated risk"

            Arguments:
              - risk_analyzer: "Historical 30% drawdowns would liquidate"
              - yield_optimizer: "Can hedge IL with options strategy"

            Rebuttals:
              - risk_analyzer: "Options cost reduces net APY to 25%"
              - yield_optimizer: "Still beats alternatives by 2x"

            Synthesis:
              - Consensus: "Enter with 30% position size, hedge with options"
              - Confidence: 75%
        """
        if len(agent_names) < 2 or len(agent_names) > 5:
            raise ValueError("Debates require 2-5 agents")

        debate = AgentDebate(
            query=query,
            participating_agents=agent_names,
            max_rounds=max_rounds,
        )

        # Phase 1: Opening Statements
        await self._debate_opening_statements(debate, agent_names, query, conversation)
        debate.advance_phase()

        # Phase 2: Arguments
        await self._debate_arguments(debate, agent_names, query)
        debate.advance_phase()

        # Phase 3: Rebuttals
        await self._debate_rebuttals(debate, agent_names)
        debate.advance_phase()

        # Phase 4: Synthesis
        consensus = await self._debate_synthesis(debate, agent_names, query)
        debate.advance_phase()

        # Phase 5: Final Vote
        if consensus:
            debate.final_consensus = consensus
            debate.consensus_status = ConsensusStatus.ACHIEVED
            debate.consensus_confidence = 0.75  # Calculate from debate quality
        else:
            debate.consensus_status = ConsensusStatus.FAILED

        debate.completed_at = datetime.utcnow()

        # Save debate
        await self._repository.save_debate(debate)

        return debate

    async def _debate_opening_statements(
        self,
        debate: AgentDebate,
        agent_names: List[str],
        query: str,
        conversation: Optional[Conversation],
    ) -> None:
        """Generate opening statements from each agent."""
        for agent_name in agent_names:
            prompt = f"""
As {agent_name}, provide your opening statement on:
"{query}"

Give your initial position and reasoning (2-3 sentences).
"""
            response, _ = await self._get_agent_response(agent_name, prompt, conversation)

            statement = DebateStatement(
                agent_name=agent_name,
                phase=DebatePhase.OPENING_STATEMENTS,
                content=response,
                position=response[:100],  # First 100 chars as position summary
                confidence=0.7,
            )
            debate.add_statement(statement)

    async def _debate_arguments(
        self,
        debate: AgentDebate,
        agent_names: List[str],
        query: str,
    ) -> None:
        """Each agent presents detailed arguments."""
        opening_statements = debate.get_statements_by_phase(DebatePhase.OPENING_STATEMENTS)

        for agent_name in agent_names:
            # Build context from other agents' opening statements
            other_statements = [s for s in opening_statements if s.agent_name != agent_name]
            context = "\n\n".join(
                f"{s.agent_name}: {s.content}" for s in other_statements
            )

            prompt = f"""
As {agent_name}, provide detailed arguments for your position on:
"{query}"

Other agents have stated:
{context}

Present your detailed arguments (3-4 points).
"""
            response, _ = await self._get_agent_response(agent_name, prompt, None)

            statement = DebateStatement(
                agent_name=agent_name,
                phase=DebatePhase.ARGUMENTS,
                content=response,
                position=opening_statements[0].position,  # Maintain position
                confidence=0.75,
            )
            debate.add_statement(statement)

    async def _debate_rebuttals(
        self,
        debate: AgentDebate,
        agent_names: List[str],
    ) -> None:
        """Each agent rebuts opposing arguments."""
        arguments = debate.get_statements_by_phase(DebatePhase.ARGUMENTS)

        for agent_name in agent_names:
            # Get opposing arguments
            opposing_arguments = [s for s in arguments if s.agent_name != agent_name]

            if not opposing_arguments:
                continue

            # Pick strongest opposing argument to rebut
            strongest_opposing = opposing_arguments[0]

            prompt = f"""
As {agent_name}, rebut this opposing argument:

{strongest_opposing.agent_name}: {strongest_opposing.content}

Provide counter-arguments (2-3 points).
"""
            response, _ = await self._get_agent_response(agent_name, prompt, None)

            statement = DebateStatement(
                agent_name=agent_name,
                phase=DebatePhase.REBUTTALS,
                content=response,
                position=arguments[0].position,
                confidence=0.7,
                references_statement_ids=[strongest_opposing.statement_id],
            )
            debate.add_statement(statement)

    async def _debate_synthesis(
        self,
        debate: AgentDebate,
        agent_names: List[str],
        query: str,
    ) -> Optional[str]:
        """
        Synthesize consensus from debate.

        Args:
            debate: Current debate
            agent_names: Participating agents
            query: Original query

        Returns:
            Consensus statement or None if no consensus
        """
        # Collect all statements
        all_statements = "\n\n".join(
            f"[{s.phase.value}] {s.agent_name}: {s.content}"
            for s in debate.statements
        )

        # Ask neutral synthesizer to find consensus
        synthesis_prompt = f"""
Analyze this multi-agent debate and synthesize a consensus answer:

Query: "{query}"

Debate transcript:
{all_statements}

Provide a balanced consensus that incorporates the strongest points
from all perspectives. If agents fundamentally disagree, state that
clearly and explain the tradeoffs.
"""

        consensus, _ = await self._get_agent_response("synthesizer", synthesis_prompt, None)

        # Record synthesis statement
        statement = DebateStatement(
            agent_name="synthesizer",
            phase=DebatePhase.SYNTHESIS,
            content=consensus,
            position="consensus",
            confidence=0.8,
        )
        debate.add_statement(statement)

        return consensus

    # =========================================================================
    # FALLBACK ROUTING
    # =========================================================================

    async def execute_with_fallback(
        self,
        query: str,
        fallback_chain: FallbackChain,
        conversation: Optional[Conversation] = None,
    ) -> Tuple[str, FallbackChain]:
        """
        Execute query with intelligent fallback routing.

        Tries agents in priority order until successful response.
        Falls back on timeout, error, or low confidence.

        Args:
            query: User query
            fallback_chain: Chain of fallback agents
            conversation: Optional conversation context

        Returns:
            Tuple of (response, updated_fallback_chain)

        Example:
            Chain: primary (risk_analyzer) → secondary (yield_optimizer) → tertiary (general)

            Attempt 1: risk_analyzer times out after 30s → FALLBACK
            Attempt 2: yield_optimizer responds with 40% confidence → FALLBACK (threshold 50%)
            Attempt 3: general agent responds with 75% confidence → SUCCESS
        """
        start_time = datetime.utcnow()
        final_response = None

        while fallback_chain.has_more_agents():
            agent = fallback_chain.get_next_agent()
            if not agent:
                break

            try:
                # Try to get response with timeout
                response, confidence = await asyncio.wait_for(
                    self._get_agent_response(agent.agent_name, query, conversation),
                    timeout=agent.timeout_seconds,
                )

                # Check if should fallback based on confidence
                if agent.should_fallback(confidence, False):
                    fallback_chain.record_attempt(agent.agent_name, FallbackReason.LOW_CONFIDENCE)
                    continue

                # Success!
                final_response = response
                fallback_chain.final_agent_used = agent.agent_name
                break

            except asyncio.TimeoutError:
                fallback_chain.record_attempt(agent.agent_name, FallbackReason.TIMEOUT)
                continue

            except Exception as e:
                fallback_chain.record_attempt(agent.agent_name, FallbackReason.ERROR)
                continue

        # Calculate total time
        fallback_chain.total_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )

        # Save fallback chain execution
        await self._repository.save_fallback_chain(fallback_chain)

        return final_response or "All agents unavailable", fallback_chain

    def create_default_fallback_chain(self) -> FallbackChain:
        """
        Create default fallback chain for DeFi queries.

        Returns:
            FallbackChain with primary, secondary, tertiary agents
        """
        agents = [
            FallbackAgent(
                agent_name="risk_analyzer",
                priority=AgentPriority.PRIMARY,
                timeout_seconds=30,
                min_confidence_threshold=0.7,
            ),
            FallbackAgent(
                agent_name="yield_optimizer",
                priority=AgentPriority.SECONDARY,
                timeout_seconds=45,
                min_confidence_threshold=0.6,
            ),
            FallbackAgent(
                agent_name="general_advisor",
                priority=AgentPriority.TERTIARY,
                timeout_seconds=60,
                min_confidence_threshold=0.5,
            ),
        ]

        return FallbackChain(agents=agents)

    # =========================================================================
    # PERFORMANCE TRACKING
    # =========================================================================

    async def _update_agent_metrics(
        self,
        agent_name: str,
        success: bool,
        response_time_ms: int,
        confidence: float,
        cost_usd: float,
        error: Optional[str] = None,
    ) -> None:
        """
        Update agent performance metrics.

        Args:
            agent_name: Agent identifier
            success: Whether request succeeded
            response_time_ms: Response time
            confidence: Response confidence
            cost_usd: Request cost
            error: Error message if failed
        """
        # Get existing metrics or create new
        metrics = await self._repository.get_performance_metrics(agent_name)
        if not metrics:
            metrics = AgentPerformanceMetrics(agent_name=agent_name)

        # Update with new result
        metrics.update_with_result(success, response_time_ms, confidence, cost_usd, error)

        # Save updated metrics
        await self._repository.save_performance_metrics(metrics)

    async def get_agent_performance_report(
        self,
        agent_name: Optional[str] = None,
    ) -> str:
        """
        Generate agent performance report.

        Args:
            agent_name: Specific agent or None for all agents

        Returns:
            Formatted performance report

        Example output:
            ```
            ┌─ 📊 Agent Performance Report ─┐

            🥇 Top Performing Agents:

            1. risk_analyzer
               • Success rate: 95.2%
               • Avg response: 1.2s
               • Efficiency: 87.5/100
               • Total requests: 1,245

            2. yield_optimizer
               • Success rate: 92.8%
               • Avg response: 1.8s
               • Efficiency: 82.3/100
               • Total requests: 987
            └────────────────────────────────┘
            ```
        """
        if agent_name:
            metrics = await self._repository.get_performance_metrics(agent_name)
            if not metrics:
                return f"No performance data for agent: {agent_name}"

            all_metrics = [metrics]
        else:
            all_metrics = await self._repository.get_top_performing_agents(limit=10)

        if not all_metrics:
            return "No performance data available"

        report_lines = ["┌─ 📊 Agent Performance Report ─┐", "", "🥇 Top Performing Agents:", ""]

        for rank, metrics in enumerate(all_metrics, 1):
            efficiency = metrics.get_efficiency_score()
            success_rate = metrics.get_success_rate()

            report_lines.extend([
                f"{rank}. {metrics.agent_name}",
                f"   • Success rate: {success_rate:.1f}%",
                f"   • Avg response: {metrics.avg_response_time_ms / 1000:.1f}s",
                f"   • Efficiency: {efficiency:.1f}/100",
                f"   • Total requests: {metrics.total_requests:,}",
                f"   • Total cost: ${metrics.total_cost_usd:.2f}",
                "",
            ])

        report_lines.append("└────────────────────────────────┘")

        return "\n".join(report_lines)

    # =========================================================================
    # CUSTOM AGENT MANAGEMENT
    # =========================================================================

    async def create_custom_agent(
        self,
        user_id: UUID,
        config: CustomAgentConfig,
    ) -> CustomAgentConfig:
        """
        Create custom agent configuration.

        Args:
            user_id: User creating the agent
            config: Agent configuration

        Returns:
            Created CustomAgentConfig

        Raises:
            ValueError: If validation fails
        """
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid agent configuration: {', '.join(errors)}")

        # Check for duplicate name
        existing = await self._repository.get_custom_agent_by_name(user_id, config.name)
        if existing:
            raise ValueError(f"Agent with name '{config.name}' already exists")

        # Set creator
        object.__setattr__(config, "created_by_user_id", user_id)

        # Save configuration
        success = await self._repository.save_custom_agent(config)
        if not success:
            raise RuntimeError("Failed to save custom agent")

        return config

    async def update_custom_agent(
        self,
        user_id: UUID,
        config: CustomAgentConfig,
    ) -> CustomAgentConfig:
        """
        Update existing custom agent.

        Args:
            user_id: User updating the agent
            config: Updated configuration

        Returns:
            Updated CustomAgentConfig

        Raises:
            ValueError: If validation fails or not owner
        """
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid agent configuration: {', '.join(errors)}")

        # Verify ownership
        existing = await self._repository.get_custom_agent(config.config_id)
        if not existing or existing.created_by_user_id != user_id:
            raise ValueError("Agent not found or access denied")

        # Update
        success = await self._repository.update_custom_agent(config)
        if not success:
            raise RuntimeError("Failed to update custom agent")

        return config

    async def get_custom_agents(
        self,
        user_id: UUID,
        active_only: bool = True,
    ) -> List[CustomAgentConfig]:
        """
        Get user's custom agents.

        Args:
            user_id: User identifier
            active_only: Only return active agents

        Returns:
            List of custom agent configurations
        """
        return await self._repository.get_user_custom_agents(user_id, active_only)

    async def format_custom_agents_list(
        self,
        user_id: UUID,
    ) -> str:
        """
        Format custom agents list for chat display.

        Returns:
            Formatted agents list
        """
        agents = await self.get_custom_agents(user_id)

        if not agents:
            return "You haven't created any custom agents yet."

        lines = ["┌─ 🤖 Your Custom Agents ─┐", ""]

        for agent in agents:
            capabilities = ", ".join(c.value for c in agent.capabilities[:3])
            lines.extend([
                f"• {agent.name}",
                f"  {agent.description}",
                f"  Capabilities: {capabilities}",
                f"  Style: {agent.response_style}",
                "",
            ])

        lines.append("└──────────────────────────┘")

        return "\n".join(lines)
