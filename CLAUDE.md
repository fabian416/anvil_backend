# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ IMPORTANT: Legacy System Deprecation

**The legacy conversation system is DEPRECATED** and will be removed on **2026-06-01**.

### Legacy System (DO NOT USE)
- ❌ Router: `src/app/presentation/http/controllers/chat/router.py`
- ❌ Base Path: `/api/v1/user/chat/*`
- ❌ Tables: `conversations`, `users` (INTEGER user_id)

### New System (USE THIS)
- ✅ Router: `src/app/presentation/http/controllers/chat/conversations_router.py`
- ✅ Base Path: `/api/v1/conversations/*`
- ✅ Tables: `chat_conversations`, `chat_users` (UUID user_id)
- ✅ Features: Guest support, multi-language, intent routing, metadata, status tracking

### Migration Guide
See **[docs/DEPRECATION_PLAN.md](docs/DEPRECATION_PLAN.md)** for complete migration instructions.

**When developing new features**:
- Always use the new system (`conversations_router.py`)
- Never add features to the legacy system (`router.py`)
- All data has been migrated - both systems currently work in parallel

---

## Development Commands

**Environment Setup:**
```bash
export APP_ENV=local  # or dev/prod
make dotenv           # Generate .env files from TOML config
make venv            # Create virtual environment
uv pip install -e '.[dev,test]'  # Install dependencies
```

**Database:**
```bash
make up.db           # Start PostgreSQL in Docker
make create-db       # Create database
alembic upgrade head # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

**Development Server:**
```bash
make start           # Start FastAPI server with reload
make start-dev       # Start ALL dev services (FastAPI + MCP + Celery + Flower)
make stop-dev        # Stop all dev services
make status-dev      # Check status of all dev services
```

**Development Logs:**
```bash
make logs-fastapi    # View FastAPI logs
make logs-mcp        # View MCP server logs
make logs-celery     # View Celery worker logs
make logs-all        # View all logs combined
```

**MCP Servers:**
```bash
make mcp.all         # Start all 11 MCP servers (ports 8081-8091)
make mcp.stop        # Stop all MCP servers

# Core Data & Market Intelligence (6 servers):
# mcp.oneinch, mcp.defillama, mcp.thegraph, mcp.coingecko, mcp.aave, mcp.portfolio

# Advanced DeFi & Trading (5 servers):
# mcp.perplexity, mcp.morpho, mcp.curve, mcp.hyperliquid, mcp.layerzero

# Note: All 11 MCP servers are automatically started with 'make start-dev'
```

**Code Quality:**
```bash
make code.format     # Format with ruff
make code.lint       # Lint with ruff, slotscheck, mypy
make code.test       # Run pytest
make code.check      # Run both lint and test
```

**Background Tasks:**
```bash
make celery.worker   # Start Celery worker
make celery.beat     # Start Celery scheduler
make celery.flower   # Start Flower monitoring UI
```

## Architecture Overview

This is a **Hexagonal Architecture** (Clean Architecture) implementation using FastAPI, following strict layered principles with dependency inversion.

### Layer Structure

**Domain Layer** (`src/app/domain/`):
- Core business entities and value objects
- Domain services for business logic
- Ports (interfaces) for external dependencies
- No dependencies on outer layers

**Application Layer** (`src/app/application/`):
- **Commands**: Write operations and business-critical reads (CQRS pattern)
- **Queries**: Optimized read operations with query models
- Interactors orchestrate domain logic and external calls
- Application services for cross-cutting concerns like authorization

**Infrastructure Layer** (`src/app/infrastructure/`):
- **Adapters**: Implementations of domain ports
- **Persistence**: SQLAlchemy mappings and database adapters
- **Auth**: Session management and JWT handling
- External integrations (Stripe, Celery, etc.)

**Presentation Layer** (`src/app/presentation/http/`):
- HTTP controllers and routers
- Request/response models (Pydantic schemas)
- Authentication middleware
- Error handling

### Key Architectural Patterns

**Dependency Injection**: Uses Dishka framework (not FastAPI's built-in DI) to maintain framework independence.

**CQRS Implementation**: 
- Commands handle writes/business-critical reads via `UserCommandGateway`
- Queries handle optimized reads via `UserQueryGateway` 
- Separate models for commands (entities) vs queries (query models)

**Authentication Context**: Implemented as infrastructure handlers rather than domain services, treating auth as a separate bounded context.

**Configuration System**: TOML-based configuration as single source of truth, generates .env files for Docker.

## Important Conventions

**Entity vs Value Object Pattern**: Domain objects follow DDD patterns with entities having identity and value objects being immutable.

**Interactor Pattern**: Each use case is implemented as a single interactor with clear input/output contracts.

**Port-Adapter Pattern**: All external dependencies accessed through domain-defined ports with infrastructure adapters.

**Error Handling**: Uses `fastapi-error-map` for contextual, per-route error handling with OpenAPI schema generation.

## Development Notes

**Testing**: 
- Unit tests focus on domain and application layers
- Integration tests for infrastructure adapters
- Use factories for test data creation

**Database**: 
- Alembic for migrations with custom config path: `src/app/infrastructure/persistence_sqla/alembic.ini`
- SQLAlchemy with explicit mappings in `mappings/` directory

**Background Tasks**: Celery + Redis for async processing (emails, data processing, etc.)

**Agent Squad**: 18 specialized AI agents for DeFi operations using Vertex AI (primary) + DeepInfra (fallback):
- Core agents (10): Chat, Hunter AI, Research, Execution, Risk Analyzer, Portfolio, Tax Optimizer, DeFi Yield, Security Auditor, Gas Optimizer
- Enterprise agents (4): Compliance Monitor, Multi-Sig Coordinator, Alert Monitoring, Crisis Manager
- Advanced agents (4): Bridge Crosschain, Lending Borrowing, NFT Asset Manager, DAO Governance
- **Cost**: $0.10/1M tokens (Vertex AI) vs $30/1M tokens (OpenAI) = 99% savings
- **Configuration**: See `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` for full setup guide
- **API Keys**: Add to `config/local/.secrets.toml` under `[vertex_ai]` and `[deepinfra]` sections

**Hunter AI Data Sources** (see `docs/HUNTER_AI_DATA_SOURCES.md`):
- CoinGecko: ✅ Real prices and OHLCV data (free)
- RSS News: ✅ Real news from CoinDesk, CoinTelegraph, etc. (free)
- Reddit: ⚠️ Fallback mode (requires OAuth2)
- Twitter/Discord: 🟡 Simulated (paid APIs)

**Guest Chat System** (see `docs/GUEST_CHAT_SYSTEM.md`):
- Endpoint: `POST /api/v1/guest/chat`
- IP-based tracking, rate limiting (20 msgs/hour)
- Real Hunter AI and ULTRA data for guests
- Multi-language support (en, es, pt, zh)

**Chat Execution** (see `docs/api/examples/`):
- User Chat: `POST /api/v1/user/chat/conversations/{id}/messages`
- Execute Actions: `POST /api/v1/user/chat/conversations/{id}/execute`
- Shortcuts: `GET /api/v1/public/chat/shortcuts`

**Authentication**: JWT with session storage, custom identity provider abstraction

**Environment Management**: Multi-environment support through TOML configs in `config/{env}/` directories