# Project Structure - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Active

---

## Directory Overview

```
anvil_backend/
├── config/                    # Environment configurations
│   ├── local/                # Local development
│   ├── dev/                  # Development environment
│   └── prod/                 # Production environment
│
├── docs/                      # Documentation
│   ├── api/                  # API documentation
│   ├── architecture/         # Architecture docs
│   ├── features/             # Feature documentation
│   ├── steering/             # Steering documents
│   └── ...
│
├── scripts/                   # Utility scripts
│   └── test_*.py            # Test scripts
│
├── src/                       # Source code
│   └── app/                  # Main application
│
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test fixtures
│
├── Makefile                   # Development commands
├── pyproject.toml            # Python project config
└── README.md                 # Project overview
```

---

## Source Code Structure

### Main Application (`src/app/`)

```
src/app/
├── domain/                    # DOMAIN LAYER
│   ├── {module}/             # Feature modules
│   │   ├── entities/         # Domain entities
│   │   ├── value_objects/    # Value objects
│   │   ├── ports/            # Port interfaces
│   │   └── services/         # Domain services
│   ├── entities/             # Shared entities
│   ├── enums/                # Domain enumerations
│   ├── exceptions/           # Domain exceptions
│   ├── ports/                # Shared ports
│   ├── services/             # Shared domain services
│   └── value_objects/        # Shared value objects
│
├── application/               # APPLICATION LAYER
│   ├── {module}/             # Feature modules
│   │   ├── commands/         # Write operations
│   │   ├── queries/          # Read operations
│   │   └── services/         # Application services
│   ├── commands/             # Shared commands
│   ├── queries/              # Shared queries
│   └── common/               # Common utilities
│       ├── ports/            # Application ports
│       ├── services/         # Cross-cutting services
│       └── exceptions/       # Application exceptions
│
├── infrastructure/            # INFRASTRUCTURE LAYER
│   ├── adapters/             # Port implementations
│   │   ├── agent_squad/      # AI agent adapters
│   │   └── ...
│   ├── persistence_sqla/     # SQLAlchemy persistence
│   │   ├── mappings/         # ORM mappings
│   │   └── migrations/       # Alembic migrations
│   ├── auth/                 # Authentication
│   │   └── handlers/         # Auth handlers
│   ├── celery/               # Background tasks
│   ├── subscription/         # Stripe integration
│   └── mcp/                  # MCP server clients
│
├── presentation/              # PRESENTATION LAYER
│   └── http/                 # HTTP interface
│       ├── controllers/      # Route handlers
│       │   ├── account/      # /api/v1/account
│       │   ├── admin/        # /api/v1/admin
│       │   ├── chat/         # /api/v1/user/chat
│       │   ├── user/         # /api/v1/user
│       │   └── ...
│       ├── auth/             # Auth utilities
│       └── errors/           # Error handling
│
├── setup/                     # Application setup
│   ├── ioc/                  # Dependency injection
│   ├── config/               # Configuration loading
│   └── app_factory.py        # App builder
│
└── run.py                     # Application entry point
```

---

## Domain Modules

### Module Structure Pattern

Each domain module follows this structure:

```
domain/{module}/
├── __init__.py
├── entities/                  # Domain entities
│   ├── __init__.py
│   └── {entity}.py           # Entity classes
├── value_objects/             # Immutable value types
│   ├── __init__.py
│   └── {vo}.py               # Value object classes
├── ports/                     # Interface definitions
│   ├── __init__.py
│   └── {port}_repository.py  # Repository interfaces
└── services/                  # Domain services
    ├── __init__.py
    └── {service}.py          # Business logic services
```

### Current Domain Modules

