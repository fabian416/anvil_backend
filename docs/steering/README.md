# Steering Documents

**Purpose**: High-level project steering documentation for product, technology, and structure decisions  
**Audience**: CPO, CEO, CTO, Engineering Leadership  
**Last Updated**: January 2, 2026

---

## 📚 Documents

### [Product Vision](./product.md)

Product strategy, target users, and roadmap priorities.

- Vision statement and product pillars
- Target user segments
- Product tiers and pricing strategy
- Key differentiators
- Success metrics
- Roadmap priorities

### [Technical Stack](./tech.md)

Technology choices, architecture patterns, and implementation details.

- Core technology stack
- Architecture patterns (Hexagonal, CQRS)
- LLM provider configuration
- MCP server architecture
- Database schema overview
- Security configuration
- Development workflow

### [Project Structure](./structure.md)

Codebase organization and conventions.

- Directory overview
- Domain module structure
- Application layer patterns
- Infrastructure adapters
- Presentation controllers
- Dependency injection setup
- Testing structure
- File naming conventions

### [Authentication & Authorization](./authentication.md)

Complete authentication system documentation.

- Privy integration (Web3-native auth)
- Traditional authentication (email/password)
- JWT token system
- Session management
- Role-Based Access Control (RBAC)
- Admin system and Super Admin
- Security features

### [Wallet SDK Integration](./wallet-sdk-integration.md)

Comprehensive wallet management documentation.

- Multi-chain support (Ethereum, Solana, Bitcoin, L2s)
- Privy SDK integration
- Wallet types (Embedded, External, Imported)
- Provider abstraction (Port-Adapter pattern)
- Wallet source modes (Privy, Hybrid, Local)
- Private key export (HPKE encryption)
- Bitcoin wallet creation and transactions
- Frontend integration guide

### [Wallet Data Model](./wallet-data-model.md)

Complete wallet database schema and entity documentation.

- Entity Relationship Diagram
- Wallet, Transaction, Policy entities
- Database schema (PostgreSQL)
- Enumerations (Provider, Status, ChainType, TransactionType)
- Repository interfaces with CRUD and analytics
- Value Objects (WalletId, TransactionId, AdditionalSigner)
- Data flow examples
- Analytics queries

### [Balance Data Model](./balance-data-model.md)

Complete balance and position data model documentation.

- Portfolio Snapshots (point-in-time wallet captures)
- Token Holdings (native + ERC-20 with USD values)
- Chain Addresses (multi-chain balance tracking)
- Earn Positions (yield farming, staking)
- Hyperliquid Positions (perpetual futures)
- DeFi Positions (Aave, Morpho, Compound - external APIs)
- Database schema (PostgreSQL)
- Repository interfaces
- Analytics and health factor monitoring

### [Transaction Data Model](./transaction-data-model.md)

Complete transaction logging and confirmation documentation.

- Transaction entity with DEX/swap support
- Multi-chain support (Ethereum, L2s, Bitcoin)
- Dual transaction records (sender + receiver views)
- Transaction types (SEND, SWAP, APPROVE, EARN, etc.)
- Celery worker for on-chain confirmation
- Block explorer URL generation
- Repository interface with 25+ methods
- Volume and user activity analytics
- API endpoints (user + admin)
- Data flow diagrams

### [1inch Integration](./oneinch-integration.md)

Complete 1inch DEX aggregator integration documentation.

- Architecture overview (client stack)
- Base, Cached, and Instrumented clients
- MCP Server for AI agents (port 8082)
- API methods (quotes, swaps, tokens, prices)
- Multi-chain support (9 chains)
- Redis caching strategy with TTLs
- Telemetry and distributed tracing
- Rate limiting (1 req/sec free, 10 req/sec paid)
- Integration points (SwapHandler, TradingAgent, ULTRA)
- Error handling and retry logic

### [Swap Execution via Agents](./swap-execution-agents.md)

Complete swap and DeFi action execution documentation.

- Architecture overview (agents → handlers → aggregators)
- SwapHandler (quote aggregation)
- ExecuteActionCommand (two-step execution flow)
- AI Agents: SwapAgent, ExecutionAgent, TradingAgent
- Multi-aggregator support (1inch, LiFi, Hyperliquid)
- Supported actions: swap, deposit, withdraw, transfer, approve, bridge
- Transaction approval service (OWASP LLM08 protection)
- Security limits ($50k swap, $100k deposit, $10k transfer)
- Multi-language confirmation messages (5 languages)
- Token address mappings per chain
- API endpoints and request/response schemas

