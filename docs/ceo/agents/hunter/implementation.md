# Hunter AI Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── hunter_ai_agent.py          # Main agent
│       └── external/
│           ├── coingecko_client.py             # CoinGecko API
│           └── hyperliquid_client.py           # Hyperliquid API
├── domain/
│   ├── enums/
│   │   └── agent_type.py                       # AgentType.HUNTER_AI
│   └── services/
│       └── agent_squad/
│           └── authenticated_supervisor.py     # Routing
├── application/
│   └── hunter/
│       ├── trading_signal_generator.py         # Signal generation
│       ├── lstm_price_predictor.py             # Price predictions
│       ├── risk_analyzer.py                    # Risk analysis
│       ├── twitter_sentiment.py                # Twitter sentiment
│       ├── discord_sentiment.py                # Discord sentiment
│       └── portfolio_optimizer.py              # Portfolio optimization
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py       # DI configuration
```

---

## Core Files

### 1. Hunter AI Agent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/hunter_ai_agent.py`

**Lines**: ~540

**Key Classes**:
- `HunterAIAgent` - Main agent implementation

**Key Methods**:

| Method | Description |
|--------|-------------|
| `execute()` | Main execution with price/quote fetching |
| `_extract_tokens()` | Extract token IDs from message |
| `_extract_token()` | Extract single token (backward compat) |
| `_extract_swap_pair()` | Extract from_token, to_token, amount |
| `_get_system_prompt()` | LLM system prompt |
| `is_available()` | Availability check |

### 2. CoinGecko Client

**File**: `src/app/infrastructure/adapters/external/coingecko_client.py`

**Key Methods**:

| Method | Description |
|--------|-------------|
| `get_price(token_id)` | Single token price with 24h data |
| `get_prices_bulk(token_ids)` | Batch pricing (efficient) |
| `get_market_chart(token_id, days)` | Historical OHLCV |

### 3. Hyperliquid Client

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Key Methods**:

| Method | Description |
|--------|-------------|
| `get_spot_quote(from, to, amount)` | Real-time swap quote |
| `get_order_book(token)` | L2 order book |

---

## Token Mapping

### Supported Tokens

```python
token_map = {
    # Major tokens
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "bnb": "binancecoin",
    "ada": "cardano",
    "avax": "avalanche-2",
    "matic": "matic-network",
    "link": "chainlink",
    "uni": "uniswap",
    "aave": "aave",
    "crv": "curve-dao-token",
    
    # Stablecoins
    "usdc": "usd-coin",
    "usdt": "tether",
    "dai": "dai",
    "wbtc": "wrapped-bitcoin",
    
    # Meme tokens (Hyperliquid Spot)
    "pepe": "pepe",
    "trump": "official-trump",
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "bonk": "bonk",
    "floki": "floki",
    "wif": "dogwifcoin",
    "mog": "mog-coin",
    "brett": "brett",
    "neiro": "neiro-on-eth",
}
```

### Swap Token Mapping

```python
# For Hyperliquid spot quotes
token_map = {
    "eth": "ETH",
    "btc": "BTC",
    "usdc": "USDC",
    "usdt": "USDT",
    "sol": "SOL",
    "avax": "AVAX",
    "matic": "MATIC",
    "arb": "ARB",
    "op": "OP",
    "link": "LINK",
    "uni": "UNI",
    "aave": "AAVE",
}
```

---

## Configuration

### Dependency Injection

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_coingecko_client(self) -> CoinGeckoClient:
    """Provide CoinGecko client for price data."""
    return CoinGeckoClient()

@provide
def provide_hyperliquid_client(self) -> HyperliquidClient:
    """Provide Hyperliquid client for swap quotes."""
    return HyperliquidClient()

@provide
def provide_hunter_ai_agent(
    self,
    llm_client: LLMClientGateway,
    coingecko_client: CoinGeckoClient,
    hyperliquid_client: HyperliquidClient,
) -> HunterAIAgent:
    """Provide Hunter AI agent with all dependencies."""
    return HunterAIAgent(
        llm_client=llm_client,
        coingecko_client=coingecko_client,
        hyperliquid_client=hyperliquid_client,
        model="gemini-2.0-flash",
        temperature=0.3,
    )
