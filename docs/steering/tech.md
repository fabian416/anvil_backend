# Technical Stack - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Active

---

## Core Technology Stack

### Language & Runtime

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.12 |
| **Package Manager** | uv | Latest |
| **Runtime** | uvicorn + uvloop | Latest |

### Framework & Libraries

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | FastAPI | High-performance async API |
| **DI Container** | Dishka | Framework-agnostic dependency injection |
| **ORM** | SQLAlchemy | Database abstraction |
| **Migrations** | Alembic | Database schema management |
| **Validation** | Pydantic | Data validation & serialization |
| **Error Handling** | fastapi-error-map | Contextual error handling |

### Data Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Primary Database** | PostgreSQL 16+ | Main data storage |
| **Cache** | Redis 7+ | Session, cache, message broker |
| **Background Jobs** | Celery | Async task processing |

### AI/LLM Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Primary LLM** | Vertex AI (Gemini 2.0) | Main AI provider |
| **Fallback LLM** | DeepInfra (Llama 3.1) | Automatic fallback |
| **Research** | Perplexity AI | Deep research queries |
| **Model Mapping** | OpenAI-compatible | Seamless provider switching |

### External Integrations

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Payments** | Stripe | Subscriptions & payments |
| **Email** | Mailgun | Transactional emails |
| **Wallet Auth** | Privy | Web3 authentication |
| **Data Providers** | 11 MCP Servers | DeFi data aggregation |

---

## Architecture Patterns

### Hexagonal Architecture (Clean Architecture)

```
┌─────────────────────────────────────────┐
│           DOMAIN LAYER                   │
│  (Entities, Value Objects, Ports)       │
│  - No external dependencies             │
│  - Pure business logic                  │
└─────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────┐
│         APPLICATION LAYER                │
│  (Commands, Queries, Interactors)       │
│  - Use case orchestration               │
│  - Depends only on Domain               │
└─────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────┐
│        INFRASTRUCTURE LAYER              │
│  (Adapters, Repositories, Clients)      │
│  - Implements Domain ports              │
│  - External system integration          │
└─────────────────────────────────────────┘
                    ▲
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER               │
│  (Controllers, Routers, Schemas)        │
│  - HTTP/WebSocket handlers              │
│  - Request/Response transformation      │
└─────────────────────────────────────────┘
```

### CQRS Pattern

- **Commands**: Write operations, business-critical reads
- **Queries**: Optimized read operations
- **Separate Models**: Command models vs Query models
- **Gateways**: CommandGateway, QueryGateway interfaces

### Dependency Injection

- **Container**: Dishka (framework-agnostic)
- **Providers**: Domain, Application, Infrastructure, Presentation
- **Scopes**: Request, Session, Singleton

---

## LLM Provider Configuration

### Model Mapping (OpenAI → Provider)

```toml
# Vertex AI (Primary)
[llm_provider.vertex_ai.model_mapping]
"gpt-4o" = "gemini-2.0-flash-exp"
"gpt-4o-mini" = "gemini-2.0-flash-exp"
"gpt-4" = "gemini-1.5-pro"
"gpt-3.5-turbo" = "gemini-2.0-flash-exp"

# DeepInfra (Fallback)
[llm_provider.deepinfra.model_mapping]
"gpt-4o" = "meta-llama/Meta-Llama-3.1-70B-Instruct"
"gpt-4o-mini" = "meta-llama/Llama-3.2-3B-Instruct"
"gpt-4" = "meta-llama/Meta-Llama-3.1-405B-Instruct"
"gpt-3.5-turbo" = "meta-llama/Llama-3.2-3B-Instruct"
```

### Fallback Behavior

```python
# Automatic fallback when primary fails
LLMClientWithFallback(
    primary_client=LLMClientVertexAI(...),    # Gemini 2.0
    fallback_client=LLMClientDeepInfra(...),  # Llama 3.1
    enable_fallback=True,
)
```

### Cost Comparison

| Provider | Cost (1M tokens) | Savings |
|----------|-----------------|---------|
| OpenAI GPT-4o | $30.00 | - |
| Vertex AI Gemini | $0.10-$0.40 | 98-99% |
| DeepInfra Llama | $0.08 | 99%+ |

---

## MCP Server Architecture

