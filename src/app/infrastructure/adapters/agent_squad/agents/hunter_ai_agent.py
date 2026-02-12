"""
Hunter AI Agent - Market sentiment & predictions.
"""

import time
import re
import logging
from typing import TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
)
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient
from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


class HunterAIAgent:
    """
    Hunter AI Agent implementation.

    Implements: AgentGateway

    Purpose: Market sentiment & predictions + Swap quotes

    Capabilities:
    - Real-time market sentiment analysis
    - Price predictions (technical analysis)
    - Social media sentiment (Twitter, Reddit)
    - News sentiment
    - Fear & Greed Index
    - **Spot swap quotes via Hyperliquid**

    Model: gemini-2.0-flash (Vertex AI, advanced reasoning)
    Temperature: 0.3 (factual, less creative)
    """

    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed)
        coingecko_client: CoinGeckoClient | None = None,
        hyperliquid_client: HyperliquidClient | None = None,
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """Initialize Hunter AI agent."""
        self._llm_client = llm_client
        self._coingecko_client = coingecko_client
        self._hyperliquid_client = hyperliquid_client
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
        swap_quote_context = ""

        # ========================================
        # SWAP RATE QUERIES - Hyperliquid Spot
        # ========================================
        message_lower = message.value.lower()
        is_swap_query = any(
            phrase in message_lower
            for phrase in [
                "swap rate",
                "best rate",
                "exchange rate",
                "convert",
                "swap",
                "trade",
                "best swap",
                "best price for",
                "eth to usdc",
                "btc to usdc",
                "usdc to eth",
            ]
        ) and any(tok in message_lower for tok in ["eth", "btc", "usdc", "usdt"])

        # Log whether Hyperliquid client is available
        logger.info(
            f"🔄 Swap query check: is_swap_query={is_swap_query}, hyperliquid_client={self._hyperliquid_client is not None}"
        )

        if is_swap_query and self._hyperliquid_client:
            logger.info(f"🔄 Detected swap rate query: {message.value[:50]}...")
            try:
                # Extract token pair from message
                swap_pair = self._extract_swap_pair(message.value)
                if swap_pair:
                    from_token, to_token, amount = swap_pair
                    logger.info(
                        f"📊 Fetching Hyperliquid spot quote: {amount} {from_token} → {to_token}"
                    )

                    quote = await self._hyperliquid_client.get_spot_quote(
                        from_token=from_token,
                        to_token=to_token,
                        amount=amount,
                    )

                    swap_quote_context = f"""
REAL-TIME SWAP QUOTE (FROM HYPERLIQUID SPOT - USE THESE EXACT VALUES):

**Swap: {quote.from_amount} {quote.from_token} → {quote.to_token}**
- You receive: {quote.to_amount:,.4f} {quote.to_token}
- Effective rate: 1 {quote.from_token} = {quote.price:,.2f} {quote.to_token}
- Mid-market price: {quote.mid_price:,.2f}
- Spread: {quote.spread_bps:.2f} bps

CRITICAL: Use these EXACT values from Hyperliquid. This is a real-time quote.
- Hyperliquid offers zero gas fees and high-speed execution
- Quote valid for ~30 seconds
"""
                    tools_used.append("hyperliquid_spot")

                    # Add Hyperliquid source
                    sources.append(
                        SourceInfo(
                            source_type=SourceType.API,
                            source_name="Hyperliquid",
                            source_id=f"spot:{from_token}-{to_token}",
                            url="https://app.hyperliquid.xyz/trade",
                            citation_text=f"Real-time spot swap quote from Hyperliquid",
                            fetched_at=fetched_at,
                            provider="Hyperliquid API",
                            endpoint="/info",
                            query_params={"type": "l2Book"},
                            relevance_score=1.0,
                            data_points_used=1,
                            metadata={
                                "from_token": from_token,
                                "to_token": to_token,
                                "amount": amount,
                                "output": quote.to_amount,
                                "rate": quote.price,
                            },
                        )
                    )

            except Exception as e:
                logger.warning(f"⚠️ Hyperliquid spot quote error: {e}")
                # Hyperliquid doesn't have this market - calculate from CoinGecko prices
                swap_quote_context = ""  # Will be calculated below from CoinGecko

        if self._coingecko_client:
            logger.info(f"✅ CoinGecko client available for Hunter AI")
            try:
                tokens = self._extract_tokens(message.value)
                logger.info(
                    f"🔍 Extracted tokens from message '{message.value[:50]}...': {tokens}"
                )

                # If query mentions "prices" or "best prices" but no specific tokens,
                # fetch common tokens for context
                if not tokens and any(
                    phrase in message.value.lower()
                    for phrase in [
                        "price",
                        "prices",
                        "best price",
                        "current price",
                        "swap",
                    ]
                ):
                    tokens = [
                        "bitcoin",
                        "ethereum",
                        "usd-coin",
                    ]  # Common tokens for price context
                    logger.info(
                        f"📊 No specific tokens found, fetching common tokens for price context: {tokens}"
                    )

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
                                sources.append(
                                    SourceInfo(
                                        source_type=SourceType.API,
                                        source_name="CoinGecko",
                                        source_id=f"coin:{token_id}",
                                        url=f"https://www.coingecko.com/en/coins/{token_id}",
                                        citation_text=f"Real-time price data for {token_id.upper()} from CoinGecko",
                                        fetched_at=fetched_at,
                                        provider="CoinGecko API",
                                        endpoint="/simple/price",
                                        query_params=sanitize_query_params({
                                            "ids": token_id,
                                            "vs_currencies": "usd",
                                        }),
                                        relevance_score=1.0,
                                        data_points_used=1,
                                        metadata={
                                            "price_usd": float(price.usd)
                                            if price.usd
                                            else None
                                        },
                                    )
                                )
                    else:
                        # Single token - get detailed data with chart
                        token = tokens[0]
                        price = await self._coingecko_client.get_price(token)
                        chart = await self._coingecko_client.get_market_chart(
                            token, days=7
                        )

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
                        sources.append(
                            SourceInfo(
                                source_type=SourceType.API,
                                source_name="CoinGecko",
                                source_id=f"coin:{token}",
                                url=f"https://www.coingecko.com/en/coins/{token}",
                                citation_text=f"Real-time price data for {token.upper()} from CoinGecko",
                                fetched_at=fetched_at,
                                provider="CoinGecko API",
                                endpoint="/simple/price",
                                query_params=sanitize_query_params({
                                    "ids": token,
                                    "vs_currencies": "usd",
                                }),
                                relevance_score=1.0,
                                data_points_used=1,
                                metadata={
                                    "price_usd": float(price.usd) if price.usd else None
                                },
                            )
                        )

                    if price_data_parts:
                        market_data_context = f"""
REAL-TIME MARKET DATA (FROM COINGECKO API - USE THESE EXACT PRICES):
{"".join(price_data_parts)}

CRITICAL: You MUST use the EXACT prices shown above. Do NOT estimate, guess, or use outdated prices.
- If BTC price is shown as $X, report it as $X (not a different value)
- If ETH price is shown as $Y, report it as $Y (not a different value)
- These are real-time prices from CoinGecko API - they are accurate and current
- Format prices with commas for thousands (e.g., $92,619 not $92619)
"""
                        tools_used.append("coingecko_api")

                        # Calculate swap rate if this is a swap query and we have prices for both tokens
                        if (
                            is_swap_query
                            and not swap_quote_context
                            and len(tokens) >= 2
                        ):
                            try:
                                prices_dict = (
                                    await self._coingecko_client.get_prices_bulk(tokens)
                                )
                                swap_pair = self._extract_swap_pair(message.value)
                                if swap_pair:
                                    from_token, to_token, amount = swap_pair
                                    # Map token symbols to CoinGecko IDs
                                    token_to_coingecko = {
                                        "ETH": "ethereum",
                                        "BTC": "bitcoin",
                                        "USDC": "usd-coin",
                                        "USDT": "tether",
                                        "SOL": "solana",
                                        "MATIC": "matic-network",
                                    }
                                    from_id = token_to_coingecko.get(
                                        from_token.upper(), from_token.lower()
                                    )
                                    to_id = token_to_coingecko.get(
                                        to_token.upper(), to_token.lower()
                                    )

                                    from_price = prices_dict.get(from_id)
                                    to_price = prices_dict.get(to_id)

                                    if (
                                        from_price
                                        and to_price
                                        and from_price.usd
                                        and to_price.usd
                                    ):
                                        swap_rate = from_price.usd / to_price.usd
                                        output_amount = amount * swap_rate

                                        swap_quote_context = f"""
CALCULATED SWAP RATE (FROM COINGECKO PRICES):

**Swap: {amount} {from_token} → {to_token}**
- {from_token} Price: ${from_price.usd:,.2f}
- {to_token} Price: ${to_price.usd:,.2f}
- **Swap Rate: 1 {from_token} = {swap_rate:,.4f} {to_token}**
- **You would receive: ~{output_amount:,.4f} {to_token}**

Note: This is a market rate calculation. Actual swap rates on DEXs may vary slightly due to:
- Liquidity depth and slippage
- DEX fees (typically 0.3% on Uniswap, varies by protocol)
- Gas costs

On Anvil, you can execute swaps through multiple DEX aggregators including 1inch, Hyperliquid, and UniswapX to get the best rate.
"""
                                        logger.info(
                                            f"📊 Calculated swap rate from CoinGecko: {amount} {from_token} = {output_amount:.4f} {to_token}"
                                        )
                            except Exception as calc_error:
                                logger.warning(
                                    f"Could not calculate swap rate: {calc_error}"
                                )

            except Exception as e:
                # Fall back to LLM-only if API fails
                logger.error(f"❌ CoinGecko API error: {str(e)}", exc_info=True)
                market_data_context = f"(Note: Unable to fetch live data: {str(e)})"
        else:
            logger.warning(
                f"⚠️ CoinGecko client not available - Hunter AI will use LLM-only mode"
            )

        # Combine all context
        full_context = ""
        if swap_quote_context:
            full_context += swap_quote_context + "\n\n"
        if market_data_context:
            full_context += market_data_context

        messages = [
            {"role": "system", "content": self._get_system_prompt() + full_context},
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
            sources.append(
                SourceInfo(
                    source_type=SourceType.LLM,
                    source_name=response.get("model", "Unknown"),
                    citation_text=f"Generated by {response.get('model', 'AI model')}",
                    fetched_at=fetched_at,
                    provider="Vertex AI"
                    if "gemini" in response.get("model", "").lower()
                    else "DeepInfra",
                    metadata={"model": response.get("model")},
                )
            )

        # Extract provider from LLM response metadata
        provider_info = response.get(
            "provider",
            "vertex_ai"
            if "gemini" in response.get("model", "").lower()
            else "deepinfra",
        )

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
            # Major tokens
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
            # Tokens on Hyperliquid Spot
            "pepe": "pepe",
            "trump": "official-trump",
            "maga": "maga",
            "doge": "dogecoin",
            "dogecoin": "dogecoin",
            "shib": "shiba-inu",
            "shiba": "shiba-inu",
            "bonk": "bonk",
            "floki": "floki",
            "wif": "dogwifcoin",
            "dogwifhat": "dogwifcoin",
            "mog": "mog-coin",
            "brett": "brett",
            "neiro": "neiro-on-eth",
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
        if not found_tokens and any(
            phrase in message_lower
            for phrase in ["price", "prices", "best price", "current price"]
        ):
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

    def _extract_swap_pair(self, message: str) -> tuple[str, str, float] | None:
        """
        Extract swap pair and amount from message.

        Returns:
            Tuple of (from_token, to_token, amount) or None if not found

        Examples:
            "swap 1 ETH to USDC" → ("ETH", "USDC", 1.0)
            "best rate for ETH to USDC" → ("ETH", "USDC", 1.0)
            "convert 100 USDC to ETH" → ("USDC", "ETH", 100.0)
        """
        message_lower = message.lower()

        # Token symbol mapping for Hyperliquid spot
        token_map = {
            "eth": "ETH",
            "ethereum": "ETH",
            "btc": "BTC",
            "bitcoin": "BTC",
            "usdc": "USDC",
            "usdt": "USDT",
            "sol": "SOL",
            "solana": "SOL",
            "avax": "AVAX",
            "matic": "MATIC",
            "arb": "ARB",
            "op": "OP",
            "link": "LINK",
            "uni": "UNI",
            "aave": "AAVE",
        }

        # Extract tokens mentioned
        found_tokens = []
        for token_name, symbol in token_map.items():
            if token_name in message_lower and symbol not in found_tokens:
                found_tokens.append(symbol)

        if len(found_tokens) < 2:
            # Default pair for generic swap queries
            if "eth" in message_lower:
                return ("ETH", "USDC", 1.0)
            return None

        # Determine order based on common patterns
        # "X to Y" pattern
        to_pattern = re.search(r"(\w+)\s+to\s+(\w+)", message_lower)
        if to_pattern:
            from_raw = to_pattern.group(1)
            to_raw = to_pattern.group(2)
            from_token = token_map.get(from_raw, from_raw.upper())
            to_token = token_map.get(to_raw, to_raw.upper())

            # Extract amount if present
            amount = 1.0
            amount_match = re.search(r"(\d+(?:\.\d+)?)\s*" + from_raw, message_lower)
            if amount_match:
                amount = float(amount_match.group(1))

            return (from_token, to_token, amount)

        # Default: first token → second token
        return (found_tokens[0], found_tokens[1], 1.0)

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