### [Earn Provider Integration](./earn-provider-integration.md)

Complete yield farming and lending protocol integration documentation.

- Architecture overview (Morpho, Aave, Compound)
- Protocol providers:
  - Morpho (MetaMorpho vaults, Morpho Blue markets)
  - Aave V3 (lending/borrowing, health factor)
  - Compound
- Domain entities: EarnPosition, MorphoPosition, AavePosition
- Gateway ports (MorphoGateway, AaveGateway)
- MCP Servers (Morpho: 8088, Aave: 8085)
- AI Agents: DeFi Yield Agent, Lending Agent
- Health Factor monitoring and liquidation risk
- Multi-chain support (Ethereum, Base, Polygon, Arbitrum)
- Yield comparison across protocols
- Database schema (earn_positions table)
- API integration (deposit/withdraw via ExecuteActionCommand)

### [Agent Orchestrator](./agent-orchestrator.md)

Complete multi-agent orchestration system documentation.

- Architecture overview (routing, workflows, fallback)
- 18 Specialized Agents:
  - Core Agents (10): Chat, Hunter AI, Research, Execution, Risk Analyzer, Portfolio, Tax Optimizer, DeFi Yield, Security Auditor, Gas Optimizer
  - Enterprise Agents (8): Compliance, Multisig, Alerts, Crisis, Bridge, Lending, NFT, DAO
- Intent Classification (LLM-based with gpt-4o-mini)
- Agent Orchestrator (message routing, confidence thresholds)
- Supervisor Coordinator (multi-agent workflows)
- Agent Router (keyword-based quick routing)
- Advanced features:
  - Multi-agent voting and consensus
  - Agent debates (structured deliberation)
  - Fallback chains (resilient routing)
  - Performance tracking (efficiency scoring)
  - Custom agent configuration
- Agent Library (10 pre-configured specialists)
- Dependency injection setup

### [Agent Router](./agent-router.md)

Complete Agno-based agent router implementation documentation.

- Architecture overview (keyword classification, MCP integration)
- 5 Specialized DeFi Agents:
  - Trading Agent (1inch, Curve): Swaps, quotes, route comparison
  - Lending Agent (Aave, Morpho): Lending, borrowing, health factor
  - Perpetual Agent (Hyperliquid): Futures, funding rates, liquidation
  - Analytics Agent (DeFiLlama): TVL, yields, protocol comparison
  - Portfolio Agent: Balance tracking, multi-chain aggregation
- Base Agent Architecture (DeFiAgentBase):
  - MCP tool auto-discovery and registration
  - Session management and memory
  - Streaming support
  - Retry with circuit breaker
- MCP Server Integration (11 servers):
  - 1inch, Aave, Morpho, Curve, DeFiLlama, Hyperliquid, Portfolio, etc.
- Intent Keywords for fast routing (no LLM call)
- Configuration (AgnoConfig, AgnoSettings, feature flags)
- Agent instructions and best practices
- Error handling and fallback behavior
- Dependency injection setup

### [Agent Fallback Strategies](./agent-fallback-strategies.md)

Complete fallback and resilience strategies documentation.

- Architecture overview (multi-layer fallback)
- LLM Provider Failover:
  - OpenAI ↔ Anthropic ↔ DeepInfra ↔ Vertex AI
  - Cost optimization (cheaper models on fallback)
  - Priority-based routing
- Circuit Breaker (Redis-backed):
  - CLOSED → OPEN → HALF_OPEN state machine
  - Configurable thresholds (failure/success)
  - Automatic recovery testing
  - Telemetry integration
- Enterprise Retry Engine:
  - Exponential backoff with jitter
  - Error classification (retryable vs non-retryable)
  - Service registry for manual override
  - Comprehensive telemetry
- Retry Configuration (RetryConfig):
  - Pre-configured profiles (MCP servers, Agno agents, testing)
  - Backoff calculation with jitter
- Agent Fallback Chains:
  - Priority-based agent routing
  - Confidence threshold-based fallback
  - Timeout handling
  - FallbackReason tracking
- Admin API endpoints for circuit breaker management
- Telemetry and monitoring metrics
- Best practices and security considerations

### [Audit Logging](./audit-logging.md)

Complete audit logging and telemetry system documentation.

- Audit Log Entity (AuditLogEntry):
  - Immutable event records with categorization
  - 45+ event types (Security, Data Access, Admin, User, System)
  - Metadata storage (JSONB), IP tracking, user agent
  - Outcome tracking (success, failure, pending)
