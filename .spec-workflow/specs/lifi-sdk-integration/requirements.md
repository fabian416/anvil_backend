# Requirements Document: LI.FI SDK Integration

## Introduction

This specification defines the requirements for integrating the **LI.FI SDK** (`libs/sdk`) into the Anvil Backend to provide **cross-chain swap and bridge functionality** for the DeFi Multi-Agents Chat platform. The LI.FI SDK enables seamless any-to-any cross-chain swaps across multiple blockchains (Ethereum, Arbitrum, Optimism, Base, Polygon, Bitcoin, Solana, Sui, etc.) through a unified API.

The integration will allow DeFi agents to:
- Get optimal swap/bridge routes across chains
- Provide real-time quotes for cross-chain transfers
- Execute transactions with user approval
- Track transaction status across bridges

## Alignment with Product Vision

This feature directly supports the goals outlined in `product.md`:

### Key Features Alignment

| Product Feature | LI.FI Integration |
|-----------------|-------------------|
| **Multi-Chain Support** | LI.FI supports 20+ chains including EVM, Bitcoin, Solana, Sui |
| **Real-Time DeFi Data** | Live quotes, gas estimates, slippage calculations |
| **Transaction Guidance** | Step-by-step execution with status tracking |
| **Portfolio Integration** | Token balances across all supported chains |

### Business Objectives Alignment

- **User Engagement**: Enable cross-chain operations directly from chat interface
- **Retention**: Provide best-rate discovery across all bridges/DEXs
- **Market Position**: Differentiate as the first chat-based cross-chain swap interface

---

## Requirements

### Requirement 1: SDK Configuration & Initialization

**User Story:** As a developer, I want the LI.FI SDK properly configured with the Anvil integrator ID, so that API calls are tracked and rate limits are managed.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL initialize LI.FI SDK with integrator configuration
2. IF custom RPC endpoints are configured THEN the system SHALL use them instead of defaults
3. WHEN SDK is initialized THEN it SHALL support all chain providers (Ethereum, Bitcoin, Solana, Sui)
4. IF initialization fails THEN the system SHALL log error and fall back to degraded mode
5. WHEN running in test environment THEN the system SHALL use mock responses

---

### Requirement 2: Cross-Chain Quote Retrieval

**User Story:** As a user, I want to get the best swap/bridge quote for transferring tokens across chains, so that I can make informed decisions.

#### Acceptance Criteria

1. WHEN user requests a quote THEN the system SHALL return the best route with estimated output
2. WHEN quote is requested THEN the system SHALL include gas estimates for all steps
3. IF multiple routes exist THEN the system SHALL return sorted by best output amount
4. WHEN quote includes bridge THEN the system SHALL show estimated time to completion
5. IF tokens or chains are not supported THEN the system SHALL return clear error message
6. WHEN slippage is specified THEN the system SHALL calculate minimum output amount

---

### Requirement 3: Route Discovery

**User Story:** As a user, I want to see all available routes for my transfer, so that I can choose based on speed, cost, or security preferences.

#### Acceptance Criteria

1. WHEN user requests routes THEN the system SHALL return all viable options
2. WHEN routes are returned THEN each SHALL include: bridges/DEXs used, steps, fees, estimated time
3. IF user specifies preferences (fastest, cheapest) THEN routes SHALL be sorted accordingly
4. WHEN routes include multiple steps THEN the system SHALL show intermediate tokens
5. IF no routes available THEN the system SHALL suggest alternatives (different token pairs)

---

### Requirement 4: Token & Chain Information

**User Story:** As a user, I want to see supported tokens and chains, so that I know what transfers are possible.

#### Acceptance Criteria

1. WHEN user queries supported chains THEN the system SHALL return all active chains with metadata
2. WHEN user queries tokens THEN the system SHALL return tokens with addresses, decimals, logos
3. IF user requests token balance THEN the system SHALL query on-chain balance
4. WHEN displaying chain info THEN the system SHALL include native token and RPC status
5. IF chain is temporarily unavailable THEN the system SHALL indicate degraded status

---

### Requirement 5: Transaction Execution Support

**User Story:** As a user, I want to execute approved transactions through the chat interface, so that I can complete swaps seamlessly.

#### Acceptance Criteria

1. WHEN user approves a route THEN the system SHALL generate transaction data for each step
2. IF token approval is needed THEN the system SHALL generate approval transaction first
3. WHEN transaction is submitted THEN the system SHALL return transaction hash
4. IF transaction requires gas THEN the system SHALL estimate and include gas parameters
5. WHEN using permits (EIP-2612) THEN the system SHALL support gasless approvals

---

### Requirement 6: Transaction Status Tracking

**User Story:** As a user, I want to track my cross-chain transfer status, so that I know when it completes.

#### Acceptance Criteria

1. WHEN transaction is submitted THEN the system SHALL provide status polling endpoint
2. WHEN status is queried THEN it SHALL return: pending, in-progress, completed, failed
3. IF bridge is involved THEN status SHALL include source and destination chain confirmations
4. WHEN transaction completes THEN the system SHALL return final output amount received
5. IF transaction fails THEN the system SHALL return error reason and recovery options

