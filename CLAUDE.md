# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**Authentication**: JWT with session storage, custom identity provider abstraction

**Environment Management**: Multi-environment support through TOML configs in `config/{env}/` directories