| Module | Purpose | Key Entities |
|--------|---------|--------------|
| `chat` | Conversation management | Conversation, Message |
| `guest` | Guest user handling | GuestUser, GuestConversation |
| `alerts` | Risk alerts | RiskAlert |
| `portfolio` | Portfolio tracking | Portfolio, Position |
| `transactions` | Transaction tracking | Transaction |
| `hunter` | Market intelligence | Sentiment |
| `ultra` | Advanced trading | - |
| `graph` | GraphRAG | - |
| `markets` | Market data | - |
| `ml` | Machine learning | - |
| `preferences` | User preferences | - |
| `projects` | User projects | Project |
| `atlas` | Geographic data | - |
| `bitcoin` | Bitcoin features | - |
| `comparison` | Asset comparison | - |
| `dashboard` | Dashboard data | - |
| `search` | Search functionality | - |

---

## Application Layer Structure

### Commands (Write Operations)

```
application/{module}/commands/
├── __init__.py
├── create_{entity}.py        # Create operation
├── update_{entity}.py        # Update operation
├── delete_{entity}.py        # Delete operation
└── {action}_{entity}.py      # Custom actions
```

**Example: Create Conversation**

```python
# application/chat/commands/create_conversation.py
class CreateConversation:
    def __init__(
        self,
        repository: ConversationRepository,  # Port from domain
    ):
        self._repository = repository

    async def execute(self, user_id: UUID) -> Conversation:
        conversation = Conversation.create(user_id)
        await self._repository.save(conversation)
        return conversation
```

### Queries (Read Operations)

```
application/{module}/queries/
├── __init__.py
├── get_{entity}.py           # Get single entity
├── list_{entities}.py        # List entities
└── search_{entities}.py      # Search operations
```

**Example: Get Conversation**

```python
# application/chat/queries/get_conversation.py
class GetConversation:
    def __init__(
        self,
        gateway: ConversationQueryGateway,  # Query-optimized
    ):
        self._gateway = gateway

    async def execute(self, conversation_id: UUID) -> ConversationQueryModel:
        return await self._gateway.get_by_id(conversation_id)
```

---

## Infrastructure Adapters

### Adapter Pattern

```
infrastructure/adapters/
├── {module}/
│   ├── __init__.py
│   └── {port}_adapter.py     # Port implementation
└── agent_squad/
    ├── llm_client_vertex_ai.py    # Vertex AI client
    ├── llm_client_deepinfra.py    # DeepInfra client
    └── llm_client_with_fallback.py # Fallback wrapper
```

**Example: Repository Adapter**

```python
# infrastructure/adapters/conversation_repository_sqla.py
class ConversationRepositorySqla(ConversationRepository):
    """Implements ConversationRepository port using SQLAlchemy"""
    
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, conversation: Conversation) -> None:
        # SQLAlchemy implementation
        pass
```

---

## Presentation Controllers

### Controller Structure

```
presentation/http/controllers/
├── api_v1_router.py           # Main v1 router
├── root_router.py             # Root endpoints
│
├── {module}/                  # Module endpoints
│   ├── __init__.py
│   ├── router.py             # Module router
│   ├── {action}.py           # Action handlers
│   └── schemas.py            # Request/Response models
```

**Example: Chat Controller**

```python
# presentation/http/controllers/chat/router.py
router = ErrorAwareRouter(prefix="/chat", tags=["chat"])

@router.post("/conversations")
async def create_conversation(
    interactor: CreateConversation = Depends(),  # From Dishka
) -> ConversationResponse:
    conversation = await interactor.execute(user_id)
    return ConversationResponse.from_domain(conversation)
```

---

## Dependency Injection Setup

### Provider Structure

```
setup/ioc/
├── __init__.py
├── domain.py                  # Domain providers
├── application.py             # Application providers
├── infrastructure.py          # Infrastructure providers
├── presentation.py            # Presentation providers
├── agent_squad_infrastructure.py  # Agent Squad providers
└── provider_registry.py       # Provider registration
```

**Example: Provider**

```python
# setup/ioc/infrastructure.py
class InfrastructureProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_conversation_repository(
        self,
        session: AsyncSession,
    ) -> ConversationRepository:
        return ConversationRepositorySqla(session)
```

