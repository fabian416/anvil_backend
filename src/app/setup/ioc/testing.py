"""
Test-specific DI providers for integration testing.

This module provides real database connections for integration tests
plus mock LLM providers for fast, deterministic testing.
"""

from collections.abc import Iterable, AsyncIterator
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from dishka import Provider, provide, Scope
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from redis.asyncio import Redis, ConnectionPool

# Domain Ports for Mocking
from app.domain.ports.chat_llm_provider import ChatLLMProvider
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

# GraphRAG Handlers (for mocking)
from app.application.chat.graph_search_handler import (
    ChatGraphSearchHandler,
    ChatSearchContext,
    ChatProtocolSearchResult,
)
from app.application.chat.risk_insights_handler import (
    ChatRiskInsightsHandler,
    RiskInsightResponse,
    ChatRiskAnalysis,
    ChatRiskFactor,
    ChatAlternativeProtocol,
)


class MockChatLLMProvider(ChatLLMProvider):
    """
    Mock LLM provider for integration testing.

    Returns deterministic responses based on intent detection,
    avoiding real API calls for fast, reliable tests.
    """

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate mock chat response based on message content.

        Returns structured response matching expected format without
        making actual LLM API calls.
        """
        # Extract user message
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        # Generate deterministic response based on keywords
        response_content = self._generate_mock_response(user_message)

        return {
            "content": response_content,
            "model": "mock-llm-4",
            "tokens_used": len(response_content.split()) * 2,
            "finish_reason": "stop",
        }

    def _generate_mock_response(self, user_message: str) -> str:
        """Generate contextually appropriate mock response."""
        message_lower = user_message.lower()

        # Protocol search responses
        if any(word in message_lower for word in ["protocol", "aave", "compound", "lending"]):
            return """Here are the top protocols:

1. **Aave V3** - Leading lending protocol
   - TVL: $12.5B
   - Risk Score: Low
   - Why: High liquidity and proven track record

2. **Compound V3** - Established DeFi protocol
   - TVL: $8.2B
   - Risk Score: Low
   - Why: Strong governance and security

These protocols are well-audited and suitable for your needs."""

        # Risk assessment responses
        if any(word in message_lower for word in ["risk", "safe", "security", "audit"]):
            return """Based on my analysis:

**Overall Risk Assessment:** Low to Medium

**Key Factors:**
- Protocol has been audited by 3+ firms
- TVL stability indicates user confidence
- No major exploits in the last 12 months

**Recommendation:** Suitable for moderate-risk portfolios with proper diversification."""

        # Sentiment analysis responses
        if any(word in message_lower for word in ["sentiment", "bullish", "bearish", "opinion"]):
            return """**Current Sentiment:** Bullish

**Market Indicators:**
- Social media mentions: +45% (trending)
- Trading volume: Increasing
- Whale activity: Accumulation phase

**Recommendation:** Sentiment is positive but monitor for trend reversal signals."""

        # Arbitrage responses
        if any(word in message_lower for word in ["arbitrage", "opportunity", "profit", "dex"]):
            return """**Arbitrage Opportunity Detected:**

- **DEX Pair:** UniswapV3 → SushiSwap
- **Estimated Profit:** 2.3% after gas
- **Capital Required:** $50,000 minimum
- **Risk Level:** Medium (slippage risk)

Execute quickly as opportunities are time-sensitive."""

        # Agent Squad responses
        if any(word in message_lower for word in ["analyze", "research", "investigate", "complex"]):
            return """I'll coordinate a multi-agent analysis for this complex request.

**Agents Deployed:**
1. Research Agent - Gathering data
2. Analysis Agent - Processing information
3. Synthesis Agent - Creating recommendations

Results will be comprehensive and cover multiple angles."""

        # Default general chat response
        return """I understand your question. Let me help you with that.

Based on current data and market conditions, here's what I can tell you:

This is a mock response for testing purposes. In production, this would contain detailed analysis based on real-time data and LLM processing.

Is there anything specific you'd like me to focus on?"""


