# Phase 7: Real API Integration Plan

**Document**: Phase 7 API Integration  
**Date**: December 1, 2025  
**Status**: 🚧 **IN PROGRESS**  
**Priority**: P0 - Enterprise Critical  
**Timeline**: 3 weeks (Dec 1-22, 2025)

---

## 📋 **Executive Summary**

Phase 7 focuses on replacing all mock/placeholder data with **real external API integrations**. This is the final critical step before production launch, enabling all 18 Agent Squad agents to use live data from DeFi protocols, blockchain networks, compliance services, and more.

### **Key Objective**
Transform Agent Squad from a functional system with mock data into a **production-ready platform** with real-time data from 15+ external services.

---

## 🎯 **Integration Priorities**

### **Week 1: DeFi Data APIs** (Dec 1-8) 🚧 **CURRENT**

#### **1.1 1inch DEX Aggregator**
- **Purpose**: Swap quotes, price data, liquidity routing
- **Used By**: ExecutionAgent, HunterAIAgent
- **API Docs**: https://docs.1inch.io/docs/aggregation-protocol/api/
- **Endpoints**:
  - `/v5.0/{chain}/quote` - Get swap quote
  - `/v5.0/{chain}/swap` - Execute swap
  - `/v5.0/{chain}/tokens` - Get token list
- **Rate Limits**: 1 req/sec (free), 10 req/sec (paid)
- **Authentication**: API key (free tier available)

**Implementation**:
```python
# src/app/infrastructure/adapters/external/oneinch_client.py
class OneInchClient:
    async def get_swap_quote(
        self, 
        from_token: str, 
        to_token: str, 
        amount: str,
        chain: str = "ethereum"
    ) -> SwapQuote
    
    async def execute_swap(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0
    ) -> SwapTransaction
```

#### **1.2 DeFiLlama**
- **Purpose**: Protocol TVL, APY, historical data
- **Used By**: ResearchAgent, DefiYieldAgent, RiskAnalyzerAgent
- **API Docs**: https://defillama.com/docs/api
- **Endpoints**:
  - `/protocols` - Get all protocols
  - `/protocol/{protocol}` - Get protocol details
  - `/tvl/{protocol}` - Get TVL history
  - `/yields` - Get yield data
- **Rate Limits**: No strict limits (public API)
- **Authentication**: None required

**Implementation**:
```python
# src/app/infrastructure/adapters/external/defillama_client.py
class DefiLlamaClient:
    async def get_protocol_tvl(self, protocol: str) -> ProtocolTVL
    async def get_protocol_yields(self, protocol: str) -> list[YieldData]
    async def get_all_protocols(self) -> list[Protocol]
```

#### **1.3 CoinGecko**
- **Purpose**: Market data, price feeds, historical data
- **Used By**: HunterAIAgent, PortfolioAgent, RiskAnalyzerAgent
- **API Docs**: https://www.coingecko.com/en/api/documentation
- **Endpoints**:
  - `/simple/price` - Get current prices
  - `/coins/{id}` - Get coin details
  - `/coins/{id}/market_chart` - Get price history
- **Rate Limits**: 10-50 calls/min (free tier)
- **Authentication**: API key (free tier available)

**Implementation**:
```python
# src/app/infrastructure/adapters/external/coingecko_client.py
class CoinGeckoClient:
    async def get_price(self, coin_id: str, vs_currency: str = "usd") -> Price
    async def get_market_chart(self, coin_id: str, days: int = 30) -> MarketChart
    async def get_coin_details(self, coin_id: str) -> CoinDetails
```

#### **1.4 Hyperliquid** ✨ **NEW**
- **Purpose**: Perpetual futures trading, order book data, liquidations
- **Used By**: ExecutionAgent, HunterAIAgent, RiskAnalyzerAgent
- **API Docs**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Endpoints**:
  - `/info` - Get market data, order book, positions
  - `/exchange` - Place orders, cancel orders, get fills
  - `/stats` - Get funding rates, liquidations, volume
- **Rate Limits**: 1200 req/min
- **Authentication**: API key + signature for trading

