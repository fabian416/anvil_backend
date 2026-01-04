# 1inch DEX Aggregator Integration - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

La integración con 1inch en Anvil Backend proporciona:

1. **DEX Aggregation**: Mejores precios de swap agregando 100+ DEXes
2. **Multi-Chain Support**: Ethereum, Polygon, Arbitrum, Optimism, Base, BSC
3. **MCP Server**: Servidor MCP para herramientas de AI agents
4. **Caching Layer**: Redis cache para reducir llamadas API
5. **Telemetry**: Observabilidad completa con tracing y métricas
6. **Rate Limiting**: Gestión de límites de API (1 req/sec free, 10 req/sec paid)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           1INCH INTEGRATION ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │    AI Agents    │
                                    │  (Trading, Swap)│
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
           ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
           │   MCP Server    │      │  SwapHandler    │      │  DEXPriceFetcher│
           │   (port 8082)   │      │  (Chat)         │      │  (ULTRA)        │
           └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │ InstrumentedClient   │
                                  │ (Telemetry + Tracing)│
                                  └──────────┬───────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │   CachedClient       │
                                  │   (Redis Cache)      │
                                  └──────────┬───────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │   OneInchClient      │
                                  │   (Base HTTP Client) │
                                  └──────────┬───────────┘
                                             │
                                             ▼
                              ╔════════════════════════════╗
                              ║      1inch API v5.2        ║
                              ║   https://api.1inch.dev    ║
                              ╚════════════════════════════╝
```

---

## Client Layer Stack

### 1. Base Client (`OneInchClient`)

**Location**: `src/app/infrastructure/adapters/external/oneinch_client.py`

El cliente base que maneja las llamadas HTTP a la API de 1inch.

```python
class OneInchClient:
    """Base 1inch API client."""
    
    BASE_URL = "https://api.1inch.dev"
    
    # Supported chains
    CHAINS = {
        "ethereum": 1,
        "bsc": 56,
        "polygon": 137,
        "optimism": 10,
        "arbitrum": 42161,
        "gnosis": 100,
        "avalanche": 43114,
        "fantom": 250,
        "base": 8453,
    }
    
    def __init__(self, api_key: str, chain: str = "ethereum"):
        self._api_key = api_key
        self._chain_id = self.CHAINS.get(chain.lower(), 1)
        self._client = httpx.AsyncClient(
            base_url=f"{self.BASE_URL}/swap/v5.2/{self._chain_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
```

### 2. Cached Client (`CachedOneInchClient`)

**Location**: `src/app/infrastructure/adapters/external/cached/cached_oneinch_client.py`

Añade caching Redis para reducir llamadas a la API.

```python
class CachedOneInchClient(OneInchClient):
    """1inch client with Redis caching."""
    
    API_NAME = "oneinch"
    
    # Cache TTLs:
    # - Quotes: 30s (prices change fast)
    # - Tokens: 15min (changes rarely)
    # - Protocols: 15min (changes rarely)
    # - Swap data: NOT CACHED (user-specific)
```

**Cache Strategy**:

| Endpoint | TTL | Reason |
|----------|-----|--------|
| `get_swap_quote` | 30s | Prices change frequently |
| `get_tokens` | 15min | Token list changes rarely |
| `get_protocols` | 15min | Protocol list changes rarely |
| `get_token_price` | 30s | Prices change frequently |
| `get_swap_data` | **NOT CACHED** | User-specific, time-sensitive |

### 3. Instrumented Client (`InstrumentedOneInchClient`)

**Location**: `src/app/infrastructure/adapters/external/instrumented/instrumented_oneinch_client.py`

Añade telemetría completa para observabilidad.

```python
class InstrumentedOneInchClient(OneInchClient):
    """1inch client with full telemetry."""
    
    API_NAME = "oneinch"
    
    async def get_swap_quote(self, ...):
        # Start telemetry context
        ctx = self._telemetry.start_call(
            api=self.API_NAME,
            operation="get_swap_quote",
        )
        
        # Start distributed trace span
        with self._tracing.start_span(
            name="oneinch.get_swap_quote",
            kind=SpanKind.CLIENT,
        ) as span:
            try:
                result = await super().get_swap_quote(...)
                ctx.complete(status=APIStatus.SUCCESS)
                return result
            except Exception as e:
                ctx.complete(status=self._classify_error(e))
                raise
```

**Error Classification**:

| Error Type | Status |
|------------|--------|
| Timeout | `APIStatus.TIMEOUT` |
| HTTP 429 | `APIStatus.RATE_LIMITED` |
| HTTP 401/403 | `APIStatus.AUTH_FAILURE` |
| Other | `APIStatus.ERROR` |

---

## API Methods

### SwapQuote

Obtiene cotización de swap sin ejecutar.

```python
@dataclass
class SwapQuote:
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    estimated_gas: int
    protocols: list[list[dict]]  # Routing path
    price_impact: float          # Percentage

# Usage
quote = await client.get_swap_quote(
    from_token="0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
    to_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",    # USDC
    amount="1000000000000000000",  # 1 ETH in wei
    slippage=1.0,
)
print(f"Expected: {int(quote.to_amount) / 1e6} USDC")
```

### SwapTransaction

Obtiene datos de transacción para ejecutar swap.

```python
@dataclass
class SwapTransaction:
    from_token: str
    to_token: str
    to_amount: str
    tx_data: str    # Transaction calldata
    tx_to: str      # Router contract address
    tx_value: str   # ETH value (for ETH swaps)
    gas_price: str

# Usage
swap_tx = await client.get_swap_data(
    from_token="0xEeee...",
    to_token="0xA0b8...",
    amount="1000000000000000000",
    from_address="0xUserWallet...",
    slippage=1.0,
)
# Submit tx_data to blockchain via Privy
```

### Token List

```python
@dataclass
class Token:
    address: str
    symbol: str
    name: str
    decimals: int
    logo_uri: str | None

# Usage
tokens = await client.get_tokens()
usdc = next(t for t in tokens if t.symbol == "USDC")
```

### Token Price

```python
# Get token price in USD
eth_price = await client.get_token_price(
    "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
)
print(f"ETH: ${eth_price:.2f}")
```

### Protocols/Liquidity Sources

```python
# Get available DEXes
protocols = await client.get_protocols()
# ["UNISWAP_V3", "SUSHISWAP", "CURVE", "BALANCER", ...]
```

---

## MCP Server

### OneInchMCPServer

**Location**: `src/app/infrastructure/mcp/servers/oneinch_mcp.py`

Servidor MCP que expone herramientas para AI agents.

```python
class OneInchMCPServer(MCPServer):
    """MCP Server for 1inch DEX aggregator."""
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.1inch.dev",
    ):
        super().__init__(
            server_name="1inch",
            description="1inch DEX aggregator for best swap routes",
            port=8081,
        )
