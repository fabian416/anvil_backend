# DI Provider Patterns Documentation - Implementation Plan

**Initiative**: Document Dishka DI patterns for test mocking
**Timeline**: 1 day
**Risk Level**: Very Low
**Dependencies**: None (can run in parallel with other initiatives)

---

## Phase 1: Investigation & Pattern Extraction (Morning)

### 1.1 Document Current DI Setup

**Goal**: Create comprehensive documentation of how DI works in the project

**Topics to Document**:

1. **Provider Registration Order**
2. **Scope Rules** (APP vs REQUEST)
3. **Type Matching** (how Dishka resolves providers)
4. **Override Patterns** (how test mocks override production)
5. **Common Pitfalls**

---

### 1.2 Experiment with Provider Precedence

**Create Test Cases**:

```python
# tests/unit/ioc/test_provider_precedence.py (NEW)

import pytest
from dishka import make_container, Provider, Scope, provide


class ProductionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_service(self) -> str:
        return "production"


class TestProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_service(self) -> str:
        return "test"


@pytest.mark.asyncio
async def test_last_provider_wins():
    """Test that last provider has precedence."""
    # Production first, test last
    container = make_container(
        ProductionProvider(),
        TestProvider(),
    )

    async with container() as request_container:
        service = await request_container.get(str)
        assert service == "test", "Last provider should win"


@pytest.mark.asyncio
async def test_scope_mismatch_behavior():
    """Test what happens when scopes don't match."""
    class AppScopeProvider(Provider):
        scope = Scope.APP

        @provide
        def provide_service(self) -> str:
            return "app_scope"

    class RequestScopeProvider(Provider):
        scope = Scope.REQUEST

        @provide
        def provide_service(self) -> str:
            return "request_scope"

    # What happens when scopes differ?
    container = make_container(
        AppScopeProvider(),
        RequestScopeProvider(),
    )

    async with container() as request_container:
        service = await request_container.get(str)
        # Document the actual behavior
        print(f"Result: {service}")


@pytest.mark.asyncio
async def test_provider_method_level_scope():
    """Test method-level scope override."""
    class MixedScopeProvider(Provider):
        scope = Scope.REQUEST  # Class level

        @provide(scope=Scope.APP)  # Method level override
        def provide_app_service(self) -> str:
            return "app_service"

        @provide  # Inherits REQUEST from class
        def provide_request_service(self) -> int:
            return 42

    container = make_container(MixedScopeProvider())

    async with container() as request_container:
        app_svc = await request_container.get(str)
        req_svc = await request_container.get(int)

        assert app_svc == "app_service"
        assert req_svc == 42
```

**Run Experiments**:

```bash
./env/bin/python -m pytest tests/unit/ioc/test_provider_precedence.py -v -s
```

**Document Results**:
- Which provider wins when scopes match?
- Which provider wins when scopes differ?
- How does method-level scope override work?

---

## Phase 2: Create DI Documentation (Afternoon)

### 2.1 Developer Guide

**File**: `docs/development/dependency-injection.md` (NEW)

```markdown
# Dependency Injection Guide

## Overview

This project uses [Dishka](https://github.com/reagento/dishka) for dependency injection, following hexagonal architecture principles.

## Core Concepts

### Providers

Providers define how to create dependencies:

```python
from dishka import Provider, Scope, provide

class MyProvider(Provider):
    scope = Scope.REQUEST  # Default scope for all methods

    @provide
    def provide_service(self, dependency: SomeDependency) -> MyService:
        return MyService(dependency)

    @provide(scope=Scope.APP)  # Override scope for this method
    def provide_singleton(self) -> SingletonService:
        return SingletonService()
```

### Scopes

**APP (Application)**: Single instance for entire app lifetime
- Use for: Configuration, database engines, singleton services
- Example: `AppSettings`, `AsyncEngine`

**REQUEST**: New instance per HTTP request
- Use for: Database sessions, user-scoped services, request handlers
- Example: `AsyncSession`, `UserRepository`, `SendMessage`

### Provider Registration

Providers are registered in order:

```python
# tests/conftest.py
container = make_container(
    *get_providers(),                    # Production providers (1st)
    *get_integration_test_providers(),   # Test overrides (2nd, WINS)
    context={AppSettings: test_settings},
)
```

**Rule**: **Last provider wins** when types and scopes match.

---

## Testing Patterns

### Pattern 1: Mock Service in Tests

**Goal**: Replace production service with test mock

**Production Provider**:
```python
# src/app/setup/ioc/infrastructure.py
class InfrastructureProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_llm_gateway(self, settings: AppSettings) -> LLMGateway:
        return LLMGatewayImpl(factory=LLMProviderFactory())