**Implementation**:
```python
# src/app/infrastructure/adapters/external/hyperliquid_client.py
class HyperliquidClient:
    async def get_order_book(self, symbol: str) -> OrderBook
    async def get_funding_rate(self, symbol: str) -> FundingRate
    async def get_liquidations(self, hours: int = 24) -> list[Liquidation]
    async def place_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        size: float,
        price: float | None = None  # None for market order
    ) -> Order
    async def get_user_positions(self, address: str) -> list[Position]
```

#### **1.5 Uniswap v3**
- **Purpose**: DEX liquidity, pool data, swap simulation
- **Used By**: ExecutionAgent, DefiYieldAgent
- **API**: The Graph (Uniswap v3 subgraph)
- **Endpoints**: GraphQL queries
- **Rate Limits**: 1000 queries/day (free tier)

**Implementation**:
```python
# src/app/infrastructure/adapters/external/uniswap_client.py
class UniswapClient:
    async def get_pool_data(self, pool_address: str) -> PoolData
    async def get_token_price(self, token_address: str) -> TokenPrice
    async def simulate_swap(
        self,
        from_token: str,
        to_token: str,
        amount: str
    ) -> SwapSimulation
```

#### **1.6 Curve Finance**
- **Purpose**: Stablecoin swaps, liquidity pools, APY
- **Used By**: DefiYieldAgent, ExecutionAgent
- **API**: Curve API + on-chain calls
- **Endpoints**: https://api.curve.fi/

**Implementation**:
```python
# src/app/infrastructure/adapters/external/curve_client.py
class CurveClient:
    async def get_pool_apy(self, pool_address: str) -> PoolAPY
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str
    ) -> SwapQuote
```

#### **1.7 Aave v3**
- **Purpose**: Lending/borrowing rates, liquidation data
- **Used By**: LendingBorrowingAgent, RiskAnalyzerAgent
- **API**: Aave v3 subgraph (The Graph)
- **Endpoints**: GraphQL queries

**Implementation**:
```python
# src/app/infrastructure/adapters/external/aave_client.py
class AaveClient:
    async def get_market_data(self, asset: str) -> MarketData
    async def get_user_position(self, user_address: str) -> UserPosition
    async def calculate_health_factor(
        self,
        collateral_usd: float,
        debt_usd: float
    ) -> float
```

---

### **Week 2: Enterprise & Security APIs** (Dec 9-15) ⏳

#### **2.1 Chainalysis**
- **Purpose**: AML/KYC screening, sanctions check
- **Used By**: ComplianceMonitorAgent
- **API Docs**: https://docs.chainalysis.com/
- **Authentication**: API key (enterprise license required)

#### **2.2 TRM Labs**
- **Purpose**: Transaction risk scoring, sanctions screening
- **Used By**: ComplianceMonitorAgent
- **API Docs**: https://docs.trmlabs.com/

#### **2.3 Gnosis Safe SDK**
- **Purpose**: Multi-sig wallet operations, proposal management
- **Used By**: MultiSigCoordinatorAgent
- **SDK**: @safe-global/safe-core-sdk

#### **2.4 Forta Network**
- **Purpose**: Real-time security alerts, anomaly detection
- **Used By**: AlertMonitoringAgent, CrisisManagerAgent
- **API Docs**: https://docs.forta.network/

#### **2.5 Twilio**
- **Purpose**: SMS/voice alerts for critical events
- **Used By**: AlertMonitoringAgent, CrisisManagerAgent
- **API Docs**: https://www.twilio.com/docs/usage/api

---

### **Week 3: Blockchain & Advanced APIs** (Dec 16-22) ⏳

#### **3.1 Privy SDK**
- **Purpose**: Embedded wallet, authentication
- **Used By**: ExecutionAgent
- **SDK**: @privy-io/react-auth

#### **3.2 Axelar Network**
- **Purpose**: Cross-chain messaging, asset bridging
- **Used By**: BridgeCrosschainAgent
- **API Docs**: https://docs.axelar.dev/

