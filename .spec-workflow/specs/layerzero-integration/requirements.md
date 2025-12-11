# Requirements Document: LayerZero Integration

## Introduction

This specification defines the requirements for completing the **LayerZero integration** into the Anvil Backend DeFi Multi-Agents Chat platform. LayerZero is a leading omnichain interoperability protocol enabling cross-chain messaging and token transfers across 50+ blockchains.

The existing `LayerZeroClient` infrastructure adapter provides basic API connectivity. This spec focuses on:
- **Full domain layer integration** (ports, entities, value objects)
- **Application layer interactors** for cross-chain tracking
- **HTTP API endpoints** for frontend consumption
- **Complementing LI.FI** for comprehensive cross-chain tracking

### Why LayerZero Matters

LayerZero powers major cross-chain applications:
- **Stargate Finance**: Leading bridge for stablecoins
- **OFT Standard**: Omnichain Fungible Tokens on 50+ chains
- **ONFT Standard**: Omnichain NFTs
- **$6B+ Total Messages**: Proven infrastructure

### Complementing LI.FI

| Capability | LI.FI | LayerZero |
|------------|-------|-----------|
| **Swap Routing** | ✅ Best routes | ❌ Not a router |
| **Message Tracking** | ❌ Limited | ✅ Full tracking |
| **OFT Transfers** | Uses LZ | ✅ Native tracking |
| **Protocol-Level Data** | Aggregated | ✅ Direct |

## Alignment with Product Vision

### Key Features Alignment

| Product Feature | LayerZero Integration |
|-----------------|-----------------------|
| **Cross-Chain Tracking** | Real-time message status |
| **Portfolio Visibility** | OFT holdings across chains |
| **Transaction History** | Complete cross-chain history |
| **Security Monitoring** | Message validation status |

### Business Objectives Alignment

- **User Trust**: Transparent cross-chain transaction tracking
- **Troubleshooting**: Debug stuck or failed messages
- **Analytics**: Cross-chain activity insights

---

## Requirements

### Requirement 1: Message Status Tracking

**User Story:** As a user, I want to track my cross-chain message status, so that I know when my transfer completes.

#### Acceptance Criteria

1. WHEN user provides source tx hash THEN the system SHALL return message status
2. WHEN status is returned THEN it SHALL include: status, source chain, destination chain
3. IF message is INFLIGHT THEN the system SHALL show estimated completion time
4. IF message is DELIVERED THEN the system SHALL show destination tx hash
5. IF message is FAILED THEN the system SHALL show error reason
6. IF message is BLOCKED THEN the system SHALL explain blocking reason

Status values: `INFLIGHT`, `DELIVERED`, `FAILED`, `BLOCKED`

---

### Requirement 2: Address Message History

**User Story:** As a user, I want to see all my cross-chain messages, so that I can review my activity history.

#### Acceptance Criteria

1. WHEN user provides wallet address THEN the system SHALL return message history
2. WHEN history is returned THEN it SHALL be sorted by timestamp (newest first)
3. IF filtering by chain THEN the system SHALL return only messages involving that chain
4. WHEN paginating THEN the system SHALL support cursor-based pagination
5. IF no messages found THEN the system SHALL return empty list with helpful message
6. WHEN displaying messages THEN the system SHALL categorize by type (OFT, ONFT, Generic)

---

### Requirement 3: Fee Estimation

**User Story:** As a user, I want to estimate cross-chain message fees before sending, so that I can budget appropriately.

#### Acceptance Criteria

1. WHEN user requests fee estimate THEN the system SHALL return native fee in source chain token
2. WHEN fee is returned THEN it SHALL include: native fee, USD equivalent
3. IF payload size is provided THEN fee estimate SHALL account for it
4. WHEN comparing chains THEN the system SHALL show fee differences
5. IF gas prices spike THEN the system SHALL show updated estimates
6. WHEN ZRO token payment is available THEN the system SHALL show alternative

---

### Requirement 4: OFT Transfer Tracking

**User Story:** As a user, I want to track my OFT token transfers specifically, so that I know when my tokens arrive.

#### Acceptance Criteria

1. WHEN user queries OFT transfers THEN the system SHALL return transfer history
2. WHEN transfer is returned THEN it SHALL include: token, amount, source/dest chains
3. IF transfer is pending THEN the system SHALL show progress percentage
4. WHEN transfer completes THEN the system SHALL show received amount
5. IF bridge fee was deducted THEN the system SHALL show fee breakdown
6. WHEN querying by token THEN the system SHALL filter by token address

---

### Requirement 5: Supported Chains Information

**User Story:** As a user, I want to see all LayerZero supported chains, so that I know where I can send messages.

#### Acceptance Criteria

1. WHEN user queries chains THEN the system SHALL return all supported chains
2. WHEN chain data is returned THEN it SHALL include: endpoint ID, name, native chain ID
3. IF chain has temporary issues THEN the system SHALL indicate degraded status
4. WHEN displaying chains THEN the system SHALL group by ecosystem (EVM, non-EVM)
5. IF new chain is added THEN the system SHALL update within 24 hours

Supported chains: Ethereum, Arbitrum, Optimism, Polygon, Base, Avalanche, BSC, Fantom, and 40+ more