```

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_swap_quote` | Get best swap quote | chain_id, from_token, to_token, amount |
| `get_liquidity_sources` | Get available DEXes | chain_id |
| `get_token_price` | Get token USD price | chain_id, token_address |
| `get_supported_chains` | Get supported chains | (none) |

### Running MCP Server

```bash
# Via Makefile
make mcp.oneinch  # Starts on port 8082

# Standalone
ONEINCH_API_KEY=your_key python -m app.infrastructure.mcp.servers.oneinch_mcp
```

### MCP Endpoints

```
http://localhost:8082/tools         # List available tools
http://localhost:8082/health        # Health check
http://localhost:8082/invoke        # Invoke tool (POST)
```

---

## Configuration

### Environment Variables

```toml
# config/local/.secrets.toml
[oneinch]
API_KEY = "your-1inch-api-key"
```

```bash
# Or via environment
export ONEINCH_API_KEY="your-1inch-api-key"
```

### Feature Flags

```python
# src/app/setup/config/agent_squad.py
class ExternalAPIsSettings:
    enable_1inch: bool = True

# src/app/setup/config/mcp.py
class MCPServersSettings:
    oneinch_enabled: bool = True
```

---

## Supported Chains

| Chain | Chain ID | Symbol |
|-------|----------|--------|
| Ethereum | 1 | ETH |
| BNB Chain | 56 | BNB |
| Polygon | 137 | MATIC |
| Optimism | 10 | ETH |
| Arbitrum | 42161 | ETH |
| Gnosis | 100 | xDAI |
| Avalanche | 43114 | AVAX |
| Fantom | 250 | FTM |
| Base | 8453 | ETH |

