"""
Hunter AI Agent - Market sentiment & predictions.
"""

import time
import re

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient


class HunterAIAgent:
    """
    Hunter AI Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Market sentiment & predictions
    
    Capabilities:
    - Real-time market sentiment analysis
    - Price predictions (technical analysis)
    - Social media sentiment (Twitter, Reddit)
    - News sentiment
    - Fear & Greed Index
    
    Model: gemini-2.0-flash (Vertex AI, advanced reasoning)
    Temperature: 0.3 (factual, less creative)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed)
        coingecko_client: CoinGeckoClient | None = None,
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
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
        from datetime import datetime, UTC
        from app.domain.value_objects.chat.source_info import SourceInfo, SourceType
        from app.domain.value_objects.chat.source_info import sanitize_query_params
        
        start_time = time.time()
        tools_used = ["openai_api"]
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Extract tokens from message if present (supports multiple tokens)
        market_data_context = ""
        import logging
        logger = logging.getLogger(__name__)
        
        if self._coingecko_client:
            logger.info(f"✅ CoinGecko client available for Hunter AI")
            try:
                tokens = self._extract_tokens(message.value)
                logger.info(f"🔍 Extracted tokens from message '{message.value[:50]}...': {tokens}")
                
                # If query mentions "prices" or "best prices" but no specific tokens,
                # fetch common tokens for context
                if not tokens and any(phrase in message.value.lower() for phrase in ["price", "prices", "best price", "current price", "swap"]):
                    tokens = ["bitcoin", "ethereum", "usd-coin"]  # Common tokens for price context
                    logger.info(f"📊 No specific tokens found, fetching common tokens for price context: {tokens}")
                
                if tokens:
                    # Fetch prices for all tokens
                    price_data_parts = []
                    
                    # Use bulk price API if multiple tokens
                    if len(tokens) > 1:
                        prices = await self._coingecko_client.get_prices_bulk(tokens)
                        for token_id, price in prices.items():
                            if price:
                                price_data_parts.append(f"""
{token_id.upper()}:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B
- 24h Volume: ${price.volume_24h / 1e9:.2f}B""")
                                
                                # Add CoinGecko source for each token
                                sources.append(SourceInfo(
                                    source_type=SourceType.API,
                                    source_name="CoinGecko",
                                    source_id=f"coin:{token_id}",
                                    url=f"https://www.coingecko.com/en/coins/{token_id}",
                                    citation_text=f"Real-time price data for {token_id.upper()} from CoinGecko",
                                    fetched_at=fetched_at,
                                    provider="CoinGecko API",
                                    endpoint="/simple/price",
                                    query_params=sanitize_query_params({"ids": token_id, "vs_currencies": "usd"}),
                                    relevance_score=1.0,
                                    data_points_used=1,
                                    metadata={"price_usd": float(price.usd) if price.usd else None},
                                ))
                    else:
                        # Single token - get detailed data with chart
                        token = tokens[0]
                        price = await self._coingecko_client.get_price(token)
                        chart = await self._coingecko_client.get_market_chart(token, days=7)
                        
                        # Calculate price metrics
                        prices_7d = [p[1] for p in chart.prices]
                        high_7d = max(prices_7d)
                        low_7d = min(prices_7d)
                        
                        price_data_parts.append(f"""
{token.upper()}:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B
- 24h Volume: ${price.volume_24h / 1e9:.2f}B
- 7-Day High: ${high_7d:,.2f}
- 7-Day Low: ${low_7d:,.2f}""")
                        
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
                    
                    if price_data_parts:
                        market_data_context = f"""
REAL-TIME MARKET DATA (FROM COINGECKO API - USE THESE EXACT PRICES):
{''.join(price_data_parts)}

CRITICAL: You MUST use the EXACT prices shown above. Do NOT estimate, guess, or use outdated prices.
- If BTC price is shown as $X, report it as $X (not a different value)
- If ETH price is shown as $Y, report it as $Y (not a different value)
- These are real-time prices from CoinGecko API - they are accurate and current
- Format prices with commas for thousands (e.g., $92,619 not $92619)
"""
                        tools_used.append("coingecko_api")
                        
            except Exception as e:
                # Fall back to LLM-only if API fails
                logger.error(f"❌ CoinGecko API error: {str(e)}", exc_info=True)
                market_data_context = f"(Note: Unable to fetch live data: {str(e)})"
        else:
            logger.warning(f"⚠️ CoinGecko client not available - Hunter AI will use LLM-only mode")
        
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
    
    def _extract_tokens(self, message: str) -> list[str]:
        """
        Extract token names from user message (supports multiple tokens).
        
        Returns list of CoinGecko coin IDs found in the message.
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
            "usdc": "usd-coin",
            "usdt": "tether",
            "dai": "dai",
            "wbtc": "wrapped-bitcoin",
        }
        
        # Check for token mentions
        message_lower = message.lower()
        found_tokens = []
        seen_ids = set()
        
        for token_name, coin_id in token_map.items():
            if token_name in message_lower and coin_id not in seen_ids:
                found_tokens.append(coin_id)
                seen_ids.add(coin_id)
        
        # If no specific tokens found but query mentions "prices" or "best prices",
        # fetch common tokens (BTC, ETH, USDC) for context
        if not found_tokens and any(phrase in message_lower for phrase in ["price", "prices", "best price", "current price"]):
            # Return common tokens for price context
            return ["bitcoin", "ethereum", "usd-coin"]
        
        return found_tokens
    
    def _extract_token(self, message: str) -> str | None:
        """
        Extract single token name from user message (backward compatibility).
        
        Returns first token found, or None.
        """
        tokens = self._extract_tokens(message)
        return tokens[0] if tokens else None
    
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

CRITICAL PRICE ACCURACY RULES:
- When REAL-TIME MARKET DATA is provided, you MUST use those EXACT prices
- Never estimate, guess, or use outdated prices when real data is available
- Format prices with commas: $92,619 (not $92619)
- If asked about prices, quote the exact values from the REAL-TIME MARKET DATA section
- Do NOT make up prices or use prices from your training data

**CRITICAL: ANVIL IS REAL, NOT SIMULATED**
- Anvil is a REAL, LIVE DeFi platform - NOT simulated or hypothetical
- DO NOT use words like "simulated", "simulation", "mock", or "hypothetical" when describing Anvil
- Anvil provides REAL swaps, REAL prices, REAL lending rates
- Use language like "On Anvil", "Anvil provides", "Anvil's platform"
- NEVER say "Simulated DeFi Environment" or "simulated Anvil"

Provide:
- Sentiment scores (0-100)
- Bullish/Bearish/Neutral classifications
- Key drivers of sentiment
- Risk factors
- Short-term predictions (with caveats)

**CRITICAL: PROVIDE SPECIFIC PRICES**
- When asked about prices, ALWAYS provide SPECIFIC current prices from CoinGecko data
- DO NOT say "need real-time data" - you have CoinGecko API access
- Format prices clearly: "$92,619" not "$92619"
- Include 24h change percentages
- If prices are provided in context, USE THEM EXACTLY

Always include:
- Data sources (Twitter, Reddit, News, etc.)
- Confidence levels
- Risk warnings
- "Not financial advice" disclaimer

Keep responses data-driven and objective.
"""