---

### Requirement 6: Cross-Chain Analytics

**User Story:** As a user, I want to see analytics about my cross-chain activity, so that I can understand my usage patterns.

#### Acceptance Criteria

1. WHEN user queries analytics THEN the system SHALL return activity summary
2. WHEN summary is returned THEN it SHALL include: total messages, success rate, chains used
3. IF filtering by time period THEN the system SHALL support 7d, 30d, 90d, all-time
4. WHEN showing volume THEN the system SHALL aggregate USD value transferred
5. IF anomalies detected THEN the system SHALL flag unusual activity
6. WHEN comparing periods THEN the system SHALL show change percentages

---

### Requirement 7: Agent Integration

**User Story:** As a user chatting with Portfolio Agent, I want cross-chain transfer context, so that I understand my omnichain positions.

#### Acceptance Criteria

1. WHEN user asks about cross-chain transfers THEN agent SHALL query LayerZero
2. IF user has pending transfers THEN agent SHALL proactively mention status
3. WHEN user asks "where is my transfer" THEN agent SHALL track by recent tx
4. IF transfer failed THEN agent SHALL explain failure and suggest retry
5. WHEN discussing portfolio THEN agent SHALL consider cross-chain holdings
6. IF user asks about fees THEN agent SHALL provide LayerZero estimates

---

### Requirement 8: Real-Time Status Updates

**User Story:** As a user, I want real-time updates on my pending transfers, so that I don't have to manually refresh.

#### Acceptance Criteria

1. WHEN user subscribes to message THEN the system SHALL poll status periodically
2. WHEN status changes THEN the system SHALL notify user
3. IF message takes longer than expected THEN the system SHALL alert user
4. WHEN message completes THEN the system SHALL send completion notification
5. IF polling fails THEN the system SHALL retry with backoff
6. WHEN user unsubscribes THEN the system SHALL stop polling

---

### Requirement 9: Caching & Performance

**User Story:** As a developer, I want LayerZero data appropriately cached, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN message status is requested THEN the system SHALL cache for 10 seconds
2. WHEN chain data is requested THEN the system SHALL cache for 1 hour
3. IF message is DELIVERED THEN the system SHALL cache permanently
4. WHEN fee estimates are requested THEN the system SHALL cache for 30 seconds
5. IF LayerZero Scan API is slow THEN the system SHALL return cached with warning

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Domain Port**: `LayerZeroDataGateway` interface in domain layer
- **Infrastructure Adapter**: Enhanced `LayerZeroClient` implementing port
- **Application Interactors**: `TrackMessage`, `GetMessageHistory`, `EstimateFees`
- **HTTP Controllers**: REST endpoints under `/api/v1/defi/layerzero/`

### Performance

- **Message Status**: < 300ms response time
- **Message History**: < 500ms for 50 messages
- **Fee Estimation**: < 1s response time
- **Concurrent Requests**: Support 50+ concurrent requests

### Security

- **Read-Only**: No message sending server-side
- **Address Validation**: Validate wallet addresses
- **Rate Limiting**: Per-user limits to prevent abuse
- **No PII**: No personal information stored

### Reliability

- **Graceful Degradation**: Return cached data on API failure
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Automatic retry for transient failures

### Usability

- **Clear Status**: Human-readable status descriptions
- **Time Estimates**: Show expected completion times
- **Documentation**: OpenAPI spec for all endpoints

---

## Technical Context

### Existing Infrastructure

```
src/app/infrastructure/adapters/external/
├── layerzero_client.py    # Basic LayerZero Scan client ✅
```

### Required New Components

```
src/app/domain/
├── entities/
│   └── cross_chain_message.py   # Message entity
├── value_objects/
│   ├── message_status.py        # Status enum
│   └── layerzero_chain.py       # Chain value object
└── ports/
    └── layerzero_gateway.py     # Port interface

src/app/application/
├── queries/
│   ├── track_lz_message.py      # Message tracking
│   ├── get_lz_message_history.py  # History
│   ├── get_lz_chains.py         # Chain info
│   └── estimate_lz_fees.py      # Fee estimation

src/app/presentation/http/controllers/defi/
└── layerzero_router.py          # HTTP endpoints
```

---

## Dependencies

- **Existing**: `LayerZeroClient` in infrastructure layer
- **LayerZero Scan API**: `https://api-mainnet.layerzero-scan.com`
- **LI.FI Integration**: Complement for cross-chain operations

---

## Out of Scope

- Direct message sending (requires wallet interaction)
- OFT contract deployment
- DVN/Executor configuration
- WebSocket real-time streaming (future enhancement)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Message Tracking Latency | < 300ms (p95) |
| Status Accuracy | 100% match with on-chain |
| History Query Success | 99%+ success rate |
| Fee Estimation Accuracy | ±10% of actual |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LayerZero Scan API changes | Low | Medium | Version pinning, monitoring |
| Message stuck INFLIGHT | Medium | Medium | Timeout alerts, manual escalation |
| Rate limiting | Low | Medium | Request queuing, caching |
| DVN delays | Medium | Low | Clear time estimates, notifications |