- Event Type Categories:
  - User Actions (login, registration, profile updates)
  - Security Events (auth failures, unauthorized access, rate limits)
  - Data Access Events (PII view/export, sensitive data)
  - Administrative Actions (user suspension, role assignment)
  - Agent Actions (execution start/complete/failed)
  - System Events (configuration changes, background jobs)
- Audit Log Repository (Port-Adapter pattern):
  - PostgreSQL persistence with optimized indexes
  - Query by user, event type, resource, IP address
  - Security event queries, failed event queries
  - Compliance reporting with date ranges
  - Retention policies (configurable, preserves critical events)
- Telemetry Collectors:
  - LLM Telemetry (requests, tokens, costs, cache hits)
  - API Telemetry (latency percentiles, error rates, cost estimation)
  - Retry Telemetry (attempts, circuit breaker state changes)
  - Distillation Telemetry (model performance)
- Distributed Tracing:
  - OpenTelemetry-compatible spans
  - W3C Trace Context propagation
  - Integration with Jaeger, Zipkin, Datadog, X-Ray
- Security Dashboard:
  - Attack statistics (XSS, Prompt Injection)
  - Security posture score (0-100)
  - Transaction approval metrics
  - PII protection stats
  - Agent isolation violations
- Compliance Features:
  - GDPR support (data access logging, retention control)
  - CCPA support (access/deletion request tracking)
  - SOC 2 Type II controls

### [Feature Flags](./feature-flags.md)

Complete feature flags system documentation.

- Telemetry Feature Flags:
  - Master switch (global_enabled)
  - Component-level: API, LLM, Database, Tracing, Metrics
  - Per-API granular control (enabled_apis, disabled_apis)
  - Per-LLM provider control (enabled_llm_providers, disabled_llm_providers)
  - Sampling rates (0.0-1.0) for volume control
  - Per-endpoint telemetry control
  - Environment variable configuration
  - Redis persistence for runtime changes
- Agent Squad Feature Flags:
  - 18 specialized AI agents (10 core + 4 enterprise + 4 advanced)
  - Per-agent configuration (enabled, model, temperature, max_tokens)
  - Intent classification settings
  - Supervisor coordination settings
  - TOML-based configuration
- Subscription Tier Filtering:
  - Free: 5 agents (chat, hunter_ai, research, portfolio, gas_optimizer)
  - Pro: 10 agents (Free + execution, risk_analyzer, etc.)
  - Enterprise: All 18 agents
- External API Feature Flags:
  - DeFi APIs: 1inch, DeFiLlama, CoinGecko, Hyperliquid, Uniswap, Curve, Aave
  - Enterprise APIs: Chainalysis, TRM Labs, Gnosis Safe, Forta, Twilio
  - Advanced APIs: Privy, Axelar, LayerZero, OpenSea, Snapshot
- Agno Agent Feature Flags:
  - 5 DeFi routing agents (Trading, Lending, Perpetual, Portfolio, Analytics)
  - Intent classification toggle
  - Fallback mode settings
  - Retry configuration with circuit breaker
- Integration Feature Flags:
  - Chat tools (Hunter AI, ULTRA, parallel execution)
  - Project scoping and permissions
  - Risk validation settings
- Admin API Endpoints:
  - GET/PUT /api/v1/telemetry/flags
  - POST /api/v1/telemetry/flags/disable-api/{api_name}
  - POST /api/v1/telemetry/flags/save (Redis persistence)
- Runtime toggle support for telemetry flags

---

## 🔗 Related Documents

- [API Architecture Spec (CPO/CEO)](../API_ARCHITECTURE_SPEC_CPO_CEO.md) - Complete API architecture overview
- [Modules Report (CPO)](../MODULES_REPORT_CPO.md) - Detailed module analysis
- [Main Documentation Index](../README.md) - Complete documentation index

---

## 📊 Quick Reference

| Aspect | Choice |
|--------|--------|
| **Architecture** | Hexagonal (Clean Architecture) |
| **Framework** | FastAPI + Dishka |
| **Database** | PostgreSQL 16+ |
| **Cache** | Redis 7+ |
| **Primary LLM** | Vertex AI (Gemini 2.0) |
| **Fallback LLM** | DeepInfra (Llama 3.1) |
| **Background Jobs** | Celery |
| **Payments** | Stripe |

---

**Last Updated**: January 2, 2026
