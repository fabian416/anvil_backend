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