---

## Integration Points

### 1. SwapHandler (Chat)

**Location**: `src/app/application/chat/handlers/swap_handler.py`

Maneja swaps desde el chat usando 1inch para single-chain.

```python
class SwapHandler:
    """
    Swap routing:
    - Same-chain: Uses 1inch (best rates)
    - Cross-chain: Uses LiFi
    - Perps: Uses Hyperliquid
    """
    
    async def get_quote(self, request: SwapRequest) -> SwapResponse:
        if request.is_cross_chain:
            return await self._get_lifi_quote(request)
        elif self._oneinch:
            return await self._get_oneinch_quote(request)
        else:
            return await self._get_lifi_quote(request)  # Fallback
```

### 2. DEXPriceFetcher (ULTRA)

**Location**: `src/app/application/ultra/dex_price_fetcher.py`

Obtiene precios para arbitraje y análisis.

```python
class DEXPriceFetcher:
    """
    Price sources:
    1. 1inch API - Best aggregated prices
    2. Fallback simulation for testing
    """
    
    async def get_all_quotes(self, from_token, to_token, amount):
        quotes = []
        
        # 1inch quote (real aggregated price)
        oneinch_quote = await self.get_quote_1inch(...)
        if oneinch_quote:
            quotes.append(oneinch_quote)
        
        # Additional sources...
        return quotes
```

### 3. TradingAgent (Agno)

**Location**: `src/app/infrastructure/agno/trading_agent.py`

Agente AI especializado en trading usando 1inch.

```python
class TradingAgent(BaseAgent):
    """Trading agent using 1inch and Curve MCP tools."""
    
    def __init__(self):
        super().__init__(
            role="DeFi trading specialist",
            mcp_servers=["1inch", "curve"],
        )
    
    # Agent uses 1inch MCP tools for:
    # - Finding best swap prices
    # - Comparing routes
    # - Getting liquidity info
```

### 4. ExecuteActionCommand

**Location**: `src/app/application/chat/commands/execute_action.py`

Ejecuta acciones de swap desde el chat.

```python
class ExecuteActionCommand:
    """Execute chat actions including swaps."""
    
    async def _execute_swap(self, action: SwapAction):
        if self._oneinch:
            quote = await self._oneinch.get_swap_quote(...)
        
        # Execute via Privy wallet
        tx = await self._privy.send_transaction(
            data=swap_tx.tx_data,
            to=swap_tx.tx_to,
            value=swap_tx.tx_value,
        )
```

---

## Rate Limiting

### API Limits

| Tier | Rate Limit | Cost |
|------|------------|------|
| Free | 1 req/sec | $0 |
| Paid | 10 req/sec | ~$49/mo |

### Handling Rate Limits

```python
# Retry with exponential backoff
self._retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)

# Rate limit detection in telemetry
if isinstance(error, httpx.HTTPStatusError):
    if error.response.status_code == 429:
        return APIStatus.RATE_LIMITED
```

---

## Caching Strategy

### Cache Configuration

```python
# src/app/infrastructure/cache/external_api_cache.py
CACHE_TTLS = {
    ("oneinch", "quote"): 30,           # 30 seconds
    ("oneinch", "swap"): 5,             # 5 seconds (very short)
    ("oneinch", "tokens"): 900,         # 15 minutes
    ("oneinch", "liquidity"): 900,      # 15 minutes
}
```

### Cache Key Structure

```python
# Quote cache key example
cache_key = f"oneinch:quote:ethereum:{from_token}:{to_token}:{amount}"
```

---

## Telemetry & Observability

### Metrics Tracked

| Metric | Description |
|--------|-------------|
| Request latency | Time per API call |
| Success rate | % of successful calls |
| Rate limit hits | 429 errors |
| Error types | Timeout, auth, etc. |
| Cost estimation | ~$0.05 per 1000 calls |

### Accessing Metrics

```python
from app.infrastructure.telemetry.api_telemetry import get_api_telemetry

telemetry = get_api_telemetry()
metrics = telemetry.get_metrics("oneinch")
print(f"Success rate: {metrics.success_rate}%")
print(f"Avg latency: {metrics.avg_latency_ms}ms")
```

### Distributed Tracing

