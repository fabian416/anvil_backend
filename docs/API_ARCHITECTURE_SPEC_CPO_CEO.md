# Anvil Backend - API Architecture Specification

**Version**: 1.0  
**Date**: January 2, 2026  
**Audience**: CPO (Chief Product Officer) & CEO  
**Purpose**: Comprehensive API architecture overview for strategic decision-making

---

## 📊 Executive Summary

Anvil Backend es una plataforma de **Multi-Agent DeFi Intelligence** que proporciona:

- **18 Agentes IA Especializados** para operaciones DeFi
- **233 Endpoints** organizados en **47 módulos**
- **Arquitectura Hexagonal** (Clean Architecture) para máxima flexibilidad
- **99% de ahorro en costos de IA** usando Vertex AI + DeepInfra vs OpenAI

### Key Metrics

| Metric | Value |
|--------|-------|
| Total API Endpoints | 233 |
| Domain Modules | 21 |
| AI Agents | 18 |
| External Integrations | 11 MCP Servers |
| LLM Cost Savings | 99% vs OpenAI |

---

## 🏗️ Architecture Overview

### Hexagonal Architecture (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL LAYER                               │
│  (Databases, APIs, Blockchain RPCs, AI Providers, MCP Servers)  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                             │
│            (HTTP Controllers, WebSocket, REST API)               │
│                                                                  │
│  /api/v1/user/*     /api/v1/admin/*     /api/v1/public/*       │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│         (Adapters, Database, External APIs, LLM Clients)         │
│                                                                  │
│  PostgreSQL  │  Redis  │  Celery  │  Stripe  │  AI Providers   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│              (Use Cases, Commands, Queries, Services)            │
│                                                                  │
│  Chat Commands  │  Agent Orchestration  │  Portfolio Services   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
│           (Entities, Value Objects, Domain Services)             │
│                                                                  │
│  Conversation  │  Message  │  Agent  │  Portfolio  │  Alert     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Dependency Inversion**: Inner layers define interfaces, outer layers implement
2. **Framework Independence**: Core business logic doesn't depend on FastAPI
3. **Database Independence**: Can switch from PostgreSQL to any database
4. **Testability**: Each layer can be tested independently
5. **CQRS Pattern**: Separate read (Queries) and write (Commands) operations

---

## 📦 Domain Modules (21 Core Domains)

### Tier 1: Core Product (Mission-Critical)

| Domain | Description | Business Impact |
|--------|-------------|-----------------|
| **Chat** | Multi-agent conversation system | Core product value proposition |
| **Agent Squad** | 18 specialized AI agents | Key differentiator |
| **Portfolio** | Asset tracking & analysis | Essential user feature |
| **Transactions** | Blockchain transaction tracking | Core functionality |
| **Wallets** | Multi-chain wallet management | Required for all operations |

### Tier 2: Intelligence & Analytics

| Domain | Description | Business Impact |
|--------|-------------|-----------------|
| **Hunter AI** | Market sentiment & predictions | Premium feature |
| **ULTRA** | Flash loans, arbitrage, MEV protection | Professional trading |
| **Graph/GraphRAG** | Protocol relationship analysis | Advanced insights |
| **Markets** | Real-time market data | Essential data source |
| **ML/Predictions** | Machine learning predictions | Advanced analytics |

### Tier 3: User Experience

| Domain | Description | Business Impact |
|--------|-------------|-----------------|
| **Alerts** | Risk alerts & notifications | User engagement |
| **Preferences** | User personalization | UX improvement |
| **Search** | Global search with history | Navigation |
| **Dashboard** | Centralized view | User interface |
| **Comparison** | Asset/protocol comparison | Decision support |

### Tier 4: Platform & Monetization

| Domain | Description | Business Impact |
|--------|-------------|-----------------|
| **Account/Auth** | Authentication & authorization | Security (Critical) |
| **Subscription** | Stripe payment integration | Revenue generation |
| **Payments** | Payment processing | Monetization |
| **Projects** | User project management | Organization |
| **Guest** | Guest chat experience | Acquisition funnel |

### Tier 5: Administration

| Domain | Description | Business Impact |
|--------|-------------|-----------------|
| **Admin** | System administration | Operations |
| **LLM Management** | AI provider management | Cost control |
| **Distillation** | LLM optimization | Cost reduction |

---

## 🤖 Agent Squad Architecture (18 Agents)

### Agent Cost Model

| Provider | Cost (per 1M tokens) | Usage |
|----------|---------------------|-------|
| **OpenAI GPT-4o** | $30.00 | Previous |
| **Vertex AI (Gemini)** | $0.10 - $0.40 | Primary ✅ |
| **DeepInfra (Llama)** | $0.08 | Fallback ✅ |
| **Savings** | **97-99%** | - |

### Agent Categories

#### Core Agents (10)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CORE AGENTS                                 │
├─────────────────────────────────────────────────────────────────┤
│  1. ChatAgent           │ General conversation & assistance     │
│  2. HunterAI            │ Market sentiment & predictions        │
│  3. ResearchAgent       │ Deep protocol analysis (Perplexity)   │
│  4. ExecutionAgent      │ Transaction execution (Privy)         │
│  5. RiskAnalyzer        │ Risk assessment & scoring             │
│  6. PortfolioAgent      │ Portfolio optimization                │
│  7. TaxOptimizer        │ Tax strategy recommendations          │
│  8. DefiYieldAgent      │ Yield farming optimization            │
│  9. SecurityAuditor     │ Smart contract security (Slither)     │
│ 10. GasOptimizer        │ Gas cost optimization                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Enterprise Agents (4)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE AGENTS                             │
├─────────────────────────────────────────────────────────────────┤
│ 11. ComplianceMonitor   │ AML/KYC compliance (Chainalysis)      │
│ 12. MultiSigCoordinator │ Multi-sig treasury (Gnosis)           │
│ 13. AlertMonitoring     │ Real-time alerts (Forta)              │
│ 14. CrisisManager       │ Emergency response                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Advanced Agents (4)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADVANCED AGENTS                              │
├─────────────────────────────────────────────────────────────────┤
│ 15. BridgeCrosschain    │ Cross-chain operations (Axelar)       │
│ 16. LendingBorrowing    │ Leverage strategies (Aave)            │
│ 17. NFTAssetManager     │ NFT portfolio (OpenSea)               │
│ 18. DAOGovernance       │ DAO governance (Snapshot)             │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Orchestration Flow

```
User Message
     │
     ▼
┌─────────────────┐
│ Intent Detector │ ←── Vertex AI (gemini-2.0-flash-exp)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supervisor    │ ←── Selects best agent(s) for task
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Agent 1│ │Agent 2│ ←── Parallel execution if needed
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│   Aggregator    │ ←── Combines responses
└────────┬────────┘
         │
         ▼
    Response
```

---

## 🔌 External Integrations (11 MCP Servers)

### Data & Market Intelligence (6 Servers)

| Server | Purpose | Port |
|--------|---------|------|
| **1inch** | DEX aggregation, swap quotes | 8081 |
| **DeFiLlama** | TVL, protocol analytics, yields | 8082 |
| **The Graph** | On-chain data queries | 8083 |
| **CoinGecko** | Prices, market data | 8084 |
| **Aave** | Lending protocol data | 8085 |
| **Portfolio** | Portfolio aggregation | 8086 |

### Advanced DeFi & Trading (5 Servers)

| Server | Purpose | Port |
|--------|---------|------|
| **Perplexity** | Research & analysis | 8087 |
| **Morpho** | Optimized lending | 8088 |
| **Curve** | Stablecoin DEX | 8089 |
| **Hyperliquid** | Perpetual trading | 8090 |
| **LayerZero** | Cross-chain messaging | 8091 |

---

## 📡 API Endpoint Structure

### URL Hierarchy

```
/api/v1/
├── public/          # Guest access (no auth required)
│   ├── chat/shortcuts
│   └── health
│
├── guest/           # IP-tracked guest access
│   └── chat         # 20 msgs/hour limit
│
├── user/            # Authenticated users
│   ├── chat/        # Multi-agent chat (19 endpoints)
│   ├── portfolio/   # Portfolio management (4 endpoints)
│   ├── hunter/      # Hunter AI features (17 endpoints)
│   ├── ultra/       # Professional trading (20 endpoints)
│   ├── alerts/      # Risk alerts (7 endpoints)
│   ├── wallet/      # Wallet management (5 endpoints)
│   ├── graph/       # GraphRAG (12 endpoints)
│   ├── markets/     # Market data (4 endpoints)
│   ├── ml/          # ML predictions (8 endpoints)
│   ├── search/      # Global search (6 endpoints)
│   ├── preferences/ # User preferences (7 endpoints)
│   ├── projects/    # User projects (5 endpoints)
│   ├── dashboard/   # Dashboard (2 endpoints)
│   └── transactions/# Transaction tracking (2 endpoints)
│
├── admin/           # Admin-only endpoints
│   ├── users/       # User management (14 endpoints)
│   ├── llm/         # LLM management (7 endpoints)
│   ├── projects/    # Project admin (13 endpoints)
│   ├── distillation/# LLM optimization (15 endpoints)
│   ├── metrics/     # System metrics (6 endpoints)
│   ├── wallet/      # Wallet admin (2 endpoints)
│   └── stats/       # Statistics
│
├── account/         # Account management (13 endpoints)
│   ├── signup
│   ├── login
│   ├── logout
│   ├── me
│   ├── password-reset/
│   ├── email-verification/
│   └── privy/       # Wallet-based auth
│
├── auth/            # Authorization (2 endpoints)
├── subscription/    # Subscriptions (6 endpoints)
├── payments/        # Payments (2 endpoints)
├── notifications/   # Notifications (1 endpoint)
└── metrics/         # User metrics (5 endpoints)
```

---

## 💰 Business Model Integration

### Subscription Tiers

| Tier | Target User | Key Features |
|------|-------------|--------------|
| **Free/Guest** | New users | Limited chat (20 msg/hour), basic features |
| **Basic** | Individual traders | Full chat, portfolio, Hunter AI |
| **Pro** | Active traders | ULTRA features, advanced analytics |
| **Enterprise** | Institutions | All agents, API access, compliance tools |

### Revenue Streams

1. **Subscriptions**: Monthly/annual recurring revenue
2. **API Access**: Enterprise API licensing
3. **Transaction Fees**: Optional execution fees
4. **Premium Features**: ULTRA, advanced agents

### Cost Structure

| Component | Cost Model | Optimization |
|-----------|------------|--------------|
| **LLM (AI)** | Per token | Vertex AI (99% savings) |
| **Database** | Storage + compute | PostgreSQL |
| **Cache** | Memory | Redis |
| **Background Jobs** | Compute | Celery + Redis |
| **External APIs** | Per request | Caching layer |

---

## 🛡️ Security Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION OPTIONS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Traditional (Email/Password)                                │
│     └─► Email + Password → JWT Token → Session                  │
│                                                                  │
│  2. Privy (Wallet-based)                                        │
│     └─► Connect Wallet → Privy Auth → JWT Token → Session       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Authorization Levels

| Level | Access |
|-------|--------|
| **Public** | Health checks, shortcuts |
| **Guest** | Limited chat (IP-tracked, rate-limited) |
| **User** | Full user features |
| **Admin** | User management, system config |
| **Super Admin** | Full system access |

### Security Features

- JWT tokens with session management
- Rate limiting per endpoint and role
- IP tracking for guests
- Secure password hashing (bcrypt + pepper)
- SQL injection prevention (parameterized queries)
- Path traversal prevention
- SSRF prevention

---

## 📈 Scalability Considerations

### Current Architecture Supports

- **Horizontal Scaling**: Stateless API servers
- **Background Processing**: Celery workers (independently scalable)
- **Caching**: Redis cluster support
- **Database**: PostgreSQL with read replicas support
- **AI Providers**: Multiple providers with automatic fallback

### Performance Optimizations

1. **Intent Caching**: Cache common intent classifications
2. **GraphRAG Caching**: Cache graph queries
3. **Market Data Caching**: Cache external API responses
4. **Query Optimization**: CQRS for efficient reads
5. **LLM Distillation**: Optimize LLM requests

---

## 🚀 Implementation Roadmap

### Phase 1: Core Platform ✅ Complete

- [x] Hexagonal architecture
- [x] Multi-agent chat system
- [x] User authentication
- [x] Portfolio management
- [x] Wallet integration

### Phase 2: Intelligence Layer ✅ Complete

- [x] 18 AI agents
- [x] Hunter AI (sentiment, predictions, patterns)
- [x] ULTRA (flash loans, arbitrage, MEV)
- [x] GraphRAG integration
- [x] Vertex AI + DeepInfra (cost optimization)

### Phase 3: Enterprise Features ✅ Complete

- [x] Enterprise retry system
- [x] Circuit breakers
- [x] Telemetry & monitoring
- [x] Admin dashboard APIs
- [x] LLM ranking & management

### Phase 4: Advanced Features 🔄 In Progress

- [x] Guest chat system
- [x] Multi-language support
- [ ] Real-time WebSocket streaming
- [ ] Advanced analytics dashboard
- [ ] Mobile API optimization

### Phase 5: Future Enhancements 📋 Planned

- [ ] Cross-chain execution
- [ ] DAO governance integration
- [ ] NFT portfolio features
- [ ] Advanced compliance tools
- [ ] White-label API

---

## 📊 Module Dependency Map

```
                    ┌─────────────────┐
                    │   Account/Auth  │ ◄── Required by all authenticated endpoints
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│     Wallets     │ │      Chat       │ │   Preferences   │
└────────┬────────┘ └────────┬────────┘ └─────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│   Transactions  │ │   Agent Squad   │
└────────┬────────┘ └────────┬────────┘
         │                   │
         │    ┌──────────────┼──────────────┐
         ▼    ▼              ▼              ▼
    ┌─────────────┐   ┌─────────────┐ ┌─────────────┐
    │  Portfolio  │   │  Hunter AI  │ │    ULTRA    │
    └─────────────┘   └─────────────┘ └─────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌─────────┐   ┌─────────────┐ ┌─────────────┐
        │ Markets │   │   GraphRAG  │ │     ML      │
        └─────────┘   └─────────────┘ └─────────────┘
```

---

## 📝 Key Technical Decisions

### Why Hexagonal Architecture?

1. **Flexibility**: Easy to swap databases, frameworks, or AI providers
2. **Testability**: Each layer can be tested independently
3. **Maintainability**: Clear separation of concerns
4. **Team Scalability**: Teams can work on different layers independently

### Why Vertex AI + DeepInfra?

1. **Cost**: 99% savings vs OpenAI ($0.10 vs $30 per 1M tokens)
2. **Reliability**: Automatic fallback if primary fails
3. **Performance**: Comparable quality for DeFi use cases
4. **Flexibility**: Easy to add/switch providers

### Why CQRS Pattern?

1. **Performance**: Optimized read paths
2. **Scalability**: Separate scaling of reads vs writes
3. **Flexibility**: Different models for reading vs writing
4. **Simplicity**: Clear separation of concerns

---

## 📞 Contact & Resources

### Technical Resources

- **API Documentation**: `/docs` (Swagger UI)
- **Architecture Docs**: `/docs/architecture/`
- **Feature Docs**: `/docs/features/`

### Quick Start Commands

```bash
# Start development environment
make start-dev     # All services (FastAPI + MCP + Celery)

# View logs
make logs-all      # All services

# Run tests
make code.test     # Run all tests

# Check API status
curl http://localhost:8000/api/v1/
```

---

**Document Version**: 1.0  
**Last Updated**: January 2, 2026  
**Author**: Engineering Team  
**Status**: Production Ready ✅
