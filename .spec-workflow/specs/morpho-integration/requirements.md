# Requirements Document: Morpho Protocol Integration

## Introduction

This specification defines the requirements for integrating **Morpho Protocol** into the Anvil Backend DeFi Multi-Agents Chat platform. Morpho is a leading decentralized lending protocol that optimizes capital efficiency through innovative vault-based lending, providing higher yields for lenders and lower rates for borrowers compared to traditional lending pools.

This is a **new integration** requiring development from scratch:
- **Infrastructure adapter** for Morpho API/subgraph
- **Domain layer** (ports, entities, value objects)
- **Application layer interactors** for vault operations
- **HTTP API endpoints** for frontend consumption
- **Yield Agent integration** for optimized lending recommendations

### Why Morpho Matters

Morpho has emerged as a leader in DeFi lending innovation:
- **$3B+ TVL**: Rapid growth in 2024-2025
- **MetaMorpho Vaults**: Curated lending vaults with optimized strategies
- **Morpho Blue**: Permissionless lending markets
- **Higher Yields**: ~2-3% higher APY than Aave/Compound on average
- **Risk-Adjusted**: Professional risk management in curated vaults

### Morpho Architecture

| Component | Description |
|-----------|-------------|
| **Morpho Blue** | Core permissionless lending protocol |
| **MetaMorpho** | Vault layer for curated lending strategies |
| **Morpho Optimizers** | Legacy Aave/Compound optimizers |
| **Morpho DAO** | Governance and MORPHO token |

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | Morpho Integration |
|-----------------|-------------------|
| **Yield Optimization** | Best lending rates via vaults |
| **Portfolio Analysis** | Vault positions and earnings |
| **Risk Assessment** | Vault risk profiles and exposure |
| **Strategy Discovery** | Find optimal lending vaults |

### Business Objectives Alignment

- **Yield Seekers**: Surface best lending opportunities
- **Risk-Aware**: Clear vault risk profiles
- **DeFi-Native**: Integrate leading lending innovation

---

## Requirements

### Requirement 1: Vault Discovery & Listing

**User Story:** As a user, I want to discover available Morpho vaults with their yields and risk profiles, so that I can find suitable lending opportunities.

#### Acceptance Criteria

1. WHEN user queries vaults THEN the system SHALL return all MetaMorpho vaults
2. WHEN vault data is returned THEN it SHALL include: name, asset, APY, TVL, risk tier
3. IF filtering by asset THEN the system SHALL return only vaults for that asset
4. WHEN displaying APY THEN the system SHALL show net APY after fees
5. IF vault has multiple markets THEN the system SHALL show market allocation
6. WHEN sorting vaults THEN the system SHALL support sort by APY, TVL, risk
7. IF vault is deprecated THEN the system SHALL indicate and suggest alternatives

---

### Requirement 2: Vault Details & Strategy

**User Story:** As a user, I want to understand a vault's strategy and risk exposure, so that I can make informed deposit decisions.

#### Acceptance Criteria

1. WHEN user queries vault details THEN the system SHALL return comprehensive info
2. WHEN details are returned THEN they SHALL include: curator, strategy, markets, allocations
3. IF vault has performance fee THEN the system SHALL show fee percentage
4. WHEN displaying markets THEN the system SHALL show each market's allocation %
5. IF vault has idle funds THEN the system SHALL show unallocated percentage
6. WHEN showing history THEN the system SHALL include APY trend (7d, 30d)
7. IF vault has withdrawal queue THEN the system SHALL indicate and show position

---

### Requirement 3: APY & Performance Tracking

**User Story:** As a user, I want to see vault APY history and performance metrics, so that I can assess consistency.

#### Acceptance Criteria

1. WHEN user queries vault APY THEN the system SHALL return current and historical
2. WHEN APY data is returned THEN it SHALL include: current, 7d avg, 30d avg
3. IF APY has been volatile THEN the system SHALL show standard deviation
4. WHEN comparing vaults THEN the system SHALL show relative performance
5. IF APY drops significantly THEN the system SHALL flag for attention
6. WHEN showing sources THEN the system SHALL break down APY by market

---

### Requirement 4: Market Data (Morpho Blue)

