# Requirements Document: Hyperliquid Integration

## Introduction

This specification defines the requirements for completing the **Hyperliquid integration** into the Anvil Backend DeFi Multi-Agents Chat platform. Hyperliquid is a high-performance decentralized perpetual futures exchange built on its own L1 blockchain, offering CEX-like performance with on-chain transparency.

The existing `HyperliquidClient` infrastructure adapter provides basic API connectivity. This spec focuses on:
- **Full domain layer integration** (ports, entities, value objects)
- **Application layer interactors** for perpetual trading operations
- **HTTP API endpoints** for frontend consumption
- **Trading Agent integration** for derivatives recommendations

### Why Hyperliquid Matters

Hyperliquid leads the DEX perpetuals market with:
- **$3B+ daily volume** - highest among perp DEXs
- **Sub-second latency** - custom L1 built for trading
- **50+ perpetual markets** - BTC, ETH, SOL, and altcoins
- **Up to 50x leverage** - competitive with centralized exchanges
- **Zero gas fees** - subsidized by protocol

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | Hyperliquid Integration |
|-----------------|-------------------------|
| **Derivatives Trading** | Perpetual futures with leverage |
| **Risk Management** | Position sizing, liquidation prices |
| **Market Analysis** | Funding rates, open interest, liquidations |
| **Portfolio Tracking** | PnL tracking, margin health |

### Business Objectives Alignment

- **User Engagement**: Enable perpetual trading guidance from chat
- **Traders**: Provide funding rate arbitrage opportunities
- **Risk-Aware**: Liquidation monitoring and risk alerts

---

## Requirements

### Requirement 1: Market Data Retrieval

**User Story:** As a trader, I want to see all available perpetual markets with current prices and funding rates, so that I can identify trading opportunities.

#### Acceptance Criteria

1. WHEN user queries markets THEN the system SHALL return all perpetual pairs
2. WHEN market data is returned THEN it SHALL include: symbol, mark price, index price, funding rate
3. IF funding rate is high (>0.05%/8h) THEN the system SHALL flag as funding opportunity
4. WHEN displaying funding THEN the system SHALL show annualized rate
5. IF market has unusual spread THEN the system SHALL indicate potential manipulation
6. WHEN querying specific market THEN the system SHALL include 24h high/low/volume

---

### Requirement 2: Order Book Data

**User Story:** As a trader, I want to see order book depth, so that I can assess liquidity before trading.

#### Acceptance Criteria

1. WHEN user requests order book THEN the system SHALL return top bids and asks
2. WHEN order book is returned THEN it SHALL include price and size for each level
3. IF spread is wide (>0.1%) THEN the system SHALL warn about slippage
4. WHEN displaying depth THEN the system SHALL show cumulative size at each level
5. IF large order detected THEN the system SHALL estimate price impact
6. WHEN order book is stale (>1s) THEN the system SHALL refresh automatically

---

### Requirement 3: Funding Rate Analysis

**User Story:** As a trader, I want to analyze funding rate trends, so that I can profit from funding arbitrage.

#### Acceptance Criteria

1. WHEN user queries funding rates THEN the system SHALL return current and predicted rates
2. WHEN funding data is returned THEN it SHALL include: current rate, next funding time
3. IF funding is significantly positive THEN the system SHALL suggest short bias
4. IF funding is significantly negative THEN the system SHALL suggest long bias
5. WHEN comparing markets THEN the system SHALL rank by funding opportunity
6. WHEN historical data exists THEN the system SHALL show 7-day average funding

---

### Requirement 4: Liquidation Monitoring

**User Story:** As a trader, I want to monitor liquidations in the market, so that I can understand market stress.

#### Acceptance Criteria

1. WHEN user queries liquidations THEN the system SHALL return recent liquidation events
2. WHEN liquidation data is returned THEN it SHALL include: symbol, side, size, price, time
3. IF large liquidation occurs (>$100k) THEN the system SHALL flag as significant
4. WHEN aggregating liquidations THEN the system SHALL show long vs short breakdown
5. IF cascade liquidations detected THEN the system SHALL issue market stress alert
6. WHEN querying by timeframe THEN the system SHALL support 1h, 4h, 24h windows

---

### Requirement 5: Position Information (Read-Only)

**User Story:** As a trader, I want to view my positions on Hyperliquid, so that I can manage my portfolio.

#### Acceptance Criteria

1. WHEN user provides wallet address THEN the system SHALL return open positions
2. WHEN position data is returned THEN it SHALL include: symbol, size, entry price, PnL
3. IF position is at liquidation risk THEN the system SHALL show warning
4. WHEN displaying PnL THEN the system SHALL show both unrealized and realized
5. IF leverage is high (>10x) THEN the system SHALL indicate risk level
6. WHEN margin ratio is low (<20%) THEN the system SHALL issue margin call warning

---

### Requirement 6: Trading Agent Integration

**User Story:** As a user chatting with Trading Agent, I want intelligent perpetual trading recommendations, so that I can make informed decisions.

#### Acceptance Criteria

