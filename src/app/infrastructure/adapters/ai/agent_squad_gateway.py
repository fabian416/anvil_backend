"""
Agent Squad Gateway - Production-grade multi-agent orchestration.

Replaces AgentGatewayImpl with Agent Squad library for:
- Advanced intent classification
- Context preservation
- Supervisor agent patterns
- Multi-agent collaboration
"""

from typing import Dict, Any, Optional
from uuid import UUID

# NOTE: Agent Squad installed as package dependency (see pyproject.toml)
# Additional dependencies: openai, boto3
try:
    from agent_squad.orchestrator import AgentSquad
    from agent_squad.agents.openai_agent import OpenAIAgent
    from agent_squad.types import ConversationMessage, ParticipantRole

    AGENT_SQUAD_AVAILABLE = True
except ImportError as e:
    # Fallback during installation - will be resolved
    AGENT_SQUAD_AVAILABLE = False
    AgentSquad = None
    OpenAIAgent = None
    ConversationMessage = None
    ParticipantRole = None
    print(f"Agent Squad import error: {e}")

from app.domain.ports.ai.agent_gateway import AgentGateway
from app.domain.enums.agent_type import AgentType
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig


class AgentSquadGateway(AgentGateway):
    """
    Production Agent Squad integration.

    Features:
    - Intelligent intent classification via Agent Squad
    - Multi-agent orchestration
    - Context preservation
    - Supervisor patterns
    """

    def __init__(
        self,
        storage: AnvilSquadStorage,
        config: AgentSquadConfig,
    ):
        """
        Initialize Agent Squad Gateway.

        Args:
            storage: Anvil storage adapter for Agent Squad
            config: Agent Squad configuration

        Raises:
            ImportError: If Agent Squad library is not installed
        """
        if not AGENT_SQUAD_AVAILABLE:
            raise ImportError(
                "Agent Squad library not installed. "
                "Install with: pip install agent-squad "
                "or: uv pip install -e '.[dev,test]'"
            )

        self.storage = storage
        self.config = config

        # Create Agent Squad orchestrator
        self.orchestrator = AgentSquad(
            storage=storage,
            options={
                "LOG_AGENT_CHAT": config.log_agent_selection,
                "LOG_CLASSIFIER_CHAT": config.log_intent_classification,
                "LOG_CLASSIFIER_RAW_OUTPUT": config.debug_mode,
                "LOG_CLASSIFIER_OUTPUT": config.debug_mode,
                "LOG_EXECUTION_TIMES": config.debug_mode,
                "MAX_RETRIES": config.max_retries,
                "USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED": True,
            },
        )

        # Register specialized agents
        self._register_agents()

    def _register_agents(self):
        """Register all specialized DeFi agents."""

        # Default model ID for Bedrock Claude
        default_model = (
            self.config.default_model or "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        fallback_model = (
            self.config.fallback_model or "anthropic.claude-3-sonnet-20240229-v1:0"
        )

        # 1. Trading Agent (Swaps, Perps)
        trading_agent = OpenAIAgent(
            name="Trading Agent",
            description="""Specialized in DeFi trading operations including:
            - Token swaps on DEXes (Uniswap, Curve, 1inch)
            - Opening perpetual positions
            - Closing positions
            - Executing market orders
            Always explain risks and ask for confirmation before trades.""",
            model=default_model,
        )
        self.orchestrator.add_agent(trading_agent)

        # 2. Lending Agent (Supply, Borrow)
        lending_agent = OpenAIAgent(
            name="Lending Agent",
            description="""Specialized in DeFi lending and borrowing:
            - Supply/lend tokens (Aave, Compound)
            - Borrow against collateral
            - Manage health factors
            - Calculate optimal collateral ratios
            Always explain liquidation risks.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(lending_agent)

        # 3. Portfolio Agent (View, Analyze)
        portfolio_agent = OpenAIAgent(
            name="Portfolio Agent",
            description="""Specialized in portfolio management:
            - View token balances and positions
            - Analyze portfolio composition
            - Track profit/loss
            - Provide diversification insights
            Display information clearly and concisely.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(portfolio_agent)

        # 4. Market Data Agent (Prices, Rates, Info)
        market_agent = OpenAIAgent(
            name="Market Agent",
            description="""Specialized in DeFi market data:
            - Real-time token prices
            - APY/APR rates
            - TVL and liquidity data
            - Funding rates for perps
            Provide accurate, up-to-date information.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(market_agent)

        # 5. Risk Agent (Analysis, Warnings)
        risk_agent = OpenAIAgent(
            name="Risk Agent",
            description="""Specialized in risk analysis:
            - Assess position risks
            - Calculate liquidation prices
            - Evaluate protocol risks
            - Warn about high-risk operations
            Always be thorough and cautious.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(risk_agent)

        # 6. Research Agent (General Questions, Education)
        research_agent = OpenAIAgent(
            name="Research Agent",
            description="""Specialized in DeFi education and research:
            - Explain DeFi concepts
            - Protocol analysis
            - Answer general questions
            - Provide educational content
            Make complex topics simple and clear.""",
            model=self.config.fallback_model,  # Use cheaper model for education
        )
        self.orchestrator.add_agent(research_agent)

        # Set research agent as default fallback
        self.orchestrator.set_default_agent(research_agent)

    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggested_model: Optional[str] = None,
        suggested_agent: Optional[str] = None,
    ) -> str:
        """
        Process message through Agent Squad orchestrator.

        Args:
            user_id: User identifier
            session_id: Session/conversation identifier
            message: User message content
            context: Optional context dictionary
            suggested_model: Optional model hint (ignored - Agent Squad handles)
            suggested_agent: Optional agent hint for routing

        Returns:
            Agent response text
        """
        try:
            # Convert our user_id to string for Agent Squad
            user_id_str = str(user_id)

            # Route through Agent Squad
            response = await self.orchestrator.route_request(
                user_input=message,
                user_id=user_id_str,
                session_id=session_id,
            )

            # Extract text response
            # Agent Squad returns AgentResponse object
            return self._normalize_agent_response(response)

        except Exception as e:
            # Log error
            print(f"Agent Squad error: {str(e)}")

            # Fallback to friendly error
            return (
                "I apologize, but I encountered an error processing your request. "
                "Please try rephrasing your message or contact support if the issue persists."
            )

    def _normalize_agent_response(self, response: Any) -> str:
        """
        Normalize agent outputs to a plain string.

        Some providers/agents may return structured outputs like:
        - tuple: (text, metadata)
        - dict: { output/content/text: "..." }
        - AgentResponse objects with `.output`

        The chat DB and API contract expect `content` to be a string.
        """
        if response is None:
            return ""

        # Common AgentResponse shape
        if hasattr(response, "output"):
            out = getattr(response, "output")
            # Some integrations may set output as non-str; normalize recursively.
            return self._normalize_agent_response(out)

        if isinstance(response, str):
            return response

        # Handle tuple/list like (text, meta)
        if isinstance(response, (tuple, list)) and len(response) > 0:
            first = response[0]
            if isinstance(first, str):
                return first
            return self._normalize_agent_response(first)

        # Handle dict payloads
        if isinstance(response, dict):
            for key in ("output", "content", "text", "message"):
                value = response.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        # Final fallback
        return str(response)
