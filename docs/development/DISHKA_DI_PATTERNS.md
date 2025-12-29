# Dishka Dependency Injection Patterns

**Purpose**: Comprehensive guide to DI patterns, provider registration, scopes, and test mocking in the Anvil DeFi project.

**Audience**: Backend developers, test engineers, new team members

**Last Updated**: 2025-12-29

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Provider Registration Order](#provider-registration-order)
3. [Scope Rules](#scope-rules)
4. [Test Mocking Patterns](#test-mocking-patterns)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

This project uses **Dishka** for dependency injection, following **Hexagonal Architecture** principles.

### Why Dishka?

- **Framework Independence**: Unlike FastAPI's built-in DI, Dishka keeps domain/application layers free from framework dependencies
- **Explicit Scopes**: Clear APP vs REQUEST scope management
- **Type Safety**: Full type hint support with async/await
- **Testing**: Easy provider override for mocking

### Dependency Flow

```
Domain Layer (Core Business Logic)
    ↓ defines ports (interfaces)
Application Layer (Use Cases)
    ↓ depends on domain ports
Infrastructure Layer (Adapters)
    ↓ implements domain ports
Presentation Layer (HTTP/WebSocket)
    ↓ uses application interactors
```

**Key Principle**: Inner layers define interfaces, outer layers implement them.

---

## Provider Registration Order

**File**: `src/app/setup/ioc/provider_registry.py`

```python
def get_providers() -> Iterable[Provider]:
    return (
        DomainProvider(),           # 1. Domain services
        ApplicationProvider(),       # 2. Application interactors
        infrastructure_provider(),   # 3. Infrastructure adapters
        PresentationProvider(),      # 4. HTTP controllers
        SettingsProvider(),          # 5. Configuration
        # ... specialized providers
        AgentSquadDomainProvider(),
        AgentSquadInfrastructureProvider(),
        AgentSquadApplicationProvider(),
        CacheProvider(),
        ChatPhase2Provider(),
        AaveProvider(),
    )
```

### Registration Order Rules

1. **Core First**: Domain → Application → Infrastructure → Presentation
2. **Dependencies Before Dependents**: Providers are registered in dependency order
3. **Specialized After Core**: Feature-specific providers (AgentSquad, Cache, etc.) come after core

**Important**: Later providers can override earlier ones for the same type!

---

## Scope Rules

Dishka supports two main scopes:

### APP Scope (Singleton)

**Lifetime**: Created once per application startup, shared across all requests

**Use Cases**:
- Database connection pools
- Configuration objects
- External API clients
- Cache connections

**Example**:
```python
from dishka import Provider, Scope, provide

class InfrastructureProvider(Provider):
    scope = Scope.APP  # Singleton

    @provide
    async def provide_database_pool(self) -> DatabasePool:
        """One pool for entire application."""
        return DatabasePool(url="postgresql://...")
```

### REQUEST Scope (Per-Request)

**Lifetime**: Created fresh for each HTTP request/WebSocket connection

**Use Cases**:
- Database sessions
- User context
- Request-specific services
- Transaction management

**Example**:
```python
from dishka import Provider, Scope, provide

class ApplicationProvider(Provider):
    scope = Scope.REQUEST  # Per-request

    @provide
    async def provide_database_session(
        self, pool: DatabasePool
    ) -> AsyncSession:
        """Fresh session per request."""
        async with pool.session() as session:
            yield session  # Auto-cleanup after request
```

### Scope Interaction Rules

1. **APP can depend on APP** ✅
2. **REQUEST can depend on APP** ✅ (common pattern)
3. **APP CANNOT depend on REQUEST** ❌ (circular dependency)

**Example**:
```python
class RequestScopeProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def provide_service(
        self,
        db_pool: DatabasePool,  # ✅ APP scope dependency
    ) -> MyService:
        return MyService(db_pool)
```

---

## Test Mocking Patterns

**File**: `src/app/setup/ioc/testing.py`

Test mocking in Dishka works by **provider override**: test providers registered AFTER production providers override them.

### Pattern 1: Mock External APIs

**Production**:
```python
# src/app/setup/ioc/infrastructure.py
class InfrastructureProvider(Provider):
    @provide
    async def provide_llm_gateway(self) -> LLMGateway:
        return OpenAILLMGateway(api_key="...")
```

**Test**:
```python
# src/app/setup/ioc/testing.py
class TestInfrastructureProvider(Provider):
    @provide
    async def provide_llm_gateway(self) -> LLMGateway:
        return MockLLMGateway()  # Overrides production!
```

**Container Setup**:
```python
# tests/conftest.py
def get_test_providers():
    return [
        *get_providers(),  # Production providers
        TestInfrastructureProvider(),  # Override with mocks
    ]
```

**Result**: `TestInfrastructureProvider.provide_llm_gateway()` overrides production `LLMGateway`.

### Pattern 2: Mock Repositories

**Production**:
```python
class ApplicationProvider(Provider):
    @provide
    async def provide_user_repository(
        self, session: AsyncSession
    ) -> UserRepository:
        return SQLAlchemyUserRepository(session)
```

**Test**:
```python
class TestApplicationProvider(Provider):
    @provide
    async def provide_user_repository(self) -> UserRepository:
        return InMemoryUserRepository()  # Fast, no DB
```

### Pattern 3: Partial Mocking

Sometimes you want to mock only specific providers:

```python
def get_integration_test_providers():
    """Integration tests: Real DB, mocked external APIs."""
    return [
        *get_providers(),  # All production providers
        TestExternalApisProvider(),  # Only mock external APIs
        # Real DB, real domain logic, real application layer
    ]
```

### Common Test Fixtures

```python
# tests/conftest.py
import pytest
from dishka import make_async_container

@pytest.fixture
async def container():
    """DI container for tests."""
    c = make_async_container(*get_test_providers())
    yield c
    await c.close()

@pytest.fixture
async def user_repository(container):
    """Get user repository from container."""
    async with container() as request_container:
        return await request_container.get(UserRepository)
```

---

## Common Patterns

### Pattern 1: Injecting Configuration

**Provider**:
```python
from app.setup.config.loader import load_full_config

class SettingsProvider(Provider):
    scope = Scope.APP

    @provide
    def provide_config(self) -> dict:
        return load_full_config()

    @provide
    def provide_database_url(self, config: dict) -> DatabaseURL:
        return config["database"]["url"]
```

**Usage**:
```python
class MyService:
    def __init__(self, db_url: DatabaseURL):
        self.db_url = db_url
```

### Pattern 2: Factory Pattern

**Provider**:
```python
class DomainProvider(Provider):
    @provide
    def provide_user_factory(self) -> UserFactory:
        return UserFactory()
```

**Usage**:
```python
class CreateUserInteractor:
    def __init__(self, user_factory: UserFactory):
        self.user_factory = user_factory

    async def execute(self, email: str) -> User:
        return self.user_factory.create(email=email)
```

### Pattern 3: Conditional Providers

**Provider**:
```python
class InfrastructureProvider(Provider):
    @provide
    async def provide_cache(self, config: dict) -> Cache:
        if config["cache"]["type"] == "redis":
            return RedisCache(url=config["cache"]["url"])
        else:
            return InMemoryCache()
```

### Pattern 4: Async Cleanup

**Provider**:
```python
class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    async def provide_http_client(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient()
        yield client
        await client.aclose()  # Auto cleanup on shutdown
```

---

## Troubleshooting

### Issue 1: "Cannot resolve dependency for X"

**Cause**: No provider registered for type `X`

**Solution**: Add a provider method:
```python
@provide
def provide_x(self) -> X:
    return X()
```

### Issue 2: "Circular dependency detected"

**Cause**: A depends on B, B depends on A

**Solution**: Refactor to break cycle, often by introducing an interface:
```python
# Before (circular)
class A:
    def __init__(self, b: B): ...

class B:
    def __init__(self, a: A): ...

# After (using interface)
class A:
    def __init__(self, b_interface: BInterface): ...

class B(BInterface):
    # No dependency on A
```

### Issue 3: "Scope mismatch"

**Cause**: APP scope provider trying to depend on REQUEST scope

**Solution**: Change dependency to APP scope or make provider REQUEST scope:
```python
# Wrong
class AppScopeProvider(Provider):
    scope = Scope.APP

    @provide
    def provide_service(
        self, session: AsyncSession  # REQUEST scope!
    ) -> Service:
        ...

# Right
class RequestScopeProvider(Provider):
    scope = Scope.REQUEST  # Match dependency scope

    @provide
    def provide_service(
        self, session: AsyncSession
    ) -> Service:
        ...
```

### Issue 4: Mock not working

**Cause**: Test provider registered BEFORE production provider

**Solution**: Ensure test providers come AFTER production in registration order:
```python
# Wrong
providers = [
    TestProvider(),  # Too early!
    *get_providers(),
]

# Right
providers = [
    *get_providers(),
    TestProvider(),  # Overrides production
]
```

### Issue 5: "Provider already registered"

**Cause**: Same provider registered multiple times

**Solution**: Check `get_providers()` doesn't duplicate providers

---

## Best Practices

1. **One Provider Per Layer**: DomainProvider, ApplicationProvider, InfrastructureProvider
2. **Explicit Dependencies**: Always declare dependencies in `__init__`, never use globals
3. **Prefer Interfaces**: Depend on abstract ports, not concrete implementations
4. **Test with Mocks**: Use test providers to override external dependencies
5. **Scope Appropriately**: Use APP for singletons, REQUEST for per-request
6. **Document Complex Providers**: Add docstrings explaining provider purpose

---

## References

- [Dishka Documentation](https://dishka.readthedocs.io/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- Project Provider Files: `src/app/setup/ioc/`
- Test Mocks: `src/app/setup/ioc/testing.py`

---

**Questions or Issues?** Open a GitHub issue or ask in #backend-dev Slack channel.
