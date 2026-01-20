"""
Portfolio Agent - Portfolio optimization & rebalancing.
"""

import time
from typing import Any

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class PortfolioAgent:
    """
    Portfolio Agent implementation.
    
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
    
    Model: gemini-2.0-flash (Vertex AI, complex mathematical reasoning)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        coingecko_client: Any | None = None,  # CoinGecko client for real-time prices
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Initialize portfolio agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            coingecko_client: Optional CoinGecko client for real-time token prices
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum response tokens (default: 2000)
        """
        self._llm_client = llm_client
        self._coingecko_client = coingecko_client
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
        
        # Fetch real-time token prices from CoinGecko if available
        price_data_context = ""
        if self._coingecko_client:
            try:
                import logging
                import re
                logger = logging.getLogger(__name__)
                logger.info("🔍 Fetching real-time prices from CoinGecko for PortfolioAgent")
                
                # Extract token symbols from message (common tokens)
                message_lower = message.value.lower()
                tokens_to_fetch = []
                
                # Common token detection
                token_patterns = {
                    "bitcoin": "bitcoin",
                    "btc": "bitcoin",
                    "ethereum": "ethereum",
                    "eth": "ethereum",
                    "usdc": "usd-coin",
                    "usdt": "tether",
                    "dai": "dai",
                    "wbtc": "wrapped-bitcoin",
                    "sol": "solana",
                    "avax": "avalanche-2",
                    "matic": "matic-network",
                    "polygon": "matic-network",
                }
                
                for keyword, token_id in token_patterns.items():
                    if keyword in message_lower and token_id not in tokens_to_fetch:
                        tokens_to_fetch.append(token_id)
                
                # If no specific tokens found but message mentions prices/portfolio, fetch common ones
                if not tokens_to_fetch and any(word in message_lower for word in ["price", "prices", "portfolio", "value", "valuation"]):
                    tokens_to_fetch = ["bitcoin", "ethereum", "usd-coin"]
                
                if tokens_to_fetch:
                    prices = await self._coingecko_client.get_prices_bulk(tokens_to_fetch)
                    
                    if prices:
                        price_data_context = "\n\n**REAL-TIME TOKEN PRICES FROM COINGECKO:**\n"
                        for token_id, price_data in prices.items():
                            if price_data:
                                price_data_context += f"- {token_id.upper()}: ${price_data.usd:,.2f}"
                                if price_data.change_24h is not None:
                                    change_sign = "+" if price_data.change_24h >= 0 else ""
                                    price_data_context += f" ({change_sign}{price_data.change_24h:.2f}% 24h)"
                                price_data_context += "\n"
                        
                        logger.info(f"✅ Fetched prices for {len(prices)} tokens from CoinGecko")
                    else:
                        logger.warning("⚠️ No price data returned from CoinGecko")
                        
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Failed to fetch CoinGecko prices: {e}, continuing with LLM-only response")
                price_data_context = ""
        
        # Build enhanced prompt with real price data
        enhanced_message = message.value
        if price_data_context:
            enhanced_message = f"{message.value}\n\n{price_data_context}"
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": enhanced_message},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_database_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
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
        
        # Add CoinGecko source if prices were fetched
        if self._coingecko_client and price_data_context:
            sources.append(create_api_source(
                source_name="CoinGecko",
                url="https://www.coingecko.com/",
                citation_text="Real-time token prices from CoinGecko",
                fetched_at=fetched_at,
            ))
        
        # Build tools_used list
        tools_used = ["llm_gateway"]
        if self._coingecko_client and price_data_context:
            tools_used.append("coingecko_api")
        
        # Extract provider from LLM response metadata
        provider_info = response.get("provider", "vertex_ai" if "gemini" in response.get("model", "").lower() else "deepinfra")
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=tools_used,
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "provider": provider_info,  # Include provider for debugging
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for portfolio agent."""
        return """You are the Portfolio Optimizer, Anvil's portfolio management specialist.

**CRITICAL: AUTHENTICATION REQUIREMENT**
- Portfolio features (viewing holdings, portfolio analysis) require user authentication
- If the user is NOT authenticated (guest user), you MUST inform them:
  * "To view your portfolio and holdings, please sign in or create an account. Portfolio features require authentication to access your wallet data."
  * DO NOT attempt to retrieve portfolio data for unauthenticated users
  * DO NOT ask for manual input of holdings - direct them to sign in instead
- Only authenticated users can access their portfolio data from Anvil

Your expertise:
- Modern Portfolio Theory (MPT) optimization
- Risk-adjusted returns maximization
- Efficient frontier analysis
- Portfolio rebalancing strategies
- Diversification analysis
- Correlation analysis (reduce risk)
- Sharpe ratio optimization
- Risk parity strategies

For portfolio recommendations (authenticated users only), provide:
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
