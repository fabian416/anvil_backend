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

### [Lending Protocols Implementation](./lending-protocols-implementation.md)

Complete implementation documentation for Aave V3, Compound V3, and Morpho Protocol following CTO methodology.

- Implementation Status:
  - Aave V3: 75% complete (user positions ✅, markets ⚠️ partial)
  - Compound V3: 100% complete ✅
  - Morpho Protocol: 100% complete ✅
- Architecture overview (Client → Adapter → Gateway pattern)
- Real RPC implementations:
  - Aave: `getUserAccountData()` for positions
  - Compound: `balanceOf()`, `borrowBalanceOf()` for positions
  - Morpho: GraphQL API (complete)
- Caching strategy (2-10 min TTLs based on data type)
- Health factor monitoring and risk assessment
- Error handling and fallback mechanisms
- MCP server integration (Aave: 8085, Morpho: 8088)
- Multi-chain support (6+ chains)
- CTO methodology application (Problem Decomposition, Solution Generation, Risk Assessment)
- Performance considerations and future enhancements

### [LLM Models & Cost Analysis](./llm-models-cost-analysis.md)

Comprehensive analysis of LLM models and costs across Hunter AI, Agent Squad, ULTRA, and Chat systems.

### [LLM Providers Analysis](./llm-providers-analysis.md)

Detailed analysis of the 3 LLM providers configured in the system:
- **Vertex AI (Gemini 2.0 Flash)**: Primary provider - $0.10-0.40/1M tokens
- **DeepInfra (Meta Llama)**: Fallback provider - $0.08/1M tokens (68% cheaper)
- **OpenAI (GPT-4)**: Legacy/Optional - $5.00-15.00/1M tokens (50-187x more expensive)

Includes cost comparison, fallback strategy, configuration files, and implementation details.

- Model configuration overview (Vertex AI + DeepInfra)
- Model mapping strategy (OpenAI names → actual models)
- Cost analysis by system:
  - Hunter AI Agent: Market sentiment ($0.20/month at 1K requests)
  - Agent Squad: 18 agents ($1.25-12.50/month depending on usage)
  - Chat: General conversation ($1.25/month at 5K requests)
  - ULTRA: Limited LLM usage (algorithmic focus)
- Provider pricing comparison:
  - Vertex AI: $0.10-0.40/1M tokens (primary)
  - DeepInfra: $0.08/1M tokens (fallback, 68% cheaper)
  - OpenAI: $5.00-15.00/1M tokens (legacy, 99% more expensive)
- Monthly cost estimates (10M, 50M, 100M tokens)
- Cost savings: 91.6% (Vertex AI) or 97.7% (DeepInfra) vs OpenAI
- Model selection strategy (when to use which model)
- Fallback strategy and cost impact
- Cost optimization recommendations
- Real-world usage patterns and projections
- Configuration files reference

### [Chat Message Sources Attribution](./chat-message-sources-spec.md)

Complete specification for adding source attribution to chat messages, enabling frontend to display knowledge sources and citations.

- Problem decomposition (CTO methodology): Source tracking requirements, constraints, solution space
- Solution generation: Hybrid approach (metadata + optional table) selected
- Data model: SourceInfo value object with rich source information
- Source mapping by agent:
  - Hunter AI: CoinGecko, Twitter, Reddit, Discord, RSS News
  - Research: Perplexity citations
  - DeFi Yield: DeFiLlama, Aave, Morpho, Compound
  - Execution: 1inch, Privy, blockchain
  - Portfolio: Database, price APIs
  - Risk Analyzer: DeFiLlama, protocol APIs
  - All 18 agents mapped with their data sources
- Updated response schemas: MessageResponse, UnifiedChatResponse with sources
- Implementation plan: 5 phases (infrastructure → agents → handlers → persistence → frontend)
- Source collection patterns: API calls, MCP servers, database queries, aggregated sources
- Security: Source sanitization (remove sensitive data from query params)
- Frontend display guidelines: Component structure, examples, citation formats
- Testing strategy: Unit tests, integration tests, backward compatibility
- Migration strategy: Gradual rollout, backward compatibility
- Performance considerations: Latency impact (<5%), storage impact (~1-2 KB per message)
- Analytics: Source usage tracking, reliability metrics

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

### [Admin Endpoints](./admin-endpoints.md)

Complete admin endpoints (operaciones internas) documentation.

- User Management:
  - List users (pagination, sorting, search)
  - Grant/revoke admin roles (super admin only for revoke)
  - Activate/deactivate user accounts
  - Change user passwords
- Wallet Management:
  - List wallets with filters (provider, chain, search)
  - Get wallet details by Privy wallet ID
  - Update wallet configuration and metadata