```

**Test Provider**:
```python
# src/app/setup/ioc/testing.py
class TestMockProvider(Provider):
    scope = Scope.REQUEST  # MUST MATCH production scope

    @provide
    def provide_llm_gateway(self) -> LLMGateway:  # MUST MATCH type
        return MockLLMGateway()
```

**Registration**:
```python
# tests/conftest.py
container = make_container(
    InfrastructureProvider(),  # Production (1st)
    TestMockProvider(),        # Test (2nd, wins)
)
```

**Result**: Tests use `MockLLMGateway` ✅

---

### Pattern 2: Override Database Session

**Production**:
```python
@provide(scope=Scope.REQUEST)
async def provide_db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(engine)() as session:
        yield session
```

**Test**:
```python
@provide(scope=Scope.REQUEST)
async def provide_test_db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(engine)() as session:
        yield session
        await session.rollback()  # Rollback after test
```

**Key**: Return type must match exactly (`AsyncIterator[AsyncSession]`)

---

### Pattern 3: Conditional Production Behavior

**Don't do this** (test-aware production code):
```python
# ❌ BAD
class MyService:
    def __init__(self, is_test_mode: bool = False):
        self._is_test = is_test_mode

    async def do_something(self):
        if self._is_test:
            return "mock_result"
        return await self._real_operation()
```

**Do this** (separate implementations):
```python
# ✅ GOOD

# Production
class ProductionService(MyServicePort):
    async def do_something(self):
        return await self._real_operation()

# Test
class MockService(MyServicePort):
    async def do_something(self):
        return "mock_result"

# DI Provider (test)
@provide
def provide_service(self) -> MyServicePort:
    return MockService()
```

---

## Common Pitfalls

### Pitfall 1: Scope Mismatch

**Problem**: Production uses `Scope.REQUEST`, test uses `Scope.APP`

```python
# Production
class ProductionProvider(Provider):
    scope = Scope.REQUEST  # ← REQUEST

    @provide
    def provide_service(self) -> MyService:
        return ProductionService()

# Test
class TestProvider(Provider):
    scope = Scope.APP  # ← APP (WRONG!)

    @provide
    def provide_service(self) -> MyService:
        return MockService()
```

**Result**: Mock doesn't override! Production service still used. ❌

**Fix**: Match scopes exactly:
```python
class TestProvider(Provider):
    scope = Scope.REQUEST  # ← Match production
```

---

### Pitfall 2: Type Mismatch

**Problem**: Test provides different type than production expects

```python
# Production expects
@provide
def provide_repository(self) -> UserRepository:
    ...

# Test provides
@provide
def provide_repository(self) -> MockUserRepository:  # Different type!
    ...
```

**Result**: Dishka can't match types, override fails. ❌

**Fix**: Return base class/interface:
```python
@provide
def provide_repository(self) -> UserRepository:  # Same type
    return MockUserRepository()  # Returns subclass
```

---

### Pitfall 3: Provider Order

**Problem**: Test provider registered before production

```python
# ❌ WRONG ORDER
container = make_container(
    TestMockProvider(),        # 1st (loses)
    ProductionProvider(),      # 2nd (wins)
)
```

**Result**: Production provider overrides test mock! ❌

**Fix**: Test providers LAST:
```python
# ✅ CORRECT ORDER
container = make_container(
    ProductionProvider(),      # 1st
    TestMockProvider(),        # 2nd (wins)
)
```

---

### Pitfall 4: Async Iterator Return Type

**Problem**: Forgetting `AsyncIterator` wrapper

```python
# ❌ WRONG
@provide(scope=Scope.REQUEST)
async def provide_session(engine) -> AsyncSession:
    session = async_sessionmaker(engine)()
    yield session
    await session.close()
```

**Error**: Type mismatch (generator vs AsyncSession)

**Fix**: Use `AsyncIterator` return type:
```python
# ✅ CORRECT
@provide(scope=Scope.REQUEST)
async def provide_session(engine) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(engine)() as session:
        yield session