**User Story:** As a user, I want to see individual Morpho Blue market data, so that I can understand where vaults are lending.

#### Acceptance Criteria

1. WHEN user queries markets THEN the system SHALL return Morpho Blue markets
2. WHEN market data is returned THEN it SHALL include: collateral, loan, LLTV, APY
3. IF market has high utilization THEN the system SHALL show current rate
4. WHEN displaying risk THEN the system SHALL show liquidation parameters
5. IF market is oracle-based THEN the system SHALL show oracle source
6. WHEN querying specific market THEN the system SHALL show total supplied/borrowed

---

### Requirement 5: User Position Tracking

**User Story:** As a user, I want to see my Morpho vault positions, so that I can track my earnings.

#### Acceptance Criteria

1. WHEN user provides wallet address THEN the system SHALL return vault positions
2. WHEN position data is returned THEN it SHALL include: vault, shares, value, earnings
3. IF position has unrealized gains THEN the system SHALL show profit/loss
4. WHEN showing earnings THEN the system SHALL calculate since deposit
5. IF user has multiple positions THEN the system SHALL aggregate total
6. WHEN displaying value THEN the system SHALL show in underlying asset and USD

---

### Requirement 6: Vault Risk Assessment

**User Story:** As a user, I want to understand vault risks, so that I can match my risk tolerance.

#### Acceptance Criteria

1. WHEN user queries vault risk THEN the system SHALL return risk profile
2. WHEN risk data is returned THEN it SHALL include: risk tier, exposure breakdown
3. IF vault has concentration risk THEN the system SHALL warn user
4. WHEN showing collateral exposure THEN the system SHALL list collateral assets
5. IF vault uses volatile collateral THEN the system SHALL indicate higher risk
6. WHEN comparing vaults THEN the system SHALL rank by risk-adjusted return

Risk tiers: `Conservative`, `Moderate`, `Aggressive`

---

### Requirement 7: Agent Integration

**User Story:** As a user chatting with Yield Agent, I want intelligent vault recommendations, so that I can optimize my lending.

#### Acceptance Criteria

1. WHEN user asks about lending yields THEN agent SHALL query Morpho vaults
2. IF user has stablecoins THEN agent SHALL prioritize stable-asset vaults
3. WHEN recommending vaults THEN agent SHALL consider user's risk profile
4. IF better yield exists THEN agent SHALL suggest vault optimization
5. WHEN user asks "where to earn" THEN agent SHALL compare Morpho vs Aave
6. IF vault strategy changes THEN agent SHALL notify user proactively

---

### Requirement 8: Comparison with Other Protocols

**User Story:** As a user, I want to compare Morpho rates with other lending protocols, so that I can find the best yield.

#### Acceptance Criteria

1. WHEN user requests comparison THEN the system SHALL show Morpho vs others
2. WHEN comparing THEN the system SHALL include: Aave, Compound, Morpho Blue
3. IF Morpho has better rate THEN the system SHALL highlight the difference
4. WHEN showing rates THEN the system SHALL ensure same-asset comparison
5. IF risk differs THEN the system SHALL indicate risk-return trade-off
6. WHEN calculating benefit THEN the system SHALL show annual extra yield

---

### Requirement 9: Caching & Performance

**User Story:** As a developer, I want Morpho data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN vault list is requested THEN the system SHALL cache for 5 minutes
2. WHEN APY data is requested THEN the system SHALL cache for 1 minute
3. IF user position is requested THEN the system SHALL cache for 30 seconds
4. WHEN market data is requested THEN the system SHALL cache for 2 minutes
5. IF Morpho API is slow THEN the system SHALL return cached with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `MorphoDataGateway` interface in domain layer
- **Infrastructure Adapter**: New `MorphoClient` implementing port
- **Application Interactors**: `GetMorphoVaults`, `GetVaultDetails`, `GetUserPositions`
- **HTTP Controllers**: REST endpoints under `/api/v1/defi/morpho/`

### Performance

- **Vault List**: < 500ms response time (cached)
- **Vault Details**: < 1s response time
- **User Positions**: < 1s response time
- **Concurrent Requests**: Support 50+ concurrent requests

### Security