#### **3.3 LayerZero**
- **Purpose**: Omnichain interoperability
- **Used By**: BridgeCrosschainAgent
- **API Docs**: https://layerzero.gitbook.io/

#### **3.4 OpenSea API**
- **Purpose**: NFT market data, valuations, sales
- **Used By**: NFTAssetManagerAgent
- **API Docs**: https://docs.opensea.io/

#### **3.5 Snapshot API**
- **Purpose**: DAO governance, voting, proposals
- **Used By**: DAOGovernanceAgent
- **API Docs**: https://docs.snapshot.org/

---

## 🏗️ **Implementation Strategy**

### **1. Create External API Client Layer**

**Directory Structure**:
```
src/app/infrastructure/adapters/external/
├── __init__.py
├── oneinch_client.py          ✨ Week 1
├── defillama_client.py         ✨ Week 1
├── coingecko_client.py         ✨ Week 1
├── hyperliquid_client.py       ✨ Week 1 (NEW)
├── uniswap_client.py           ✨ Week 1
├── curve_client.py             ✨ Week 1
├── aave_client.py              ✨ Week 1
├── chainalysis_client.py       ⏳ Week 2
├── trm_labs_client.py          ⏳ Week 2
├── gnosis_safe_client.py       ⏳ Week 2
├── forta_client.py             ⏳ Week 2
├── twilio_client.py            ⏳ Week 2
├── privy_client.py             ⏳ Week 3
├── axelar_client.py            ⏳ Week 3
├── layerzero_client.py         ⏳ Week 3
├── opensea_client.py           ⏳ Week 3
└── snapshot_client.py          ⏳ Week 3
```

### **2. Update Agent Implementations**

Replace mock data calls in each agent:

**Example (Hunter AI Agent)**:
```python
# BEFORE (Mock data)
async def execute(self, conversation_id, message, context) -> AgentResponse:
    # Mock implementation
    mock_price = "$3,200"
    response = f"ETH is currently trading at {mock_price}"
    return AgentResponse(content=response, ...)

# AFTER (Real API)
async def execute(self, conversation_id, message, context) -> AgentResponse:
    # Parse token from message
    token = self._extract_token(message)
    
    # Get real price from CoinGecko
    price_data = await self._coingecko_client.get_price(token)
    
    # Get 1inch quote for comparison
    oneinch_quote = await self._oneinch_client.get_swap_quote(
        from_token=token,
        to_token="USDC",
        amount="1"
    )
    
    response = f"{token.upper()} is trading at ${price_data.usd:.2f}"
    return AgentResponse(content=response, ...)
```

### **3. Add Environment Configuration**

**Update `config/local/config.toml`**:
```toml
[external_apis]
# DeFi Data
ONEINCH_API_KEY = ""
COINGECKO_API_KEY = ""
HYPERLIQUID_API_KEY = ""        # NEW
HYPERLIQUID_API_SECRET = ""     # NEW

# Enterprise
CHAINALYSIS_API_KEY = ""
TRM_LABS_API_KEY = ""

# Monitoring
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
FORTA_API_KEY = ""

# Blockchain
PRIVY_APP_ID = ""
OPENSEA_API_KEY = ""
```

### **4. Implement Rate Limiting & Caching**

**Rate Limiting**:
```python
from app.infrastructure.common.rate_limiter import RateLimiter

class OneInchClient:
    def __init__(self, api_key: str):
        self._rate_limiter = RateLimiter(max_requests=10, window=1)  # 10 req/sec
    
    async def get_swap_quote(self, ...):
        await self._rate_limiter.acquire()
        # Make API call
```

**Caching**:
```python
from app.infrastructure.common.cache import RedisCache

class CoinGeckoClient:
    def __init__(self, api_key: str, cache: RedisCache):
        self._cache = cache
    
    async def get_price(self, coin_id: str):
        cache_key = f"coingecko:price:{coin_id}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from API
        price = await self._fetch_price(coin_id)
        await self._cache.set(cache_key, price, ttl=60)  # 1 min cache
        return price
```