class MockLLMClientGateway(LLMClientGateway):
    """
    Mock LLM client gateway for integration testing.

    Provides deterministic responses for intent detection, agent
    recommendation, and workflow planning without making real API calls.
    """

    async def classify_intent(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Mock intent classification."""
        # Simple keyword-based intent detection for testing
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["protocol", "aave", "compound", "lending"]):
            return {
                "intent": "protocol_search",
                "confidence": 0.95,
                "reasoning": "Query mentions protocol names and lending keywords",
            }
        elif any(word in prompt_lower for word in ["risk", "safe", "security"]):
            return {
                "intent": "risk_assessment",
                "confidence": 0.92,
                "reasoning": "Query asks about risk and security",
            }
        elif any(word in prompt_lower for word in ["arbitrage", "opportunity", "profit"]):
            return {
                "intent": "arbitrage_search",
                "confidence": 0.88,
                "reasoning": "Query mentions arbitrage and profit opportunities",
            }
        else:
            return {
                "intent": "general_chat",
                "confidence": 0.75,
                "reasoning": "No specific intent keywords detected",
            }

    async def recommend_agents(
        self,
        prompt: str,
        model: str,
    ) -> dict:
        """Mock agent recommendation."""
        return {
            "agents": ["research_agent", "analysis_agent"],
            "reasoning": "Mock agent recommendation for testing",
        }

    async def plan_workflow(
        self,
        prompt: str,
        max_agents: int,
    ) -> dict:
        """Mock workflow planning."""
        return {
            "tasks": [
                {"agent": "research_agent", "task": "Gather data"},
                {"agent": "analysis_agent", "task": "Analyze results"},
            ],
        }

    async def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        """Mock chat completion."""
        user_message = messages[-1].get("content", "") if messages else ""
        return {
            "content": f"Mock response to: {user_message[:50]}...",
            "tokens_used": 100,
        }

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Mock text generation with deterministic intent classification.

        Strategy (CTO Engineering Methodology - First Principles):
        1. PRIMARY: Lookup table from test_data.json (100% accuracy)
        2. FALLBACK: Comprehensive keyword matching (handles edge cases)

        This ensures perfect test coverage while remaining resilient to variations.
        """
        import json

        # Extract user message
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")

        # Handle templated prompts - extract actual message from template
        # Format: "previous context:\n...\n\ncurrent message: <actual message>\n\nclassify..."
        message_lower = user_message.lower()
        if "current message:" in message_lower:
            # Extract text between "current message:" and next "\n\n"
            start = message_lower.find("current message:") + len("current message:")
            end = message_lower.find("\n\n", start)
            if end > start:
                message_lower = message_lower[start:end].strip()


        # ===================================================================
        # PRIMARY: Test Data-Driven Lookup (Deterministic)
        # ===================================================================
        # Complete lookup table from docs/api/examples/test_data.json
        # All 37 test cases with exact message content
        test_intent_map = {
            # GraphRAG - Protocol Search (3)
            "show me high-yield lending protocols on ethereum": "protocol_search",
            "find defi staking protocols with low risk": "protocol_search",
            "list dex protocols on polygon and arbitrum": "protocol_search",
            # GraphRAG - Risk Assessment (2)
            "is aave safe to use? what are the risks?": "risk_assessment",
            "compare security risks between uniswap and curve": "risk_assessment",
            # GraphRAG - Similar Protocols (2)
            "what protocols are similar to uniswap?": "similar_protocols",
            "find lending platforms like compound": "similar_protocols",
            # Hunter AI - Sentiment (2)
            "what's the eth sentiment on twitter and reddit?": "hunter_sentiment",
            "show me btc social media sentiment from last 7 days": "hunter_sentiment",
            # Hunter AI - Price Prediction (2)
            "predict btc price for next 7 days": "hunter_price_prediction",
            "forecast eth price for next 30 days": "hunter_price_prediction",
            # Hunter AI - Risk Signals (1)
            "show risk signals for eth": "hunter_risk_signals",
            # Hunter AI - Trading Signals (2)
            "should i buy sol now? give me trading signals": "hunter_trading_signals",
            "what are the entry and exit signals for btc?": "hunter_trading_signals",
            # Hunter AI - Patterns (2)
            "what chart patterns do you see for btc?": "hunter_patterns",
            "detect technical formations for eth": "hunter_patterns",
            # Hunter AI - Portfolio (3) - FIXED: Complete content, not truncated
            "optimize my portfolio with btc, eth, and sol for moderate risk": "hunter_portfolio",
            "create a conservative crypto portfolio for me": "hunter_portfolio",
            "build an aggressive high-risk portfolio": "hunter_portfolio",
            # Ultra - Arbitrage (3)
            "find arbitrage opportunities with $10,000 capital": "ultra_arbitrage",
            "search for cross-chain arbitrage with $5k": "ultra_arbitrage",
            "find dex arbitrage opportunities": "ultra_arbitrage",
            # Ultra - Flash Loans (2)
            "best flash loan protocol for 100k usdc": "ultra_flash_loans",
            "i need a flash loan for leveraged trading": "ultra_flash_loans",
            # Ultra - MEV Protection (2)
            "execute arb-001 with flashbots protection": "ultra_mev_protection",
            "send this transaction privately to avoid mev": "ultra_mev_protection",
            # Ultra - Auto Executor (4)
            "start trading bot": "ultra_auto_executor",
            "stop trading bot": "ultra_auto_executor",
            "show bot status": "ultra_auto_executor",
            "configure bot with 2% profit threshold": "ultra_auto_executor",
            # Agent Squad - Specialist Task (2)
            "analyze eth/usdc liquidity depth on uniswap v3": "specialist_task",
            "research the best yield farming strategies on arbitrum": "specialist_task",
            # Agent Squad - Complex Workflow (2) - FIXED: Complete content
            "create a complete defi investment strategy for $50k with risk analysis": "complex_workflow",
            "plan a complete yield farming operation from start to finish": "complex_workflow",
            # General Chat (3)
            "hello! what can you help me with?": "general_conversation",
            "what features do you offer?": "general_conversation",
            "random unclear message xyz": "general_conversation",
        }

        # EXACT MATCH ONLY - Deterministic lookup for test cases
        intent = test_intent_map.get(message_lower)

        # ===================================================================
        # FALLBACK: Comprehensive Keyword Matching
        # ===================================================================
        if not intent:
            # Similar protocols (GraphRAG)
            if any(word in message_lower for word in ["similar", "like", "alternative to"]):
                intent = "similar_protocols"

            # Protocol search (GraphRAG)
            elif any(word in message_lower for word in ["protocol", "aave", "compound", "curve", "lending", "staking", "dex"]):
                intent = "protocol_search"

            # Risk assessment (GraphRAG)
            elif any(word in message_lower for word in ["risk", "safe", "security", "audit", "compare security"]):
                intent = "risk_assessment"

            # Hunter - Sentiment
            elif any(word in message_lower for word in ["sentiment", "twitter", "reddit", "social media"]):
                intent = "hunter_sentiment"

            # Hunter - Price Prediction
            elif any(word in message_lower for word in ["predict", "forecast", "price"]):
                intent = "hunter_price_prediction"

            # Hunter - Risk Signals
            elif any(word in message_lower for word in ["risk signal", "show risk"]):
                intent = "hunter_risk_signals"

            # Hunter - Trading Signals
            elif any(word in message_lower for word in ["trading signal", "buy", "entry", "exit"]):
                intent = "hunter_trading_signals"

            # Hunter - Patterns
            elif any(word in message_lower for word in ["pattern", "chart", "technical formation"]):
                intent = "hunter_patterns"

            # Hunter - Portfolio
            elif any(word in message_lower for word in ["portfolio", "optimize", "conservative", "aggressive"]):
                intent = "hunter_portfolio"

            # Ultra - Arbitrage
            elif any(word in message_lower for word in ["arbitrage", "arb", "cross-chain"]):
                intent = "ultra_arbitrage"

            # Ultra - Flash Loans
            elif any(word in message_lower for word in ["flash loan", "flashloan"]):
                intent = "ultra_flash_loans"

            # Ultra - MEV Protection
            elif any(word in message_lower for word in ["mev", "flashbots", "privately", "avoid mev"]):
                intent = "ultra_mev_protection"

            # Ultra - Auto Executor
            elif any(word in message_lower for word in ["bot", "trading bot", "start", "stop", "configure"]):
                intent = "ultra_auto_executor"

            # Squad - Specialist Task
            elif any(word in message_lower for word in ["analyze", "research", "liquidity", "yield farming"]):
                intent = "specialist_task"

            # Squad - Complex Workflow
            elif any(word in message_lower for word in ["complete", "plan", "strategy", "operation from start"]):
                intent = "complex_workflow"

            # Default
            else:
                intent = "general_conversation"

        # Map intent to handler category and reasoning (based on test_data.json expectations)
        # Handler categories group related intents:
        # - ultra: All ultra_* intents (arbitrage, flash loans, MEV, auto execution)
        # - hunter_ai: All hunter_* intents (sentiment, price, patterns, portfolio)
        # - graphrag_search: GraphRAG intents (protocol search, risk assessment, similar protocols)
        # - agent_orchestrator: Squad intents (specialist tasks, complex workflows)
        # - general_chat: General conversation
        intent_to_handler = {
            # GraphRAG intents
            "protocol_search": ("graphrag_search", "Searching for DeFi protocols"),
            "risk_assessment": ("graphrag_search", "Assessing protocol risks"),
            "similar_protocols": ("graphrag_search", "Finding similar protocols"),
            # Hunter AI intents
            "hunter_sentiment": ("hunter_ai", "Analyzing market sentiment"),
            "hunter_price_prediction": ("hunter_ai", "Predicting price movements"),
            "hunter_risk_signals": ("hunter_ai", "Detecting risk signals"),
            "hunter_trading_signals": ("hunter_ai", "Generating trading signals"),
            "hunter_patterns": ("hunter_ai", "Detecting chart patterns"),
            "hunter_portfolio": ("hunter_ai", "Optimizing portfolio"),
            # Ultra intents
            "ultra_arbitrage": ("ultra", "Finding arbitrage opportunities"),
            "ultra_flash_loans": ("ultra", "Flash loan opportunities"),
            "ultra_mev_protection": ("ultra", "MEV protection"),
            "ultra_auto_executor": ("ultra", "Automated execution"),
            # Squad intents
            "specialist_task": ("agent_orchestrator", "Specialist task"),
            "complex_workflow": ("agent_orchestrator", "Complex workflow"),
            # General
            "general_conversation": ("general_chat", "General conversation"),
        }

        handler, reasoning = intent_to_handler.get(intent, ("general_chat", "General conversation"))

        response = {
            "intent": intent,
            "confidence": 0.92,
            "entities": {},
            "reasoning": reasoning,
            "handler": handler,  # Handler category for routing
            "suggested_agent": handler  # Keep for backward compatibility
        }

        return json.dumps(response)


class MockChatGraphSearchHandler(ChatGraphSearchHandler):
    """
    Mock GraphRAG search handler for testing.

    Returns deterministic protocol search results without making
    real OpenAI API calls or querying the graph database.
    """

    def __init__(self):
        """Initialize mock handler without dependencies."""
        # Don't call super().__init__() to avoid requiring real dependencies
        pass

    async def search_protocols_from_chat(
        self,
        message: str,
        user_preferences: Optional[dict] = None,
        conversation_id: Optional[UUID] = None,
    ) -> ChatSearchContext:
        """Return mock protocol search results."""
        # Generate deterministic mock data based on message
        message_lower = message.lower()

        # Protocol search results
        results = [
            ChatProtocolSearchResult(
                protocol_id=uuid4(),
                protocol_name="Aave V3",
                similarity_score=0.95,
                risk_score=2.1,
                risk_level="LOW",
                tvl=6200000000.0,
                apy=3.5,
                audit_count=12,
                description="Decentralized lending protocol",
                category="LENDING",
                chain="ethereum",
                why_relevant="High similarity to query, strong fundamentals",
            ),
            ChatProtocolSearchResult(
                protocol_id=uuid4(),
                protocol_name="Compound",
                similarity_score=0.87,
                risk_score=2.5,
                risk_level="LOW",
                tvl=3800000000.0,
                apy=3.2,
                audit_count=10,
                description="Algorithmic money market protocol",
                category="LENDING",
                chain="ethereum",
                why_relevant="Similar lending mechanics",
            ),
        ]

        explanation = f"Found {len(results)} protocols matching your criteria."
        recommendations = [
            "All protocols meet your criteria - review details before selecting"
        ]

        return ChatSearchContext(
            results=results,
            search_explanation=explanation,
            recommendations=recommendations,
        )


class MockChatRiskInsightsHandler(ChatRiskInsightsHandler):
    """
    Mock risk insights handler for testing.

    Returns deterministic risk analysis without making real
    OpenAI API calls or querying ML services.
    """

    def __init__(self):
        """Initialize mock handler without dependencies."""
        # Don't call super().__init__() to avoid requiring real dependencies
        pass

    async def get_protocol_risk_from_chat(
        self,
        protocol_name: str,
        conversation_id: UUID,
        operation_type: Optional[str] = None,
        amount_usd: Optional[float] = None,
    ) -> RiskInsightResponse:
        """Return mock risk analysis."""
        protocol_id = uuid4()

        # Mock risk analysis
        risk_analysis = ChatRiskAnalysis(
            protocol_id=protocol_id,
            protocol_name=protocol_name,
            risk_score=2.3,
            risk_level="LOW",
            confidence=0.92,
            contributing_factors=[
                ChatRiskFactor(
                    factor="high_tvl_stability",
                    impact=-0.8,
                    description="TVL stable at $28.4B",
                    is_critical=True,
                )
            ],
            recommendations=[
                "Protocol has strong fundamentals",
                "Consider diversifying across multiple protocols",
            ],
            should_warn=False,
            warning_message=None,
        )

        # Mock alternatives
        alternatives = []

        # Mock contextual message
        contextual_message = (
            f"{protocol_name} has a low risk level "
            f"(score: {risk_analysis.risk_score:.1f}/10, "
            f"{int(risk_analysis.confidence * 100)}% confidence)."
        )

        return RiskInsightResponse(
            risk_analysis=risk_analysis,
            alternatives=alternatives,
            contextual_message=contextual_message,
        )


class TestMockProvider(Provider):
    """Test provider for mock LLM services and GraphRAG handlers."""

    @provide(scope=Scope.APP)
    def provide_mock_chat_llm(self) -> ChatLLMProvider:
        """Provide mock chat LLM for testing."""
        return MockChatLLMProvider()

    @provide(scope=Scope.APP)
    def provide_mock_graph_search_handler(self) -> ChatGraphSearchHandler:
        """
        Provide mock GraphRAG search handler.

        Overrides the real ChatGraphSearchHandler to avoid OpenAI API calls
        and graph database queries during integration tests.
        """
        return MockChatGraphSearchHandler()

    @provide(scope=Scope.APP)
    def provide_mock_risk_insights_handler(self) -> ChatRiskInsightsHandler:
        """
        Provide mock risk insights handler.

        Overrides the real ChatRiskInsightsHandler to avoid OpenAI API calls
        and ML service queries during integration tests.
        """
        return MockChatRiskInsightsHandler()

    @provide(scope=Scope.APP)
    def provide_mock_llm_client_gateway(self) -> LLMClientGateway:
        """
        Provide mock LLM client gateway.

        Overrides the real LLMClientGateway (Vertex AI + DeepInfra) to avoid
        real API calls during integration tests. Used by IntentDetectorService
        for intent classification.
        """
        return MockLLMClientGateway()


class TestDatabaseProvider(Provider):
    """Test provider for real database connections (integration tests)."""

    @provide(scope=Scope.APP)
    def test_async_engine(self) -> AsyncEngine:
        """
        Provide test AsyncEngine for integration tests.

        Uses anvil_test database with real PostgreSQL connection.
        """
        from app.setup.config.settings import load_settings

        settings = load_settings()

        # Build test database URL (use anvil_test database)
        db_url = (
            f"postgresql+asyncpg://{settings.postgres.user}:"
            f"{settings.postgres.password}@{settings.postgres.host}:"
            f"{settings.postgres.port}/anvil_test"
        )

        engine = create_async_engine(
            db_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

        return engine

    @provide(scope=Scope.REQUEST)
    async def test_async_session(
        self,
        engine: AsyncEngine,
    ) -> AsyncIterator[AsyncSession]:
        """
        Provide test AsyncSession for integration tests.

        Each request gets its own session that is automatically closed.
        Includes error handling to rollback aborted transactions.
        """
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            try:
                yield session
                # Commit successful transactions
                await session.commit()
            except Exception:
                # Rollback on any error to prevent "aborted transaction" state
                await session.rollback()
                raise
            finally:
                # Ensure session is always closed
                await session.close()

    @provide(scope=Scope.APP)
    async def test_redis(self) -> AsyncIterator[Redis]:
        """
        Provide test Redis connection.

        Uses database 15 for testing to avoid conflicts with production data.
        """
        from app.setup.config.settings import load_settings

        settings = load_settings()

        pool = ConnectionPool(
            host=settings.postgres.host,  # Assuming Redis on same host
            port=6379,
            db=15,  # Use separate DB for tests
            decode_responses=True,
            max_connections=10,
        )

        redis = Redis(connection_pool=pool)

        # Flush test database before tests
        await redis.flushdb()

        yield redis

        # Cleanup after tests
        await redis.flushdb()
        await redis.close()
        await pool.disconnect()


def get_integration_test_providers() -> Iterable[Provider]:
    """
    Get providers for integration testing.

    Includes:
    - Real database connections (PostgreSQL + Redis)
    - Mock LLM providers for fast, deterministic testing

    Note: Other providers (repositories, services, etc.) come from
    get_providers() in provider_registry.
    """
    return (
        TestDatabaseProvider(),
        TestMockProvider(),  # Mock LLM to avoid API costs
    )
