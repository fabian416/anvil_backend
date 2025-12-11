# Requirements Document: Axelar Network Integration

## Introduction

This specification defines the requirements for completing the **Axelar Network integration** into the Anvil Backend DeFi Multi-Agents Chat platform. Axelar is a decentralized cross-chain communication network enabling secure asset transfers and General Message Passing (GMP) across 50+ blockchains.

The existing `AxelarClient` infrastructure adapter provides basic API connectivity. This spec focuses on:
- **Full domain layer integration** (ports, entities, value objects)
- **Application layer interactors** for cross-chain bridging
- **HTTP API endpoints** for frontend consumption
- **Advanced GMP tracking** for complex cross-chain operations

### Why Axelar Matters

Axelar differentiates with enterprise-grade features:
- **General Message Passing (GMP)**: Execute smart contracts cross-chain
- **Proof-of-Stake Security**: Decentralized validator network
- **axlUSDC/axlWETH**: Native wrapped assets across chains
- **Cosmos IBC Gateway**: Connect EVM to Cosmos ecosystem
- **Express Service**: Fast finality for time-sensitive transfers

### Complementing LayerZero

| Capability | LayerZero | Axelar |
|------------|-----------|--------|
| **Protocol Type** | Message passing | Bridge + GMP |
| **Native Assets** | OFT tokens | axl-wrapped assets |
| **Cosmos Support** | Limited | ✅ Full IBC |
| **Express Mode** | ❌ | ✅ Fast finality |

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | Axelar Integration |
|-----------------|-------------------|
| **Cross-Chain Bridging** | Asset transfers with security |
| **GMP Tracking** | Complex cross-chain tx status |
| **Route Optimization** | Compare with LI.FI routes |
| **Cosmos Access** | Bridge to/from Cosmos chains |

### Business Objectives Alignment

- **User Trust**: Proven security with validator network
- **Cosmos Users**: Serve IBC-connected community
- **Enterprise**: Support complex GMP operations

---

## Requirements

### Requirement 1: Bridge Route Discovery

**User Story:** As a user, I want to see available Axelar bridge routes for my transfer, so that I can compare options.

#### Acceptance Criteria

1. WHEN user requests bridge routes THEN the system SHALL return available paths
2. WHEN routes are returned THEN they SHALL include: estimated time, fees, security score
3. IF express route available THEN the system SHALL show fast option with higher fee
4. IF standard route available THEN the system SHALL show normal finality option
5. WHEN comparing routes THEN the system SHALL indicate trade-offs (speed vs cost)
6. IF route is temporarily unavailable THEN the system SHALL indicate and suggest alternatives

---

### Requirement 2: Transfer Estimation

**User Story:** As a user, I want accurate transfer cost estimates, so that I can make informed bridging decisions.

#### Acceptance Criteria

1. WHEN user requests transfer estimate THEN the system SHALL return comprehensive costs
2. WHEN estimate is returned THEN it SHALL include: gas fee, relay fee, total USD cost
3. IF express service is used THEN the system SHALL show express premium
4. WHEN time estimate is shown THEN it SHALL differentiate standard vs express
5. IF destination gas price is high THEN the system SHALL warn user
6. WHEN comparing to LI.FI THEN the system SHALL indicate which offers better rate

---

### Requirement 3: Transfer Status Tracking

**User Story:** As a user, I want to track my Axelar transfer progress, so that I know when it completes.

#### Acceptance Criteria

1. WHEN user provides tx hash THEN the system SHALL return transfer status
2. WHEN status is returned THEN it SHALL include: status, source/dest chains, token, amount
3. IF status is PENDING THEN the system SHALL show confirmation progress
4. IF status is EXECUTING THEN the system SHALL show destination execution status
5. IF status is EXECUTED THEN the system SHALL return destination tx hash
6. IF status is FAILED THEN the system SHALL show error and recovery options

Status values: `PENDING`, `CONFIRMED`, `EXECUTING`, `EXECUTED`, `FAILED`

---

### Requirement 4: GMP Transaction Tracking

**User Story:** As a developer, I want to track General Message Passing transactions, so that I can monitor complex cross-chain operations.

#### Acceptance Criteria

1. WHEN GMP tx is submitted THEN the system SHALL track message relay progress
2. WHEN GMP status is returned THEN it SHALL include: call status, callback status
3. IF GMP includes multiple steps THEN the system SHALL track each step
4. IF GMP execution fails THEN the system SHALL show which step failed
5. WHEN gas payment is required THEN the system SHALL show payment status
6. IF express execution requested THEN the system SHALL track express relay

---

### Requirement 5: Supported Assets & Chains

**User Story:** As a user, I want to see all supported assets and chains, so that I know what transfers are possible.

#### Acceptance Criteria

1. WHEN user queries chains THEN the system SHALL return all supported chains
2. WHEN chain data is returned THEN it SHALL include: chain ID, name, supported tokens
3. IF querying tokens THEN the system SHALL return tokens for specific chain
4. WHEN displaying tokens THEN the system SHALL show decimals and addresses
5. IF chain has axl-wrapped assets THEN the system SHALL identify them
6. WHEN new chain/token is added THEN the system SHALL update within 24 hours

