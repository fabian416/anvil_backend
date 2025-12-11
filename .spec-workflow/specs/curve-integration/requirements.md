# Requirements Document: Curve Finance Integration

## Introduction

This specification defines the requirements for completing the **Curve Finance integration** into the Anvil Backend DeFi Multi-Agents Chat platform. Curve is the leading decentralized exchange optimized for stablecoin swaps with low slippage and efficient liquidity provision.

The existing `CurveClient` infrastructure adapter provides basic API connectivity. This spec focuses on:
- **Full domain layer integration** (ports, entities, value objects)
- **Application layer interactors** for stablecoin operations
- **HTTP API endpoints** for frontend consumption
- **Agent integration** for intelligent stablecoin recommendations

### Why Curve Matters

Curve handles ~70% of on-chain stablecoin trading volume. Key features:
- **StableSwap AMM**: Ultra-low slippage for like-kind assets (USDC↔USDT↔DAI)
- **Gauge System**: CRV rewards for liquidity providers
- **veCRV**: Vote-escrow mechanics for governance and boosted yields
- **Multi-chain**: Available on Ethereum, Arbitrum, Optimism, Polygon, Base

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | Curve Integration |
|-----------------|-------------------|
| **Stablecoin Operations** | Best rates for stable-to-stable swaps |
| **Yield Optimization** | APY tracking for Curve pools and gauges |
| **Portfolio Analysis** | LP position value and reward tracking |
| **Risk Assessment** | Depeg risk monitoring for stablecoins |

### Business Objectives Alignment

- **User Engagement**: Enable optimal stablecoin swaps from chat
- **Yield Hunters**: Surface best Curve pool opportunities
- **Safety Focus**: Monitor stablecoin depegs and pool health

---

## Requirements

### Requirement 1: Pool Data Retrieval

**User Story:** As a user, I want to see all Curve pools with current TVL, APY, and composition, so that I can identify yield opportunities.

#### Acceptance Criteria

1. WHEN user queries Curve pools THEN the system SHALL return pools sorted by TVL
2. WHEN pool data is returned THEN it SHALL include: name, tokens, TVL, base APY, reward APY
3. IF user filters by chain THEN the system SHALL return only pools on that chain
4. WHEN pool has gauge THEN the system SHALL include CRV reward APY
5. IF pool has additional rewards THEN the system SHALL show breakdown by token
6. WHEN displaying APY THEN the system SHALL show boosted APY range (1x to 2.5x)

---

### Requirement 2: Stablecoin Swap Quotes

**User Story:** As a user, I want to get the best swap quote for stablecoin exchanges, so that I minimize slippage and fees.

#### Acceptance Criteria

1. WHEN user requests stablecoin swap quote THEN the system SHALL return expected output
2. WHEN quote is returned THEN it SHALL include: output amount, price impact, fees
3. IF swap amount is large (>$100k) THEN the system SHALL warn about slippage
4. WHEN multiple pools can fulfill swap THEN the system SHALL route through best one
5. IF stablecoin is depegged (>0.5% from peg) THEN the system SHALL show warning
6. WHEN comparing to other DEXs THEN the system SHALL indicate if Curve has best rate

---

### Requirement 3: Gauge & Reward Data

**User Story:** As a yield farmer, I want to see gauge rewards and veCRV boost information, so that I can maximize my yields.

#### Acceptance Criteria

1. WHEN user queries gauge data THEN the system SHALL return all active gauges
2. WHEN gauge data is returned THEN it SHALL include: CRV emissions, relative weight, TVL
3. IF user has veCRV THEN the system SHALL calculate their boost multiplier
4. WHEN displaying rewards THEN the system SHALL show annual CRV reward in USD
5. IF gauge weight is low (<0.1%) THEN the system SHALL indicate low emissions
6. WHEN new gauge votes occur THEN the system SHALL update weights within 1 hour

---

### Requirement 4: Pool APY Breakdown

**User Story:** As a user, I want to understand the APY composition of Curve pools, so that I can assess sustainability of yields.

#### Acceptance Criteria

1. WHEN user requests pool APY THEN the system SHALL return full breakdown
2. WHEN APY is shown THEN it SHALL separate: base (fees), CRV rewards, extra rewards
3. IF pool is Factory pool THEN the system SHALL indicate community-deployed
4. WHEN showing boosted APY THEN the system SHALL explain veCRV requirements
5. IF historical APY data exists THEN the system SHALL show 7-day and 30-day averages

---

### Requirement 5: TVL & Volume Analytics

**User Story:** As a user, I want to see Curve's TVL and volume trends, so that I can assess protocol health.

#### Acceptance Criteria