- LLM Orchestration Management:
  - Dashboard with WebSocket real-time updates
  - Provider management (list, update, health checks)
  - Model management (list, update, performance metrics)
  - Rankings and leaderboards
  - Telemetry metrics and cost tracking
  - Budget configuration and alerts
  - Circuit breaker management
- Agent Management:
  - List all agents with status
- Security Dashboard:
  - Security dashboard summary
  - Latest security scan results
  - Scan history and tool results
  - Vulnerability trends (1-90 days)
  - Health check for security system
  - 5 OWASP security tools (Helios, LLMExploiter, Nettacker, etc.)
- Retry System Management:
  - List all services with retry status
  - Enable/disable services manually
  - Circuit breaker status and reset
  - Service metrics (attempts, success rate, latency)
- Transactions Admin View:
  - List transactions by wallet address or user ID
  - Filter by chain, status, transaction type
  - Pagination support
- Projects Management:
  - CRUD operations for projects
  - Knowledge base documents (create, list, process)
  - Assignment rules (create, list, update)
  - User assignments to projects
- Chat Analytics Dashboard:
  - Dashboard summary (conversations, messages, users)
  - Agent performance leaderboard
  - Cache efficiency metrics
  - Cost tracking (by agent, model, day, user)
  - Error monitoring and trends
  - Active users metrics (DAU, WAU, MAU)
  - Conversation metrics
  - Data export (JSON, CSV)
- Metrics & Statistics:
  - Metrics overview (wallets, transactions, users)
  - Time series data (transactions, wallets, user activity)
  - Distribution data (wallets by provider, transactions by chain/status/type)
  - System statistics
- Distillation Management:
  - Static response templates (CRUD)
  - Configuration management
  - Cache invalidation (exact, semantic, all)
  - Cache statistics
  - Telemetry requests and summary
  - Distillation validation metrics
- Policies Management:
  - List, create, get, update Privy policies
  - Policy rules management
- Telemetry Feature Flags:
  - Runtime toggle for telemetry components
  - Per-API and per-LLM provider control
  - Redis persistence
- Authentication: All endpoints require Bearer token + ADMIN role
- Total: 110+ admin endpoints across 13 categories

### [Permissions & Scopes](./permissions-scopes.md)

Complete permissions and scopes system documentation.

- Permission-Based Authorization:
  - Base Permission class with PermissionContext
  - authorize() function for permission checks
  - Permission types: CanManageSelf, CanManageSubordinate, CanManageRole
  - Composite permissions (AnyOf) for OR logic
- User Role-Based Access Control (RBAC):
  - 4 roles: ADMIN, MODERATOR, USER, GUEST
  - Role hierarchy (SUBORDINATE_ROLES):
    - ADMIN can manage all roles (including other admins)
    - MODERATOR can manage USER and GUEST
    - USER can manage GUEST
    - GUEST can manage nothing
  - Role properties: is_assignable, is_changeable
  - get_hierarchy() method for role hierarchy
- Super Admin Protection:
  - Email-based super admin (ADMIN_USER_ADMIN or USER_ADMIN env var)
  - Cannot be revoked or deactivated
  - Only super admin can grant/revoke admin roles
  - Protected from role changes
- Agent Isolation & RBAC:
  - 4 agent roles: READ_ONLY, STANDARD, PRIVILEGED, ADMIN
  - 8 resource types: USER_DATA, SYSTEM_CONFIG, EXTERNAL_API, DATABASE, FILE_SYSTEM, NETWORK, WALLET, AGENT_COMMUNICATION
  - AgentPermission dataclass (resource_type, actions, scope)
  - AgentIsolationGuard class:
    - register_agent() for role assignment
    - check_permission() for resource access
    - check_agent_communication() for agent-to-agent messaging
    - validate_agent_routing() to prevent prompt injection
    - get_agent_capabilities() for capability queries
    - revoke_agent_access() for access revocation
  - Default role permissions matrix
  - High-risk actions: delete, transfer, execute, terminate, broadcast, elevate
  - Permission decorator (@require_agent_permission)
- Project Tool Permissions:
  - Tool whitelisting via enabled_tools list
  - Protocol whitelisting via enabled_protocols
  - Chain whitelisting via enabled_chains
  - Risk validation against risk_config:
    - max_risk_tolerance for portfolio optimization
    - max_capital_per_trade for arbitrage tools
    - min_profit_threshold for trading
  - ProjectToolExecutor with permission and risk validation
  - Feature flags: tool_permissions_enabled, risk_validation_enabled
- Setting Scopes:
  - SettingScope enum: GLOBAL, SECURITY, PAYMENTS, AI
  - Setting entity with scope field
  - Scope-based organization for access control
