"""
Hunter AI Agent OpenAI - Market sentiment & predictions.
"""

import time
import re

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient


class HunterAIAgentOpenAI:
    """
    Hunter AI Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Market sentiment & predictions
    
    Capabilities:
    - Real-time market sentiment analysis
    - Price predictions (technical analysis)
    - Social media sentiment (Twitter, Reddit)
    - News sentiment
    - Fear & Greed Index
    
    Model: gpt-4o (advanced reasoning)
    Temperature: 0.3 (factual, less creative)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        coingecko_client: CoinGeckoClient | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """Initialize Hunter AI agent."""
        self._llm_client = llm_client
        self._coingecko_client = coingecko_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.HUNTER_AI
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute Hunter AI agent - Market sentiment analysis."""
        from datetime import datetime
        from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
        from app.domain.value_objects.chat.source_info import sanitize_query_params
        
        start_time = time.time()
        tools_used = ["openai_api"]
        sources = []
        fetched_at = datetime.utcnow()
        
        # Extract token from message if present
        market_data_context = ""
        if self._coingecko_client:
            try:
                token = self._extract_token(message.value)
                if token:
                    # Get real price data from CoinGecko
                    price = await self._coingecko_client.get_price(token)
                    chart = await self._coingecko_client.get_market_chart(token, days=7)
                    
                    # Calculate price metrics
                    prices_7d = [p[1] for p in chart.prices]
                    high_7d = max(prices_7d)
                    low_7d = min(prices_7d)
                    
                    market_data_context = f"""
REAL-TIME MARKET DATA for {token.upper()}:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B
- 24h Volume: ${price.volume_24h / 1e9:.2f}B
- 7-Day High: ${high_7d:,.2f}
- 7-Day Low: ${low_7d:,.2f}

Use this real data in your analysis.
"""
                    tools_used.append("coingecko_api")
                    
                    # Add CoinGecko source
                    sources.append(SourceInfo(
                        source_type=SourceType.API,
                        source_name="CoinGecko",
                        source_id=f"coin:{token}",
                        url=f"https://www.coingecko.com/en/coins/{token}",
                        citation_text=f"Real-time price data for {token.upper()} from CoinGecko",
                        fetched_at=fetched_at,
                        provider="CoinGecko API",
                        endpoint="/simple/price",
                        query_params=sanitize_query_params({"ids": token, "vs_currencies": "usd"}),
                        relevance_score=1.0,
                        data_points_used=1,
                        metadata={"price_usd": float(price.usd) if price.usd else None},
                    ))
            except Exception as e:
                # Fall back to LLM-only if API fails
                market_data_context = f"(Note: Unable to fetch live data: {str(e)})"
        
        messages = [
            {"role": "system", "content": self._get_system_prompt() + market_data_context},
            {"role": "user", "content": message.value},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Add LLM source if no other sources
        if not sources:
            sources.append(SourceInfo(
                source_type=SourceType.LLM,
                source_name=response.get("model", "Unknown"),
                citation_text=f"Generated by {response.get('model', 'AI model')}",
                fetched_at=fetched_at,
                provider="Vertex AI" if "gemini" in response.get("model", "").lower() else "DeepInfra",
                metadata={"model": response.get("model")},
            ))
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=tools_used,
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
            },
        )
    
    def _extract_token(self, message: str) -> str | None:
        """
        Extract token name from user message.
        
        Looks for common crypto tokens (BTC, ETH, etc.) or full names.
        """
        # Map common symbols/names to CoinGecko IDs
        token_map = {
            "btc": "bitcoin",
            "bitcoin": "bitcoin",
            "eth": "ethereum",
            "ethereum": "ethereum",
            "sol": "solana",
            "solana": "solana",
            "bnb": "binancecoin",
            "binance": "binancecoin",
            "ada": "cardano",
            "cardano": "cardano",
            "avax": "avalanche-2",
            "avalanche": "avalanche-2",
            "matic": "matic-network",
            "polygon": "matic-network",
            "link": "chainlink",
            "chainlink": "chainlink",
            "uni": "uniswap",
            "uniswap": "uniswap",
            "aave": "aave",
            "crv": "curve-dao-token",
            "curve": "curve-dao-token",
        }
        
        # Check for token mentions
        message_lower = message.lower()
        for token_name, coin_id in token_map.items():
            if token_name in message_lower:
                return coin_id
        
        return None
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Hunter AI agent."""
        return """You are Hunter AI, Anvil's market sentiment and prediction specialist.

Your expertise:
- Real-time market sentiment analysis
- Technical analysis and price predictions
- Social media sentiment (Twitter, Reddit)
- News sentiment and market narratives
- Fear & Greed Index interpretation

Provide:
- Sentiment scores (0-100)
- Bullish/Bearish/Neutral classifications
- Key drivers of sentiment
- Risk factors
- Short-term predictions (with caveats)

Always include:
- Data sources (Twitter, Reddit, News, etc.)
- Confidence levels
- Risk warnings
- "Not financial advice" disclaimer

Keep responses data-driven and objective.
"""