```

---

## Debugging DI Issues

### Step 1: Verify Provider Registration

```python
# Add logging to conftest.py
print("Registered providers:")
for provider in get_providers():
    print(f"  - {provider.__class__.__name__}")
for provider in get_integration_test_providers():
    print(f"  - {provider.__class__.__name__} (TEST OVERRIDE)")
```

### Step 2: Check Scope Match

```python
# Production
print(f"Production scope: {ProductionProvider.scope}")

# Test
print(f"Test scope: {TestMockProvider.scope}")

# Should be the same!
```

### Step 3: Verify Type Annotations

```python
import inspect

prod_method = ProductionProvider.provide_service
test_method = TestMockProvider.provide_service

prod_return = inspect.signature(prod_method).return_annotation
test_return = inspect.signature(test_method).return_annotation

print(f"Production returns: {prod_return}")
print(f"Test returns: {test_return}")

assert prod_return == test_return, "Type mismatch!"
```

### Step 4: Use Dishka Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("dishka").setLevel(logging.DEBUG)

container = make_container(...)
# Check logs for provider resolution
```

---

## Best Practices

### 1. Always Match Scopes

✅ **DO**: Match production and test provider scopes exactly
❌ **DON'T**: Assume `Scope.APP` is "safer" for tests

### 2. Use Base Classes for Return Types

✅ **DO**: Return abstract base class or interface
❌ **DON'T**: Return concrete implementation class in type hint

### 3. Test Providers Last

✅ **DO**: Register test providers after production providers
❌ **DON'T**: Mix test and production provider order

### 4. Document Provider Dependencies

```python
@provide
def provide_service(
    self,
    dep1: Dependency1,  # Injected by Dishka
    dep2: Dependency2,  # Injected by Dishka
) -> MyService:
    """
    Provide MyService.

    Dependencies:
    - dep1: Description of what this provides
    - dep2: Description of what this provides

    Scope: REQUEST (new instance per request)
    """
    return MyService(dep1, dep2)
```

### 5. Keep Providers Simple

✅ **DO**: Simple factory methods that construct instances
❌ **DON'T**: Complex logic, conditional behavior, or side effects

---

## Testing Checklist

Before adding new provider:

- [ ] Scope matches all consumers
- [ ] Return type matches interface/base class
- [ ] No complex logic in provider method
- [ ] Documented dependencies and scope
- [ ] Test provider registered last
- [ ] Verified with actual test run

---

## Examples

### Full Example: User Repository Mock

**Domain Port**:
```python
# src/app/domain/ports/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        ...
```

**Production Implementation**:
```python
# src/app/infrastructure/adapters/persistence/user_repository_sqla.py
class UserRepositorySQLA(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        return result.scalar_one_or_none()
```

**Production Provider**:
```python
# src/app/setup/ioc/infrastructure.py
class InfrastructureProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_user_repository(
        self,
        session: AsyncSession,
    ) -> UserRepository:
        return UserRepositorySQLA(session)
```

**Test Implementation**:
```python
# tests/mocks/user_repository_mock.py
class MockUserRepository(UserRepository):
    def __init__(self):
        self._users = {}

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def add_mock_user(self, user: User):
        self._users[user.id] = user
```

**Test Provider**:
```python
# src/app/setup/ioc/testing.py
class TestMockProvider(Provider):
    scope = Scope.REQUEST  # Match production!

    @provide
    def provide_user_repository(self) -> UserRepository:  # Match type!
        return MockUserRepository()
```

**Test Usage**:
```python
# tests/integration/test_user_service.py
async def test_get_user(test_app):
    # DI automatically injects MockUserRepository
    # No manual mocking needed!

    response = await client.get("/users/123")
    assert response.status_code == 200
```

---

## Troubleshooting Guide

### "Mock not being used in tests"

**Check**:
1. ✅ Scopes match? (`print(scope)` in both providers)
2. ✅ Types match? (`print(return_annotation)`)
3. ✅ Test provider registered last? (check conftest.py)
4. ✅ Provider actually has `@provide` decorator?

### "Type error in DI resolution"

**Check**:
1. ✅ Return type annotation present?
2. ✅ Async iterator using `AsyncIterator[T]` not `T`?
3. ✅ All dependencies have providers?

### "Singleton behaving like request-scoped"