- **Read-Only**: No deposit/withdrawal operations server-side
- **Address Validation**: Validate wallet addresses
- **Rate Limiting**: Per-user limits to prevent abuse
- **No Private Keys**: Never handle user keys

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry for transient failures
- **Subgraph Fallback**: Use alternative data source if primary fails

### Usability

- **Clear Yields**: Show net APY after all fees
- **Risk Clarity**: Clear risk tier communication
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Required New Components

```
src/app/infrastructure/adapters/external/
├── morpho_client.py                 # Morpho API client (NEW)
└── instrumented/
    └── instrumented_morpho_client.py   # Telemetry wrapper

src/app/domain/
├── entities/
│   ├── morpho_vault.py              # Vault entity
│   └── morpho_position.py           # Position entity
├── value_objects/
│   ├── vault_apy.py                 # APY value object
│   └── risk_tier.py                 # Risk tier enum
└── ports/
    └── morpho_gateway.py            # Port interface

src/app/application/
├── queries/
│   ├── get_morpho_vaults.py         # Vault listing
│   ├── get_morpho_vault_details.py  # Vault details
│   ├── get_morpho_markets.py        # Blue markets
│   ├── get_morpho_positions.py      # User positions
│   └── compare_lending_yields.py    # Protocol comparison
└── commands/
    └── analyze_vault_risk.py        # Risk analysis

src/app/presentation/http/controllers/defi/
└── morpho_router.py                 # HTTP endpoints
```

### Data Sources

| Source | Data | Latency |
|--------|------|---------|
| **Morpho API** | Vaults, APYs, positions | Real-time |
| **Morpho Subgraph** | Historical data, events | ~30s delay |
| **DeFiLlama** | TVL verification | Real-time |
| **On-chain** | Exact balances (fallback) | Block time |

### API Endpoints (Morpho)

```
# MetaMorpho Vaults API
GET /api/vaults - List vaults
GET /api/vaults/{address} - Vault details
GET /api/vaults/{address}/apy-history - APY history

# Morpho Blue API
GET /api/markets - List markets
GET /api/markets/{id} - Market details

# User Data
GET /api/users/{address}/positions - User positions
```

---

## Dependencies

- **New Development**: `MorphoClient` infrastructure adapter
- **Morpho API**: TBD (check latest documentation)
- **TheGraph Subgraph**: Morpho Blue subgraph
- **DeFiLlama API**: TVL verification

---

## Out of Scope

- Vault deposits/withdrawals (requires wallet interaction)
- Morpho Blue direct lending (requires smart contract calls)
- MORPHO token staking
- Governance participation
- Liquidation operations

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Vault List Latency | < 500ms (p95) |
| APY Data Freshness | < 1 min staleness |
| Position Accuracy | 100% match with on-chain |
| Yield Comparison Coverage | Morpho vs top 3 protocols |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No official API | Medium | High | Use subgraph + on-chain calls |
| APY calculation complexity | Medium | Medium | Follow Morpho's methodology |
| Vault strategy changes | Medium | Low | Regular data refresh, alerts |
| Smart contract risk | Low | High | Display audits, risk tiers |

---

## Research Notes

### Morpho Blue Markets

Morpho Blue uses isolated lending markets with:
- **LLTV**: Liquidation Loan-To-Value (e.g., 86% for WETH/USDC)
- **Oracle**: Price feed for collateral valuation
- **IRM**: Interest Rate Model determining rates

### MetaMorpho Vault Structure

```
Vault
├── Underlying Asset (e.g., USDC)
├── Curator (risk manager)
├── Market Allocations
│   ├── Market 1: 40% → WETH collateral @ 86% LLTV
│   ├── Market 2: 35% → wstETH collateral @ 90% LLTV
│   └── Market 3: 25% → sDAI collateral @ 96% LLTV
├── Performance Fee (e.g., 15%)
└── Queue (for withdrawals during high utilization)
```

### Competitive Comparison

| Protocol | ETH Lending APY | USDC Lending APY |
|----------|-----------------|------------------|
| Aave v3 | ~2.5% | ~4% |
| Compound v3 | ~2.3% | ~3.8% |
| Morpho Blue | ~3.5% | ~5.5% |

*Rates are illustrative and vary with market conditions*