### **5. Error Handling & Fallbacks**

```python
class HunterAIAgent:
    async def execute(self, ...):
        try:
            # Try CoinGecko first
            price = await self._coingecko_client.get_price(token)
        except CoinGeckoAPIError:
            try:
                # Fallback to 1inch
                price = await self._oneinch_client.get_price(token)
            except OneInchAPIError:
                # Final fallback to mock data
                price = await self._get_mock_price(token)
        
        return AgentResponse(content=f"Price: ${price}", ...)
```

---

## 📊 **Testing Strategy**

### **1. Unit Tests for API Clients**
```python
# tests/unit/infrastructure/external/test_hyperliquid_client.py
@pytest.mark.asyncio
async def test_hyperliquid_get_order_book():
    client = HyperliquidClient(api_key="test_key")
    order_book = await client.get_order_book("ETH-PERP")
    
    assert order_book.bids
    assert order_book.asks
    assert order_book.symbol == "ETH-PERP"
```

### **2. Integration Tests with Real APIs**
```python
# tests/integration/external/test_defi_apis.py
@pytest.mark.asyncio
@pytest.mark.real_api
async def test_1inch_swap_quote():
    client = OneInchClient(api_key=os.getenv("ONEINCH_API_KEY"))
    quote = await client.get_swap_quote(
        from_token="ETH",
        to_token="USDC",
        amount="1000000000000000000"  # 1 ETH
    )
    
    assert quote.to_token_amount > 0
    assert quote.estimated_gas > 0
```

### **3. E2E Tests with Agents**
```python
# tests/e2e/agent_squad/test_agents_with_real_apis.py
@pytest.mark.asyncio
@pytest.mark.real_api
async def test_hunter_ai_with_real_coingecko():
    # Test Hunter AI agent uses real CoinGecko API
    response = await hunter_ai_agent.execute(
        conversation_id=uuid4(),
        message="What's the price of ETH?",
        context=mock_context
    )
    
    # Response should contain real price data
    assert "$" in response.content
    assert "ETH" in response.content
    assert response.tools_used == ["coingecko_api"]
```

---

## 🔒 **Security Considerations**

1. **API Key Management**
   - Store in `.secrets.toml` (not tracked in git)
   - Use environment variables in production
   - Rotate keys regularly

2. **Rate Limiting**
   - Implement per-API rate limiters
   - Handle 429 responses gracefully
   - Use exponential backoff

3. **Input Validation**
   - Sanitize user inputs before API calls
   - Validate token addresses (checksums)
   - Prevent injection attacks

4. **Error Handling**
   - Never expose API keys in error messages
   - Log errors securely (no sensitive data)
   - Provide user-friendly error messages

5. **Compliance**
   - Chainalysis/TRM Labs for AML/KYC
   - Log all transaction screening
   - Alert on high-risk addresses

---

## 📈 **Success Metrics**

- ✅ All 18 agents use real data (no mocks)
- ✅ Response latency < 3 seconds (p95)
- ✅ API error rate < 1%
- ✅ Cache hit rate > 50%
- ✅ 100% test coverage for API clients

---

## 🚀 **Rollout Plan**

### **Week 1 (Dec 1-8)**: DeFi APIs
- Day 1-2: 1inch, DeFiLlama, CoinGecko
- Day 3: Hyperliquid integration
- Day 4-5: Uniswap, Curve, Aave
- Day 6-7: Testing & optimization

### **Week 2 (Dec 9-15)**: Enterprise APIs
- Day 1-2: Chainalysis, TRM Labs
- Day 3: Gnosis Safe SDK
- Day 4: Forta Network
- Day 5: Twilio alerts
- Day 6-7: Testing & compliance validation

### **Week 3 (Dec 16-22)**: Advanced APIs
- Day 1-2: Privy SDK, Axelar, LayerZero
- Day 3-4: OpenSea, Snapshot
- Day 5-7: Full system testing, performance optimization

---

**Status**: 🚧 Week 1 Starting Now  
**Next Update**: December 8, 2025  
**Target Completion**: December 22, 2025