1. WHEN user asks about perpetuals THEN Trading Agent SHALL query Hyperliquid data
2. IF user mentions "funding" THEN agent SHALL surface funding rate opportunities
3. WHEN user asks about market sentiment THEN agent SHALL analyze long/short ratio
4. IF user asks about risk THEN agent SHALL calculate position sizing suggestions
5. WHEN large liquidations occur THEN agent SHALL proactively mention market stress
6. IF user has open positions THEN agent SHALL include PnL context in responses

---

### Requirement 7: Risk Calculation Tools

**User Story:** As a trader, I want position sizing and liquidation price calculations, so that I can manage risk effectively.

#### Acceptance Criteria

1. WHEN user requests position size THEN the system SHALL calculate based on risk %
2. WHEN calculating liquidation price THEN the system SHALL use current margin mode
3. IF leverage is requested THEN the system SHALL show liquidation at that leverage
4. WHEN displaying risk THEN the system SHALL show max loss in USD terms
5. IF position exceeds risk parameters THEN the system SHALL suggest smaller size
6. WHEN margin is cross-margin THEN the system SHALL factor in all positions

---

### Requirement 8: Market Analytics

**User Story:** As a trader, I want to see open interest and volume trends, so that I can understand market dynamics.

#### Acceptance Criteria

1. WHEN user queries open interest THEN the system SHALL return per-market OI
2. WHEN OI data is returned THEN it SHALL include: long OI, short OI, total USD value
3. IF OI is increasing with price THEN the system SHALL indicate trend confirmation
4. IF OI is decreasing THEN the system SHALL indicate potential reversal
5. WHEN displaying volume THEN the system SHALL show 24h and 7d comparisons
6. WHEN unusual activity detected THEN the system SHALL flag for review

---

### Requirement 9: Caching & Performance

**User Story:** As a developer, I want Hyperliquid data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN market data is requested THEN the system SHALL cache for 5 seconds
2. WHEN order book is requested THEN the system SHALL NOT cache (real-time)
3. IF funding data is requested THEN the system SHALL cache for 30 seconds
4. WHEN position data is requested THEN the system SHALL cache for 10 seconds
5. IF Hyperliquid API is slow (>2s) THEN the system SHALL return cached with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `HyperliquidDataGateway` interface in domain layer
- **Infrastructure Adapter**: Enhanced `HyperliquidClient` implementing port
- **Application Interactors**: `GetMarkets`, `GetOrderBook`, `GetFundingRates`, `GetPositions`
- **HTTP Controllers**: REST endpoints under `/api/v1/defi/hyperliquid/`

### Performance

- **Market Data**: < 200ms response time
- **Order Book**: < 100ms response time (critical for trading)
- **Position Query**: < 500ms response time
- **Concurrent Requests**: Support 100+ concurrent requests

### Security

- **Read-Only by Default**: No trading operations server-side
- **Address Validation**: Validate Ethereum addresses
- **Rate Limiting**: Per-user limits to prevent abuse
- **No API Keys for Public Data**: Use public endpoints for market data

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry for transient failures

### Usability

- **Clear Errors**: Human-readable messages for all failures
- **Risk Warnings**: Prominent display of leverage/liquidation risks
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Existing Infrastructure

```
src/app/infrastructure/adapters/external/
├── hyperliquid_client.py              # Basic Hyperliquid API client ✅
└── instrumented/
    └── instrumented_hyperliquid_client.py  # Telemetry wrapper ✅
```

### Required New Components

```
src/app/domain/
├── entities/
│   └── perpetual_position.py    # Position entity
├── value_objects/
│   └── funding_rate.py          # Funding rate VO
└── ports/
    └── hyperliquid_gateway.py   # Port interface

src/app/application/
├── queries/
│   ├── get_perp_markets.py      # Market listing
│   ├── get_order_book.py        # Order book data
│   ├── get_funding_rates.py     # Funding analysis
│   └── get_perp_positions.py    # Position data
└── commands/
    └── calculate_position_risk.py  # Risk calculations

src/app/presentation/http/controllers/defi/
└── hyperliquid_router.py        # HTTP endpoints
```

---

## Dependencies

- **Existing**: `HyperliquidClient` in infrastructure layer
- **Hyperliquid API**: `https://api.hyperliquid.xyz`
- **Testnet**: `https://api.hyperliquid-testnet.xyz`

---

## Out of Scope

- Direct order placement (requires wallet signing)
- Account creation/deposits
- Leverage adjustment (requires auth)
- WebSocket streaming (future enhancement)
- Historical trade data beyond liquidations

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Market Data Latency | < 200ms (p95) |
| Order Book Freshness | < 1s staleness |
| Position Query Success | 99%+ success rate |
| Risk Calculation Accuracy | ±0.5% of actual liquidation |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API rate limiting | Medium | Medium | Request queuing, caching |
| Data staleness | Medium | High | Low TTL caching, refresh on read |
| Liquidation cascade | Low | High | Real-time monitoring, alerts |
| Hyperliquid L1 issues | Low | High | Circuit breaker, fallback data |
