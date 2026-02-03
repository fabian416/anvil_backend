# Hunter AI Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **Hunter AI** agent, providing real-time market intelligence including prices, swap quotes, and sentiment analysis.

### Key Features

- **Real-Time Price Data**: CoinGecko API integration
- **Swap Rate Quotes**: Hyperliquid Spot integration
- **Multi-Token Support**: 10,000+ cryptocurrencies
- **Sentiment Analysis**: News, Reddit, Twitter, Discord
- **LLM Analysis**: Vertex AI (gemini-2.0-flash)

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HUNTER AI ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌─────────────────┐
│  Chat         │    │   Shortcuts       │    │   Guest Chat    │
│  Endpoints    │    │   Endpoint        │    │   Endpoint      │
└───────┬───────┘    └──────────┬────────┘    └────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Application Layer   │
                    │  (Supervisor)        │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Authenticated│    │  Guest           │    │   Intent        │
│  Supervisor   │    │  Supervisor      │    │   Detector      │
└───────┬───────┘    └──────────┬───────┘    └────────┬────────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Infrastructure Layer │
                    │  (HunterAIAgent)      │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  CoinGecko    │    │  Hyperliquid     │    │   LLM Client    │
│  Client       │    │  Client          │    │  (Vertex AI)    │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Domain Layer

### Agent Type

```python
# src/app/domain/enums/agent_type.py
class AgentType(str, Enum):
    HUNTER_AI = "hunter_ai"
    # ... other agent types
```

### Agent Capabilities

Hunter AI handles these query types:

| Query Type | Description | Data Source |
|------------|-------------|-------------|
| Price Queries | Token prices and market data | CoinGecko |
| Swap Rates | Best swap rates between tokens | Hyperliquid / CoinGecko |
| Market Sentiment | Social and news sentiment | RSS, Reddit |
| Whale Activity | Large transaction monitoring | On-chain data |
| Technical Analysis | Price patterns and predictions | Historical data |

---

## Application Layer

### Supervisor Routing

Hunter AI is routed via the supervisor for these intents:

```python
# In authenticated_supervisor.py

"""
13. PRICE/MARKET DATA:
    - Token prices → "hunter_ai"
    - Market sentiment → "hunter_ai"
    
16. ADVANCED MARKET ANALYSIS:
    - Historical patterns, bull/bear market cycles → "hunter_ai"
    - Correlation analysis between tokens → "hunter_ai"
    - Whale activity, large transactions → "hunter_ai"
"""
```

### Example Routing

```python
"price of ETH" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get ETH price","depends_on":[]}}]}}
"BTC and ETH prices" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Get BTC and ETH prices","depends_on":[]}}]}}
"whale activity for BTC" → {{"tasks":[{{"agent_type":"hunter_ai","task_description":"Analyze whale activity for BTC","depends_on":[]}}]}}
```

---

## Infrastructure Layer

### HunterAIAgent

**Location**: `src/app/infrastructure/adapters/agent_squad/agents/hunter_ai_agent.py`

```python
class HunterAIAgent:
    """
    Hunter AI Agent implementation.
    
    Purpose: Market sentiment & predictions + Swap quotes
    
    Capabilities:
    - Real-time market sentiment analysis
    - Price predictions (technical analysis)
    - Social media sentiment
    - News sentiment
    - Fear & Greed Index
    - Spot swap quotes via Hyperliquid
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.3 (factual)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,
        coingecko_client: CoinGeckoClient | None = None,
        hyperliquid_client: HyperliquidClient | None = None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        self._llm_client = llm_client
        self._coingecko_client = coingecko_client
        self._hyperliquid_client = hyperliquid_client
        ...
```

### Key Methods

#### `execute()`

Main execution flow:

```python
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    """Execute Hunter AI agent."""
    
    # 1. Check for swap queries
    if is_swap_query and self._hyperliquid_client:
        swap_quote = await self._get_hyperliquid_quote(...)
    
    # 2. Fetch price data from CoinGecko
    if self._coingecko_client:
        tokens = self._extract_tokens(message.value)
        prices = await self._coingecko_client.get_prices_bulk(tokens)
    
    # 3. Generate response with LLM
    response = await self._llm_client.chat(
        messages=[
            {"role": "system", "content": system_prompt + market_context},
            {"role": "user", "content": message.value},
        ],
        model=self._model,
        temperature=self._temperature,
    )
    
    return AgentResponse(
        content=response["content"],
        sources=sources,
        ...
    )
```

#### `_extract_tokens()`

Extracts token mentions from user message:

```python
def _extract_tokens(self, message: str) -> list[str]:
    """Extract token names from user message."""
    token_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "usdc": "usd-coin",
        "pepe": "pepe",
        # ... 30+ tokens
    }
    
    found_tokens = []
    for token_name, coin_id in token_map.items():
        if token_name in message.lower():
            found_tokens.append(coin_id)
    
    return found_tokens
```