Supported chains: Ethereum, Polygon, Avalanche, Arbitrum, Optimism, Base, BSC, Fantom, Cosmos Hub, Osmosis, and more

---

### Requirement 6: Express Transfer Support

**User Story:** As a user who needs fast transfers, I want to use Axelar Express service, so that I get faster finality.

#### Acceptance Criteria

1. WHEN user requests express transfer THEN the system SHALL check availability
2. IF express is available THEN the system SHALL show express fee premium
3. WHEN express is used THEN completion time SHALL be significantly faster
4. IF express fails THEN transfer SHALL fall back to standard execution
5. WHEN displaying options THEN the system SHALL clearly differentiate express vs standard
6. IF express is unavailable for route THEN the system SHALL explain why

---

### Requirement 7: Agent Integration

**User Story:** As a user chatting with Trading Agent, I want Axelar bridge recommendations, so that I can efficiently move assets cross-chain.

#### Acceptance Criteria

1. WHEN user asks about bridging THEN agent SHALL consider Axelar routes
2. IF user needs fast transfer THEN agent SHALL recommend Express service
3. WHEN comparing bridges THEN agent SHALL consider Axelar security
4. IF user needs Cosmos access THEN agent SHALL prioritize Axelar
5. WHEN transfer is pending THEN agent SHALL provide status updates
6. IF transfer fails THEN agent SHALL explain failure and suggest retry

---

### Requirement 8: Fee Analysis

**User Story:** As a user, I want to understand Axelar fee breakdown, so that I can optimize my bridging costs.

#### Acceptance Criteria

1. WHEN fee breakdown is requested THEN the system SHALL itemize all fees
2. WHEN displaying fees THEN the system SHALL show: gas fee, relay fee, express fee
3. IF gas on destination is paid THEN the system SHALL show destination gas
4. WHEN comparing routes THEN the system SHALL calculate total cost difference
5. IF batch transfer is cheaper THEN the system SHALL suggest batching
6. WHEN fees are high THEN the system SHALL suggest waiting for lower gas

---

### Requirement 9: Caching & Performance

**User Story:** As a developer, I want Axelar data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN transfer status is requested THEN the system SHALL cache for 15 seconds
2. WHEN chain data is requested THEN the system SHALL cache for 1 hour
3. IF transfer is EXECUTED THEN the system SHALL cache permanently
4. WHEN fee estimates are requested THEN the system SHALL cache for 1 minute
5. IF Axelar API is slow THEN the system SHALL return cached with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `AxelarDataGateway` interface in domain layer
- **Infrastructure Adapter**: Enhanced `AxelarClient` implementing port
- **Application Interactors**: `GetBridgeRoutes`, `EstimateTransfer`, `TrackTransfer`
- **HTTP Controllers**: REST endpoints under `/api/v1/defi/axelar/`

### Performance

- **Route Discovery**: < 1s response time
- **Transfer Estimate**: < 1s response time
- **Status Tracking**: < 500ms response time
- **Concurrent Requests**: Support 50+ concurrent requests

### Security

- **Read-Only**: No bridging operations server-side
- **Address Validation**: Validate addresses for all chains
- **Rate Limiting**: Per-user limits to prevent abuse
- **Validator Monitoring**: Track validator set health

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry for transient failures
- **Express Fallback**: Fall back to standard if express fails

### Usability

- **Clear Status**: Human-readable status descriptions
- **Time Estimates**: Show expected completion times
- **Fee Transparency**: Clear breakdown of all costs
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Existing Infrastructure

```
src/app/infrastructure/adapters/external/
├── axelar_client.py    # Basic Axelar API client ✅
```

### Required New Components

```
src/app/domain/
├── entities/
│   └── axelar_transfer.py       # Transfer entity
├── value_objects/
│   ├── transfer_status.py       # Status enum
│   └── bridge_route.py          # Route value object
└── ports/
    └── axelar_gateway.py        # Port interface

src/app/application/
├── queries/
│   ├── get_axelar_routes.py     # Route discovery
│   ├── estimate_axelar_transfer.py  # Cost estimation
│   ├── track_axelar_transfer.py # Status tracking
│   └── get_axelar_chains.py     # Chain info

src/app/presentation/http/controllers/defi/
└── axelar_router.py             # HTTP endpoints
```

---

## Dependencies

- **Existing**: `AxelarClient` in infrastructure layer
- **Axelar Scan API**: `https://api.axelarscan.io`
- **GMP API**: `https://api.gmp.axelarscan.io`
- **LI.FI Integration**: Compare routes and fees

---

## Out of Scope

- Direct bridge transactions (requires wallet interaction)
- Validator staking operations
- IBC relayer management
- Satellite bridge (deprecated)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Route Discovery Latency | < 1s (p95) |
| Status Tracking Accuracy | 100% match with on-chain |
| Fee Estimation Accuracy | ±5% of actual |
| Express Availability | Track and report |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Axelar API changes | Low | Medium | Version pinning, monitoring |
| Transfer stuck | Medium | Medium | Timeout alerts, recovery guide |
| Express unavailable | Medium | Low | Clear fallback messaging |
| Validator issues | Low | High | Monitor validator set health |