---

## Configuration Structure

### Environment Configuration

```
config/{env}/
├── config.toml               # Main configuration
├── .secrets.toml             # Secrets (not in git)
├── export.toml               # Env vars to export
└── docker-compose.yaml       # Docker services
```

### Configuration Sections

```toml
# config.toml structure
[app]
name = "anvil-backend"
debug = false

[database]
host = "localhost"
port = 5432
name = "anvil"

[redis]
host = "localhost"
port = 6379

[llm_provider]
primary_provider = "vertex_ai"
fallback_provider = "deepinfra"

[agent_squad]
enabled = true
intent_classification_model = "gpt-4o-mini"

# ... more sections
```

---

## Testing Structure

### Test Organization

```
tests/
├── conftest.py               # Shared fixtures
├── factories/                # Test data factories
│
├── unit/                     # Unit tests
│   ├── domain/              # Domain layer tests
│   ├── application/         # Application layer tests
│   └── infrastructure/      # Infrastructure tests
│
├── integration/              # Integration tests
│   ├── api/                 # API endpoint tests
│   └── database/            # Database tests
│
└── fixtures/                 # Test fixtures
    ├── data/                # Test data files
    └── mocks/               # Mock implementations
```

### Test Naming Convention

```python
# test_{module}_{feature}.py
# Example: test_chat_create_conversation.py

def test_{action}_{scenario}_{expected_result}():
    """Test description"""
    pass

# Example:
def test_create_conversation_with_valid_user_returns_conversation():
    pass
```

---

## File Naming Conventions

### Python Files

| Type | Pattern | Example |
|------|---------|---------|
| Entity | `{entity}.py` | `conversation.py` |
| Value Object | `{name}.py` | `message_role.py` |
| Port | `{name}_repository.py` | `conversation_repository.py` |
| Adapter | `{name}_adapter.py` | `conversation_repository_sqla.py` |
| Command | `{action}_{entity}.py` | `create_conversation.py` |
| Query | `{action}_{entities}.py` | `list_conversations.py` |
| Controller | `router.py` or `{action}.py` | `router.py`, `send_message.py` |
| Test | `test_{module}_{feature}.py` | `test_chat_create.py` |

### Directories

- Use `snake_case` for all directory names
- Use plural for collections (e.g., `entities/`, `adapters/`)
- Use singular for specific items (e.g., `chat/`, `user/`)

---

## Code Organization Principles

### 1. Dependency Direction

```
Presentation → Application → Domain
Infrastructure → Domain
```

- Inner layers define interfaces (ports)
- Outer layers implement interfaces (adapters)
- Never import from outer layers in inner layers

### 2. Module Independence

- Each domain module is self-contained
- Shared code goes in `common/` directories
- Cross-module communication through domain events (future)

### 3. CQRS Separation

- Commands for writes and business-critical reads
- Queries for optimized read operations
- Different models for commands vs queries

### 4. Single Responsibility

- One class per file for entities and major components
- Keep files under 500 lines
- Keep functions under 50 lines

---

## Adding New Features

### 1. Domain First

```bash
# Create domain structure
src/app/domain/{feature}/
├── entities/{entity}.py
├── value_objects/
├── ports/{repository}.py
└── services/
```

### 2. Application Layer

```bash
# Create use cases
src/app/application/{feature}/
├── commands/{action}.py
└── queries/{query}.py
```

### 3. Infrastructure

```bash
# Create adapters
src/app/infrastructure/adapters/{feature}/
└── {port}_adapter.py
```

### 4. Presentation

```bash
# Create controllers
src/app/presentation/http/controllers/{feature}/
├── router.py
└── schemas.py
```

### 5. Wire Dependencies

```python
# setup/ioc/{layer}.py
# Add provider for new components
```

---

**Last Updated**: January 2, 2026