1. WHEN user queries Curve TVL THEN the system SHALL return total and per-chain breakdown
2. WHEN TVL is shown THEN it SHALL include 24h change percentage
3. IF user queries volume THEN the system SHALL show 24h trading volume per pool
4. WHEN comparing pools THEN the system SHALL rank by volume/TVL ratio (utilization)
5. IF TVL drops significantly (>10% in 24h) THEN the system SHALL flag for review

---

### Requirement 6: Agent Integration

**User Story:** As a user chatting with Trading Agent, I want intelligent stablecoin swap recommendations, so that I get optimal execution.

#### Acceptance Criteria

1. WHEN user asks "swap USDC to DAI" THEN Trading Agent SHALL query Curve for quote
2. IF Curve has better rate than 1inch THEN agent SHALL recommend Curve
3. WHEN user asks about stablecoin yields THEN agent SHALL surface top Curve pools
4. IF user mentions "low slippage" THEN agent SHALL prioritize Curve recommendations
5. WHEN large swap is requested THEN agent SHALL warn about price impact
6. IF depeg risk exists THEN agent SHALL include warning in recommendation

---

### Requirement 7: Multi-Chain Support

**User Story:** As a user, I want to query Curve data across all supported chains, so that I can find opportunities anywhere.

#### Acceptance Criteria

1. WHEN user doesn't specify chain THEN the system SHALL query Ethereum by default
2. IF user specifies chain THEN the system SHALL query that chain's Curve deployment
3. WHEN displaying results THEN the system SHALL include chain identifier
4. IF chain is not supported THEN the system SHALL return helpful error message
5. WHEN aggregating cross-chain THEN the system SHALL convert all values to USD

Supported chains: Ethereum, Arbitrum, Optimism, Polygon, Base, Avalanche, Fantom

---

### Requirement 8: Caching & Performance

**User Story:** As a developer, I want Curve data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN pool list is requested THEN the system SHALL cache for 5 minutes
2. WHEN APY data is requested THEN the system SHALL cache for 1 minute
3. IF swap quote is older than 15 seconds THEN the system SHALL refresh
4. WHEN gauge data is requested THEN the system SHALL cache for 10 minutes
5. IF Curve API is slow (>3s) THEN the system SHALL return cached data with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `CurveDataGateway` interface in domain layer
- **Infrastructure Adapter**: Enhanced `CurveClient` implementing port
- **Application Interactors**: `GetCurvePools`, `GetSwapQuote`, `GetGaugeData`
- **HTTP Controllers**: REST endpoints under `/api/v1/defi/curve/`

### Performance

- **Pool List**: < 500ms response time (cached)
- **Swap Quote**: < 1s response time
- **APY Calculation**: < 2s for full breakdown
- **Concurrent Requests**: Support 50+ concurrent requests

### Security

- **No Private Keys**: Read-only data queries
- **Rate Limiting**: Per-user limits to prevent abuse
- **Input Validation**: Validate pool addresses, token addresses, amounts

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry with exponential backoff

### Usability

- **Clear Errors**: Human-readable messages for all failures
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Existing Infrastructure

```
src/app/infrastructure/adapters/external/
├── curve_client.py              # Basic Curve API client ✅
└── instrumented/
    └── instrumented_curve_client.py  # Telemetry wrapper ✅
```

### Required New Components

```
src/app/domain/ports/
└── curve_gateway.py             # Port interface

src/app/application/
├── queries/
│   ├── get_curve_pools.py       # Pool listing
│   ├── get_curve_pool_apy.py    # APY breakdown
│   └── get_curve_gauges.py      # Gauge data
└── commands/
    └── get_curve_swap_quote.py  # Swap quoting

src/app/presentation/http/controllers/defi/
└── curve_router.py              # HTTP endpoints
```

---

## Dependencies

- **Existing**: `CurveClient` in infrastructure layer
- **Curve API**: `https://api.curve.finance/v1`
- **Multi-chain**: Chain-specific endpoints per network

---

## Out of Scope

- Direct LP deposits/withdrawals (requires wallet interaction)
- veCRV locking/voting (governance operations)
- Gauge voting (complex multi-step process)
- Convex/Yearn integration (separate spec)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Pool Data Response Time | < 500ms (p95) |
| Swap Quote Accuracy | ±0.1% of actual execution |
| Cache Hit Rate | > 80% for pool data |
| Agent Recommendation Accuracy | 90%+ best rate |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Curve API changes | Low | Medium | Version pinning, fallback endpoints |
| Stablecoin depeg | Medium | High | Real-time monitoring, warnings |
| High gas costs | Medium | Low | Gas estimation, user warnings |
| Rate limiting | Low | Medium | Request queuing, caching |
