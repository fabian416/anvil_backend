# Architecture Documentation

**Purpose**: System architecture, design patterns, and technical decisions  
**Audience**: Architects, senior developers, technical leads

---

## 📐 Architecture Overview

Anvil Backend follows **Hexagonal Architecture** (Clean Architecture) principles with strict layer separation and dependency inversion.

### Core Principles

1. **Layer Separation**: Domain → Application → Infrastructure → Presentation
2. **Dependency Inversion**: Inner layers define interfaces, outer layers implement
3. **Modular Organization**: Features organized by business domain
4. **CQRS Pattern**: Commands and queries separated
5. **Testability**: Easy to test without infrastructure dependencies

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────┐
│         Presentation Layer (HTTP)           │
│   Controllers, Request/Response Schemas     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Application Layer (Use Cases)       │
│    Commands, Queries, Interactors          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Domain Layer (Business Logic)       │
│  Entities, Services, Value Objects, Ports   │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│      Infrastructure Layer (Adapters)        │
│  Database, External APIs, Messaging, Cache   │
└─────────────────────────────────────────────┘
```

### Layer Responsibilities

- **Domain**: Pure business logic, no dependencies
- **Application**: Use cases, orchestrates domain logic
- **Infrastructure**: External system integrations
- **Presentation**: HTTP interface, input/output handling

---

## 📁 Project Structure

### Modular Organization

```
src/app/
├── domain/                    # Domain layer (modular)
│   ├── {module}/             # Feature modules
│   │   ├── entities/         # Domain entities
│   │   ├── value_objects/    # Value objects
│   │   ├── ports/            # Interfaces
│   │   └── services/         # Domain services
│   └── ...
│
├── application/               # Application layer (modular)
│   ├── {module}/             # Feature modules
│   │   ├── commands/         # Write operations
│   │   ├── queries/          # Read operations
│   │   └── services/         # Application services
│   └── ...
│
├── infrastructure/            # Infrastructure layer
│   ├── adapters/             # Port implementations
│   ├── persistence_sqla/     # Database adapters
│   ├── celery/               # Background tasks
│   └── ...
│
└── presentation/              # Presentation layer
    └── http/                  # HTTP interface
        ├── controllers/       # Route handlers
        └── schemas/           # Request/response models
```

### Module Examples

- `domain/chat/` - Chat domain logic
- `domain/transactions/` - Transaction domain logic
- `domain/portfolio/` - Portfolio domain logic
- `application/chat/` - Chat use cases
- `application/transactions/` - Transaction use cases

---

## 🔄 Data Flow

### Request Flow

1. **HTTP Request** → Presentation Layer (Controller)
2. **Validation** → Request schema validation
3. **Delegation** → Application Layer (Interactor)
4. **Business Logic** → Domain Layer (Entities, Services)
5. **Persistence** → Infrastructure Layer (Repository Adapter)
6. **Response** → Presentation Layer (Response Schema)

### Command Flow (Write)

```
Controller → Command Interactor → Domain Service → Repository → Database
```

### Query Flow (Read)

```
Controller → Query Interactor → Query Gateway → Database → Response Model
```

---

## 🧩 Design Patterns

### Hexagonal Architecture

- **Ports**: Interfaces defined in Domain layer
- **Adapters**: Implementations in Infrastructure layer
- **Dependency Inversion**: Domain defines contracts

### CQRS (Command Query Responsibility Segregation)

- **Commands**: Write operations, return entities
- **Queries**: Read operations, return query models
- **Separation**: Different models for reads and writes

### Dependency Injection

- **Framework**: Dishka (framework-agnostic)
- **Scopes**: APP, REQUEST scopes
- **Registration**: Providers in `setup/ioc/`

---

## 📚 Documentation

### Core Architecture

- **[Hexagonal Architecture](hexagonal-architecture.md)** - Clean architecture patterns
- **[System Design](system-design.md)** - Overall system design
- **[Data Flow](data-flow.md)** - Request/response flows
- **[Integration Patterns](integration-patterns.md)** - How components integrate

### Patterns & Practices

- **[CQRS Pattern](cqrs.md)** - Command Query Separation
- **[Dependency Injection](dependency-injection.md)** - DI patterns
- **[Error Handling](error-handling.md)** - Error handling patterns
- **[Testing Architecture](testing-architecture.md)** - Testing patterns

### Module Architecture

- **[Chat Architecture](../features/chat/architecture.md)** - Chat system design
- **[GraphRAG Architecture](../features/graphrag/architecture.md)** - GraphRAG design
- **[Agent System Architecture](../features/agents/architecture.md)** - Agent orchestration

---

## 🔍 Key Concepts

### Domain Layer

- **Entities**: Business objects with identity
- **Value Objects**: Immutable objects without identity
- **Domain Services**: Business logic that doesn't fit in entities
- **Ports**: Interfaces for external dependencies

### Application Layer

- **Commands**: Write operations (create, update, delete)
- **Queries**: Read operations (get, list, search)
- **Interactors**: Orchestrate domain logic
- **Services**: Application-level services

### Infrastructure Layer

- **Adapters**: Implement domain/application ports
- **Repositories**: Database persistence
- **Gateways**: External API integrations
- **Background Tasks**: Celery tasks

### Presentation Layer

- **Controllers**: HTTP route handlers
- **Schemas**: Request/response models
- **Middleware**: Cross-cutting concerns
- **Error Handlers**: Error response formatting

---

## 🎯 Design Decisions

### Why Hexagonal Architecture?

- **Testability**: Easy to test domain logic in isolation
- **Flexibility**: Swap implementations without changing business logic
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to add new features

### Why Modular Structure?

- **Organization**: Features grouped by business domain
- **Scalability**: Easy to add new modules
- **Team Collaboration**: Teams can work on different modules
- **Maintainability**: Clear module boundaries

### Why CQRS?

- **Performance**: Optimized models for reads
- **Scalability**: Separate read/write scaling
- **Flexibility**: Different models for different use cases
- **Clarity**: Clear separation of concerns

---

## 📊 System Components

### Core Components

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM and database toolkit
- **Dishka**: Dependency injection
- **Celery**: Background task processing
- **Redis**: Caching and message broker
- **PostgreSQL**: Primary database

### External Integrations

- **Stripe**: Payment processing
- **Mailgun**: Email delivery
- **OpenAI**: LLM services
- **MCP Servers**: External data providers
- **Agno**: Agent runtime

---

## 🔗 Related Documentation

- **[Project Structure](../steering/structure.md)** - Detailed structure guide
- **[Developer Guide](../developer/README.md)** - Developer documentation
- **[API Reference](../api/README.md)** - API documentation
- **[Features](../features/README.md)** - Feature documentation

---

**Last Updated**: December 19, 2025

