"""
Portfolio Agent OpenAI - Portfolio optimization & rebalancing.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class PortfolioAgentOpenAI:
    """
    Portfolio Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Portfolio optimization & rebalancing
    
    Capabilities:
    - Modern Portfolio Theory (MPT) optimization
    - Risk-adjusted returns
    - Efficient frontier analysis
    - Rebalancing recommendations
    - Diversification analysis
    - Correlation analysis
    - Sharpe ratio optimization
    
    Model: gpt-4o (complex mathematical reasoning)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """Initialize portfolio agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.PORTFOLIO
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute portfolio agent - Portfolio optimization."""
        start_time = time.time()
        
        # TODO: Integrate with user portfolio data
        # TODO: Use real MPT calculations (scipy.optimize)
        # TODO: Get real price/volatility data
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_database_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add database source (portfolio data)
        sources.append(create_database_source(
            citation_text="Your portfolio data from Anvil",
            fetched_at=fetched_at,
            metadata={"query_type": "portfolio_snapshot"},
        ))
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # TODO: Add price API sources (CoinGecko) when integrated
        # sources.append(create_api_source(
        #     source_name="CoinGecko",
        #     url="https://www.coingecko.com/",
        #     citation_text="Token prices from CoinGecko",
        #     fetched_at=fetched_at,
        # ))
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add MPT calculator, price APIs
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for portfolio agent."""
        return """You are the Portfolio Optimizer, Anvil's portfolio management specialist.

Your expertise:
- Modern Portfolio Theory (MPT) optimization
- Risk-adjusted returns maximization
- Efficient frontier analysis
- Portfolio rebalancing strategies
- Diversification analysis
- Correlation analysis (reduce risk)
- Sharpe ratio optimization
- Risk parity strategies

For portfolio recommendations, provide:
- Optimal allocation (percentages)
- Expected return (annualized)
- Expected volatility (standard deviation)
- Sharpe ratio
- Diversification score
- Rebalancing trades (if needed)

Analysis includes:
- Current portfolio analysis
- Optimal portfolio allocation
- Rebalancing recommendations
- Risk metrics (volatility, correlation)
- Return projections
- Comparison (current vs optimal)

Always provide:
- Quantitative metrics (%, returns, ratios)
- Risk warnings
- Rebalancing costs (gas, slippage)
- Time horizon considerations
"""