- Permission Contexts:
  - UserManagementContext (subject, target)
  - RoleManagementContext (subject, target_role)
  - AgentPermission (resource_type, actions, scope)
- Permission Enforcement Points:
  - Application layer (interactors)
  - Presentation layer (controllers with Security(bearer_scheme))
  - Agent actions (AgentIsolationGuard)
  - Project tool execution (ProjectToolExecutor)
- Usage examples for all permission types
- Security considerations:
  - Principle of least privilege
  - Defense in depth
  - Super admin protection
  - Agent isolation
  - Project tool permissions

### [API Documentation](./api-documentation.md)

Complete API documentation with endpoint reference.

- API Architecture:
  - Root router structure
  - API v1 router organization
  - Public, User, and Admin endpoint categories
  - WebSocket endpoints
- Endpoint Categories (200+ endpoints):
  - Public Endpoints (15): Account management, Guest chat, Health check
  - User Endpoints (100+): Chat, Wallet, Portfolio, Markets, Alerts, Projects, Transactions, Bitcoin, DeFi protocols (Aave, Morpho, Hyperliquid, Curve, Axelar, LayerZero), Hunter AI (6 tools), ULTRA Arbitrage (4 tools), GraphRAG, ML, Preferences, Dashboard, Search, Comparison, Notifications, Metrics
  - Admin Endpoints (110+): User management, Wallet management, LLM orchestration (dashboard, providers, models, rankings, telemetry, budgets, circuit breakers), Agent management, Retry system, Security dashboard, Chat analytics, Transactions admin, Projects management, Distillation, Policies, Stats, Metrics, Telemetry flags
  - Subscription & Payment: Subscription management, Payment processing
- Authentication & Authorization:
  - Bearer Token (JWT): Access token (15 min), Refresh token (7 days)
  - Privy Web3 Login: Web3-native authentication
  - Role-Based Access Control: GUEST, USER, MODERATOR, ADMIN, SUPER_ADMIN
  - Permission checks in application layer
- Request/Response Formats:
  - Standard JSON request/response
  - Pagination (limit, offset)
  - Sorting (sort_by, sort_order)
  - Filtering (field=value, search)
  - Error response format
- Error Handling:
  - Error codes: Authentication (401), Authorization (403), Validation (400), Not Found (404), Conflict (409), Service (503)
  - Structured error responses with codes, messages, details
- Rate Limiting:
  - Guest: 20/hour, 50/day
  - Authenticated: 1000/hour, 10000/day
  - Rate limit headers (X-RateLimit-*)
- Multi-Language Support:
  - Supported languages: en (English), es (Spanish), pt (Portuguese), zh (Mandarin)
  - Language detection: Header, Query parameter, Request body
  - Language-specific endpoints
- WebSocket API:
  - Chat WebSocket (/ws/chat): Real-time agent responses, streaming support
  - Graph WebSocket (/ws/graph): Real-time graph updates
  - LLM Dashboard WebSocket (/admin/llm/dashboard/ws): Real-time metrics
  - Message format and types
- API Examples:
  - Create conversation
  - Send message (unified routing)
  - Execute swap action (two-step flow)
  - List users (admin)
- API Versioning:
  - Current version: v1
  - Future versions: v2 (GraphQL, webhooks, batch operations)
  - Migration strategy
- OpenAPI/Swagger Documentation:
  - Swagger UI (/docs)
  - ReDoc (/redoc)
  - OpenAPI JSON (/openapi.json)
  - Interactive testing
- Best Practices:
  - HTTP methods (GET, POST, PUT, PATCH, DELETE)
  - Error handling
  - Pagination
  - Rate limiting
  - WebSockets for real-time
  - Language support
- API Statistics:
  - 200+ total endpoints
  - 30+ API modules
  - 4 supported languages
  - 3 WebSocket endpoints

### [Error Handling](./error-handling.md)

Complete error handling system documentation following CTO methodology.

- Architecture overview (Domain, Application, Infrastructure layers)
- Error Code System (100+ codes across 15 categories)
- Standardized error response format with i18n support
- Error handling layers:
  - Domain Layer (DomainError, DomainFieldError)
  - Application Layer (ApplicationError with ErrorCode)
  - Infrastructure Layer (route-level handlers)
- Global exception handlers (8 handlers)
- Error translators (9 translators for fastapi-error-map)
- Error callbacks (logging: log_info, log_error)
- Usage patterns and best practices
- Error code reference (AUTH, USER, CHAT, WALLET, PORT, MKT, SRCH, ALRT, SUB, ADM, LLM, TEL, VAL, SYS, LOC)
- Testing error handling (unit and integration tests)
- Migration guide from legacy DomainError to ApplicationError
- Key files reference

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