```

---

## API Integration

### Request Flow

```
1. User sends "price of ETH" to chat endpoint
2. Supervisor routes to hunter_ai agent
3. HunterAIAgent.execute() called
4. _extract_tokens() finds "ethereum"
5. CoinGecko client fetches price
6. LLM generates response with real data
7. Response returned with sources
```

### Response Structure

```json
{
  "agent_message": {
    "content": "📊 **ETH Market Data**\n\n**Current Price:** $2,988.55\n...",
    "sources": [
      {
        "source_type": "api",
        "source_name": "CoinGecko",
        "source_id": "coin:ethereum",
        "url": "https://www.coingecko.com/en/coins/ethereum",
        "citation_text": "Real-time price data for ETHEREUM",
        "relevance_score": 1.0
      }
    ]
  },
  "enrichment": {
    "agents_used": ["hunter_ai"],
    "agent_timings": [
      {
        "agent_type": "hunter_ai",
        "execution_time_ms": 1200,
        "status": "completed"
      }
    ]
  }
}
```

---

## Swap Quote Logic

### Detection

```python
is_swap_query = any(phrase in message_lower for phrase in [
    "swap rate", "best rate", "exchange rate", "convert", 
    "swap", "trade", "best swap", "best price for",
    "eth to usdc", "btc to usdc", "usdc to eth",
]) and any(tok in message_lower for tok in ["eth", "btc", "usdc", "usdt"])
```

### Quote Fetching

```python
if is_swap_query and self._hyperliquid_client:
    swap_pair = self._extract_swap_pair(message.value)
    if swap_pair:
        from_token, to_token, amount = swap_pair
        quote = await self._hyperliquid_client.get_spot_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
        )
```

### Fallback to CoinGecko

```python
if not swap_quote_context and len(tokens) >= 2:
    # Calculate swap rate from CoinGecko prices
    from_price = prices_dict.get(from_id)
    to_price = prices_dict.get(to_id)
    
    if from_price and to_price:
        swap_rate = from_price.usd / to_price.usd
        output_amount = amount * swap_rate
```

---

## LLM Prompt Engineering

### System Prompt Key Points

1. **Price Accuracy**: Must use EXACT prices from data
2. **Formatting**: Use commas for thousands ($92,619)
3. **Real Platform**: Never say "simulated" or "hypothetical"
4. **Disclaimers**: Always include risk warnings

### Context Injection

```python
market_data_context = f"""
REAL-TIME MARKET DATA (FROM COINGECKO API - USE THESE EXACT PRICES):

ETHEREUM:
- Current Price: ${price.usd:,.2f}
- 24h Change: {price.usd_24h_change:+.2f}%
- Market Cap: ${price.market_cap / 1e9:.2f}B
- 24h Volume: ${price.volume_24h / 1e9:.2f}B

CRITICAL: You MUST use the EXACT prices shown above.
"""
```

---

## Error Handling

### CoinGecko Errors

```python
try:
    tokens = self._extract_tokens(message.value)
    if tokens:
        prices = await self._coingecko_client.get_prices_bulk(tokens)
except Exception as e:
    logger.error(f"CoinGecko API error: {e}")
    market_data_context = f"(Note: Unable to fetch live data: {e})"
```

### Hyperliquid Errors

```python
try:
    quote = await self._hyperliquid_client.get_spot_quote(...)
except Exception as e:
    logger.warning(f"Hyperliquid spot quote error: {e}")
    swap_quote_context = ""  # Will be calculated from CoinGecko
```

---

## Logging

### Debug Logging

```python
logger.info(f"🔍 Extracted tokens from message: {tokens}")
logger.info(f"📊 Fetching Hyperliquid spot quote: {amount} {from_token} → {to_token}")
logger.info(f"✅ CoinGecko client available for Hunter AI")
logger.warning(f"⚠️ CoinGecko client not available - LLM-only mode")
```

### Enable Debug Mode

```python
import logging
logging.getLogger("app.infrastructure.adapters.agent_squad.agents.hunter_ai_agent").setLevel(logging.DEBUG)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_hunter_ai_agent.py

# Integration tests
pytest tests/integration/test_coingecko_client.py

# All tests
make code.test
```

### Test Files

- `tests/unit/agents/test_hunter_ai_agent.py`
- `tests/unit/adapters/test_coingecko_client.py`
- `tests/unit/adapters/test_hyperliquid_client.py`

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Token extraction | <10ms | ~5ms |
| CoinGecko single | <500ms | ~300ms |
| CoinGecko bulk | <800ms | ~500ms |
| Hyperliquid quote | <200ms | ~100ms |
| LLM response | <2s | ~1.2s |
| Total response | <3s | ~2s |

### Caching Strategy

- CoinGecko prices: 60s TTL (via Redis)
- Hyperliquid quotes: No cache (real-time required)
- Market charts: 5min TTL

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added Hyperliquid integration |
| 2026-01-29 | Added multi-token support |
| 2026-01-29 | Added swap rate calculation fallback |