**Check**:
1. ✅ Scope is `Scope.APP` not `Scope.REQUEST`?
2. ✅ Method-level scope not overriding class scope?

---

## Resources

- [Dishka Documentation](https://github.com/reagento/dishka)
- [Hexagonal Architecture](./hexagonal-architecture.md)
- [Testing Guide](./testing.md)
```

---

### 2.2 Testing Guide Addendum

**File**: `docs/development/testing.md` (ADD SECTION)

```markdown
## DI Mocking in Integration Tests

### Quick Reference

**Override a service in tests**:

1. Create mock implementation
2. Add provider to `TestMockProvider`
3. Match scope and type exactly
4. Test provider is already registered last ✅

### Example

```python
# 1. Mock implementation
class MockEmailService(EmailService):
    async def send(self, to: str, subject: str, body: str):
        print(f"Mock email to {to}: {subject}")

# 2. Add provider
class TestMockProvider(Provider):
    scope = Scope.REQUEST  # Match production

    @provide
    def provide_email_service(self) -> EmailService:  # Match type
        return MockEmailService()

# 3. Use in tests (automatic!)
async def test_user_registration(client):
    # Email service automatically mocked
    response = await client.post("/register", json={...})
    # No manual setup needed!
```

See [Dependency Injection Guide](./dependency-injection.md) for details.
```

---

## Phase 3: Create Quick Reference Card (Afternoon)

**File**: `docs/quick-reference/di-patterns.md` (NEW)

```markdown
# DI Patterns Quick Reference

## Mock a Service

```python
# In src/app/setup/ioc/testing.py

@provide(scope=Scope.REQUEST)  # ← Match production scope
def provide_my_service(self) -> MyServiceInterface:  # ← Match type
    return MockMyService()
```

## Scope Cheat Sheet

| Scope | Lifetime | Use For |
|-------|----------|---------|
| `APP` | Entire app | Singletons, config, engines |
| `REQUEST` | Per HTTP request | Sessions, repositories, handlers |

## Override Checklist

- [ ] Scope matches production
- [ ] Type annotation matches
- [ ] Test provider registered LAST
- [ ] Mock has `@provide` decorator

## Debug Command

```python
# In conftest.py (temporary)
import logging
logging.getLogger("dishka").setLevel(logging.DEBUG)
```
```

---

## Phase 4: Add Inline Documentation (Ongoing)

### Update Existing Providers

Add docstrings explaining scope and override behavior:

```python
# src/app/setup/ioc/testing.py

class TestMockProvider(Provider):
    """
    Test provider for integration testing.

    Overrides production dependencies with mocks for:
    - LLM gateway (avoid API costs)
    - Email service (no real emails)
    - Payment service (no real charges)

    Registration: This provider is registered LAST in conftest.py,
    so all provides here override production providers.

    Scope: All methods use Scope.REQUEST to match production providers.
    """

    scope = Scope.REQUEST

    @provide
    def provide_llm_gateway(self) -> LLMGateway:
        """
        Override LLMGateway with mock.

        Production: LLMGatewayImpl (calls OpenAI/Anthropic)
        Test: MockLLMGateway (deterministic keyword responses)

        Scope: REQUEST (matches production)
        """
        return MockLLMGateway()
```

---

## Success Metrics

**Deliverables**:
- [ ] Comprehensive DI guide (`docs/development/dependency-injection.md`)
- [ ] Testing guide addendum
- [ ] Quick reference card
- [ ] Inline provider docstrings
- [ ] Unit tests documenting behavior
- [ ] Troubleshooting guide

**Outcome**:
- ✅ Future developers can debug DI issues quickly
- ✅ Test provider patterns documented
- ✅ Common pitfalls explained with examples
- ✅ Reduced time spent debugging provider precedence

---

## Timeline

| Time | Task |
|------|------|
| **Morning** | Experiments + pattern extraction |
| **Afternoon** | Write comprehensive guide |
| **End of Day** | Quick reference + inline docs |

**Total**: 1 day

---

## Post-Implementation

**Maintenance**:
- Update guide when adding new providers
- Add new pitfalls as discovered
- Keep examples in sync with codebase

**Training**:
- Share guide with team
- Code review checklist for DI patterns
- Onboarding document reference

---

**Expected Impact**: Reduced DI debugging time from hours to minutes