```python
# Spans created for each call
with self._tracing.start_span(
    name="oneinch.get_swap_quote",
    kind=SpanKind.CLIENT,
    attributes={
        "api.name": "oneinch",
        "api.operation": "get_swap_quote",
        "from_token": from_token,
        "to_token": to_token,
    },
) as span:
    # API call...
```

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| 429 Too Many Requests | Rate limit exceeded | Implement backoff |
| 401 Unauthorized | Invalid API key | Check key |
| 400 Bad Request | Invalid params | Validate input |
| Timeout | Network/API slow | Retry with backoff |

### Error Response Format

```python
# MCP tool error response
{
    "error": "1inch API error: 429 Too Many Requests",
    "chain_id": 1,
}
```

---

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_get_swap_quote():
    client = OneInchClient(api_key="test_key")
    client._client = AsyncMock()
    client._client.get.return_value = MockResponse({
        "toAmount": "3000000000",  # 3000 USDC
        "estimatedGas": 200000,
    })
    
    quote = await client.get_swap_quote(
        from_token="0xEeee...",
        to_token="0xA0b8...",
        amount="1000000000000000000",
    )
    
    assert quote.to_amount == "3000000000"
```

### Integration Testing

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_quote():
    """Test against real 1inch API (requires API key)."""
    client = OneInchClient(api_key=os.getenv("ONEINCH_API_KEY"))
    
    quote = await client.get_swap_quote(
        from_token="0xEeee...",  # ETH
        to_token="0xA0b8...",    # USDC
        amount="100000000000000000",  # 0.1 ETH
    )
    
    assert int(quote.to_amount) > 0
    await client.close()
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Base Client** | `infrastructure/adapters/external/oneinch_client.py` | HTTP client |
| **Cached Client** | `infrastructure/adapters/external/cached/cached_oneinch_client.py` | Redis cache |
| **Instrumented** | `infrastructure/adapters/external/instrumented/instrumented_oneinch_client.py` | Telemetry |
| **MCP Server** | `infrastructure/mcp/servers/oneinch_mcp.py` | AI agent tools |
| **DeFi Provider** | `infrastructure/defi/providers/oneinch.py` | Alternative client |
| **Swap Handler** | `application/chat/handlers/swap_handler.py` | Chat integration |
| **DEX Fetcher** | `application/ultra/dex_price_fetcher.py` | ULTRA integration |
| **Trading Agent** | `infrastructure/agno/trading_agent.py` | AI agent |
| **Config** | `setup/config/mcp.py` | Feature flags |

---

## Best Practices

### 1. Always Use Caching

```python
# DON'T: Direct client (hits API every time)
client = OneInchClient(api_key=key)

# DO: Cached client (reduces API calls)
client = CachedOneInchClient(api_key=key, cache=redis_cache)
```

### 2. Handle Rate Limits

```python
# DON'T: Ignore rate limits
quote = await client.get_swap_quote(...)

# DO: Implement retry with backoff
@retry(wait=wait_exponential(min=2, max=10))
async def get_quote_with_retry(...):
    return await client.get_swap_quote(...)
```

### 3. Use Telemetry in Production

```python
# DO: Use instrumented client for observability
client = InstrumentedOneInchClient(api_key=key)
```

### 4. Validate Token Addresses

```python
# DO: Normalize addresses
from_token = from_token.lower()
to_token = to_token.lower()

# Validate format
if not from_token.startswith("0x") or len(from_token) != 42:
    raise ValueError("Invalid token address")
```

---

## API Reference

### 1inch API v5.2 Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/swap/v5.2/{chain}/quote` | GET | Get swap quote |
| `/swap/v5.2/{chain}/swap` | GET | Get swap tx data |
| `/swap/v5.2/{chain}/tokens` | GET | List tokens |
| `/swap/v5.2/{chain}/liquidity-sources` | GET | List DEXes |
| `/swap/v5.2/{chain}/approve/spender` | GET | Get approval address |
| `/price/v1.1/{chain}/{token}` | GET | Get token price |

### Official Documentation

- API Docs: https://docs.1inch.io/docs/aggregation-protocol/api/
- Rate Limits: https://docs.1inch.io/docs/aggregation-protocol/api/rate-limits

---

**Last Updated**: January 2, 2026