#### `_extract_swap_pair()`

Extracts swap pair from message:

```python
def _extract_swap_pair(self, message: str) -> tuple[str, str, float] | None:
    """
    Extract swap pair and amount from message.
    
    Examples:
        "swap 1 ETH to USDC" → ("ETH", "USDC", 1.0)
        "best rate for ETH to USDC" → ("ETH", "USDC", 1.0)
    """
    # Uses regex patterns to extract from_token, to_token, amount
    ...
```

---

## External Integrations

### CoinGecko Client

**Location**: `src/app/infrastructure/adapters/external/coingecko_client.py`

**Methods**:
- `get_price(token_id)` - Single token price
- `get_prices_bulk(token_ids)` - Multiple token prices
- `get_market_chart(token_id, days)` - Historical OHLCV data

**Rate Limits**: 10-50 calls/minute (free tier)

### Hyperliquid Client

**Location**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Methods**:
- `get_spot_quote(from_token, to_token, amount)` - Real-time swap quote
- `get_order_book(token)` - L2 order book data

**Rate Limits**: Unlimited

---

## Source Attribution

Hunter AI provides proper source attribution:

```python
# CoinGecko source
sources.append(SourceInfo(
    source_type=SourceType.API,
    source_name="CoinGecko",
    source_id=f"coin:{token_id}",
    url=f"https://www.coingecko.com/en/coins/{token_id}",
    citation_text=f"Real-time price data for {token_id.upper()}",
    fetched_at=fetched_at,
    provider="CoinGecko API",
    relevance_score=1.0,
))

# Hyperliquid source
sources.append(SourceInfo(
    source_type=SourceType.API,
    source_name="Hyperliquid",
    source_id=f"spot:{from_token}-{to_token}",
    url="https://app.hyperliquid.xyz/trade",
    citation_text="Real-time spot swap quote",
    fetched_at=fetched_at,
    provider="Hyperliquid API",
))
```

---

## LLM Integration

### System Prompt

```python
def _get_system_prompt(self) -> str:
    return """You are Hunter AI, Anvil's market sentiment and prediction specialist.

Your expertise:
- Real-time market sentiment analysis
- Technical analysis and price predictions
- Social media sentiment
- News sentiment and market narratives
- Fear & Greed Index interpretation

CRITICAL PRICE ACCURACY RULES:
- When REAL-TIME MARKET DATA is provided, use those EXACT prices
- Never estimate or guess when real data is available
- Format prices with commas: $92,619 (not $92619)

CRITICAL: ANVIL IS REAL, NOT SIMULATED
- Anvil is a REAL, LIVE DeFi platform
- DO NOT use words like "simulated" or "hypothetical"
- Use language like "On Anvil", "Anvil provides"

Always include:
- Data sources
- Confidence levels
- Risk warnings
- "Not financial advice" disclaimer
"""
```

### Context Injection

Market data is injected into the LLM context:

```python
market_data_context = f"""
REAL-TIME MARKET DATA (FROM COINGECKO API):

ETHEREUM:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B

CRITICAL: Use these EXACT prices. Do NOT estimate.
"""
```

---

## Error Handling

### API Failures

```python
try:
    prices = await self._coingecko_client.get_prices_bulk(tokens)
except Exception as e:
    logger.error(f"CoinGecko API error: {e}")
    market_data_context = f"(Note: Unable to fetch live data: {e})"
```

### Fallback Behavior

| Scenario | Fallback |
|----------|----------|
| CoinGecko unavailable | LLM-only response with disclaimer |
| Hyperliquid unavailable | Calculate from CoinGecko prices |
| Token not found | Skip token, continue with others |

---

## Testing Strategy

### Unit Tests

```python
def test_extract_tokens():
    agent = HunterAIAgent(...)
    tokens = agent._extract_tokens("price of BTC and ETH")
    assert "bitcoin" in tokens
    assert "ethereum" in tokens

def test_extract_swap_pair():
    agent = HunterAIAgent(...)
    pair = agent._extract_swap_pair("swap 1 ETH to USDC")
    assert pair == ("ETH", "USDC", 1.0)
```

### Integration Tests

```python
async def test_coingecko_price_fetch():
    client = CoinGeckoClient()
    price = await client.get_price("ethereum")
    assert price.usd > 0
    assert price.market_cap > 0
```

---

## Summary

Hunter AI implements:

1. **Hexagonal Architecture**: Clean separation of layers
2. **Real-Time Data**: CoinGecko and Hyperliquid integration
3. **Multi-Token Support**: 10,000+ tokens via CoinGecko
4. **Swap Quotes**: Hyperliquid Spot or calculated rates
5. **Source Attribution**: Proper API source tracking
6. **LLM Enhancement**: Context-aware responses with real data
7. **Error Handling**: Graceful fallbacks for API failures

All implementations follow established codebase patterns.