### Data & Market Intelligence (Ports 8081-8086)

| Server | Port | Data Source |
|--------|------|-------------|
| 1inch | 8081 | DEX aggregation |
| DeFiLlama | 8082 | Protocol analytics |
| The Graph | 8083 | On-chain data |
| CoinGecko | 8084 | Market data |
| Aave | 8085 | Lending data |
| Portfolio | 8086 | Aggregation |

### Advanced DeFi (Ports 8087-8091)

| Server | Port | Data Source |
|--------|------|-------------|
| Perplexity | 8087 | Research |
| Morpho | 8088 | Lending |
| Curve | 8089 | Stablecoins |
| Hyperliquid | 8090 | Perpetuals |
| LayerZero | 8091 | Cross-chain |

---

## Database Schema (Key Tables)

### Core Entities

```sql
-- Users
users (id, email, password_hash, role, created_at, ...)

-- Conversations
conversations (id, user_id, title, created_at, ...)

-- Messages
messages (id, conversation_id, role, content, agent_type, ...)

-- Agent Sessions
agent_sessions (id, conversation_id, agent_type, state, ...)
```

### Supporting Entities

```sql
-- Wallets
wallets (id, user_id, address, chain, provider, ...)

-- Transactions
transactions (id, user_id, hash, chain, status, ...)

-- Alerts
alerts (id, user_id, type, threshold, enabled, ...)

-- Subscriptions
subscriptions (id, user_id, plan_id, stripe_id, ...)
```

---

## Security Configuration

### Authentication

- **JWT Tokens**: HS256 algorithm
- **Session Storage**: Redis
- **Token Refresh**: Automatic before expiration
- **Password Hashing**: bcrypt + pepper + salt

### Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Guest Chat | 20 requests/hour |
| User Chat | 100 requests/minute |
| Admin API | 1000 requests/minute |
| Public API | 60 requests/minute |

### Security Headers

- CORS configured per environment
- CSRF protection
- Content Security Policy
- Rate limiting per IP/user

---

## Observability

### Logging

- **Format**: Structured JSON
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Storage**: File + stdout
- **Rotation**: Daily, 30-day retention

### Metrics

- Request latency (p50, p95, p99)
- Error rates by endpoint
- LLM token usage
- Agent utilization

### Monitoring

- Health check endpoints
- Circuit breaker status
- Database connection pool
- Redis connection status

---

## Development Workflow

### Local Development

```bash
# Environment setup
export APP_ENV=local
make dotenv
make venv
uv pip install -e '.[dev,test]'

# Start services
make up.db         # Database
make start-dev     # All services

# Code quality
make code.format   # Ruff format
make code.lint     # Ruff + mypy
make code.test     # Pytest
```

### Testing Strategy

| Level | Coverage Target | Tools |
|-------|-----------------|-------|
| Unit | 80%+ | pytest |
| Integration | 70%+ | pytest + testcontainers |
| E2E | Key flows | pytest + httpx |

### CI/CD Pipeline

1. **Lint**: ruff, mypy, slotscheck
2. **Test**: pytest with coverage
3. **Build**: Docker image
4. **Deploy**: Environment-specific

---

## Configuration Management

### TOML-based Configuration

```
config/
├── local/
│   ├── config.toml      # Main config
│   ├── .secrets.toml    # Secrets (not in git)
│   └── export.toml      # Env vars to export
├── dev/
│   └── ...
└── prod/
    └── ...
```

### Environment Variables

- `APP_ENV`: Environment (local/dev/prod)
- Database credentials (from TOML)
- API keys (from .secrets.toml)
- Redis URL (from TOML)

---

## Technology Decisions

### Why Python 3.12?

- Performance improvements
- Better typing support
- Async/await maturity
- Rich ecosystem for AI/ML

### Why FastAPI?

- High performance (async)
- OpenAPI auto-generation
- Type hints integration
- Active community

### Why Dishka over FastAPI DI?

- Framework-agnostic
- Better testing support
- No dependency leakage
- Cleaner architecture

### Why PostgreSQL?

- ACID compliance
- JSON support
- Full-text search
- Mature ecosystem

### Why Redis?

- Session storage
- Caching
- Message broker (Celery)
- Pub/sub for real-time

---

**Last Updated**: January 2, 2026