---

### Requirement 7: Agent Integration

**User Story:** As a Trading Agent, I want to use LI.FI data to recommend optimal swaps, so that users get the best rates.

#### Acceptance Criteria

1. WHEN Trading Agent is asked about swaps THEN it SHALL use LI.FI quote API
2. WHEN Portfolio Agent analyzes holdings THEN it SHALL use token balance APIs
3. IF user asks to compare routes THEN the agent SHALL present options clearly
4. WHEN recommending a swap THEN the agent SHALL include fee breakdown and risks
5. IF better rate exists on different path THEN the agent SHALL suggest it

---

### Requirement 8: Caching & Performance

**User Story:** As a developer, I want quote and chain data cached appropriately, so that the system remains responsive.

#### Acceptance Criteria

1. WHEN chain data is requested THEN the system SHALL cache for 1 hour
2. WHEN token lists are requested THEN the system SHALL cache for 15 minutes
3. IF quote is older than 30 seconds THEN the system SHALL refresh automatically
4. WHEN cache expires THEN the system SHALL refresh in background (stale-while-revalidate)
5. IF LI.FI API is slow THEN the system SHALL return cached data with staleness indicator

---

### Requirement 9: Error Handling & Resilience

**User Story:** As a user, I want clear error messages when something goes wrong, so that I can take appropriate action.

#### Acceptance Criteria

1. IF LI.FI API returns error THEN the system SHALL translate to user-friendly message
2. WHEN rate limit is hit THEN the system SHALL queue request with exponential backoff
3. IF specific bridge is unavailable THEN the system SHALL exclude from routes
4. WHEN transaction simulation fails THEN the system SHALL explain why
5. IF network error occurs THEN the system SHALL retry with configurable policy

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility**: LI.FI adapter separate from domain logic
- **Port/Adapter Pattern**: Domain defines port, infrastructure implements adapter
- **Service Isolation**: SDK wrapper independent of chat/agent logic
- **Clear Interfaces**: Typed request/response models for all operations

### Performance

- **Quote Latency**: < 2 seconds for single-chain swaps
- **Route Discovery**: < 5 seconds for cross-chain routes
- **Status Polling**: Support polling every 5 seconds without rate limits
- **Concurrent Requests**: Support 100+ concurrent quote requests

### Security

- **No Private Keys**: SDK never handles or stores private keys
- **Transaction Signing**: Handled client-side, backend receives signed tx
- **Rate Limiting**: Per-user rate limits to prevent abuse
- **Input Validation**: Validate all addresses, amounts, chain IDs

### Reliability

- **Graceful Degradation**: Fall back to cached data if API unavailable
- **Circuit Breaker**: Prevent cascading failures on LI.FI outage
- **Retry Logic**: Automatic retry with exponential backoff
- **Monitoring**: Track API latency, error rates, cache hit rates

### Usability

- **Clear Errors**: Human-readable error messages for all failure modes
- **Progress Feedback**: Real-time updates on multi-step transactions
- **Documentation**: OpenAPI spec for all exposed endpoints

---

## Technical Context

### LI.FI SDK Package Structure

```
libs/sdk/packages/
├── sdk/                      # Core SDK
│   └── src/
│       ├── actions/          # API actions (getQuote, getRoutes, etc.)
│       ├── client/           # HTTP client
│       ├── core/             # Configuration, types
│       └── errors/           # Error handling
├── sdk-provider-ethereum/    # EVM chain support
├── sdk-provider-bitcoin/     # Bitcoin support
├── sdk-provider-solana/      # Solana support
└── sdk-provider-sui/         # Sui support
```

### Key SDK Functions to Integrate

| Function | Purpose |
|----------|---------|
| `createConfig` | Initialize SDK with integrator ID |
| `getQuote` | Get single best quote |
| `getRoutes` | Get all available routes |
| `getChains` | List supported chains |
| `getTokens` | List tokens for chain |
| `getTokenBalance` | Get user token balance |
| `getStatus` | Get transaction status |
| `getStepTransaction` | Get transaction data for step |

---

## Dependencies

- **LI.FI SDK**: `@lifi/sdk` v4.0.0-alpha.5 (TypeScript)
- **Viem**: v2.41.2 (Ethereum interactions)
- **Backend Bridge**: Python wrapper calling Node.js SDK or REST API fallback

---

## Out of Scope

- Direct transaction signing (handled by frontend/wallet)
- Wallet connection management
- Fiat on-ramp integration
- NFT bridging
- MEV protection implementation

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Quote Response Time | < 2s (p95) |
| Route Discovery Time | < 5s (p95) |
| API Availability | 99.9% |
| Cache Hit Rate | > 70% for chain/token data |
| User Satisfaction | 90%+ successful swaps |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LI.FI API downtime | Low | High | Cache + fallback to direct DEX calls |
| Rate limiting | Medium | Medium | Request queuing, user-level limits |
| Bridge delays | Medium | Low | Clear time estimates, status updates |
| Price slippage | Medium | Medium | Real-time quotes, slippage protection |
| TypeScript/Python bridge complexity | High | Medium | Use LI.FI REST API as fallback |
