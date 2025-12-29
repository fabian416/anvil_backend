# Long-Term Initiatives - Implementation Plan (Q1 2025)

**Timeline**: 1 Quarter (12 weeks)
**Goal**: Modernize test infrastructure for 100% coverage and sustainable testing
**Methodology**: CTO Engineering Framework

---

## Initiative 4: Component-Level Integration Testing

**Timeline**: 4-5 weeks
**Risk**: Medium
**Impact**: High (faster tests, clearer failures, better isolation)

### Problem Statement

**Current**: Full HTTP integration tests (slow, brittle, hard to debug)
- Test makes HTTP request → Full app stack → Database → Response
- Failure could be in any layer
- Slow execution (DB + HTTP overhead)
- Hard to isolate failures

**Target**: Component-level integration tests
- Test specific components in isolation
- Fast execution (no HTTP overhead)
- Clear failure location
- Easy to debug

---

### Phase 1: Design Testing Layers (Week 1-2)

#### Testing Pyramid

```
         /\
        /  \  E2E (Few)
       /----\
      /      \  Integration (Some)
     /--------\
    /          \  Unit (Many)
   /------------\
  Component Tests (NEW LAYER)
```

**Component Tests** = Integration tests without HTTP layer

**Example**:

```python
# CURRENT: Full HTTP Integration Test
async def test_send_message_http(client):
    response = await client.post(
        "/api/v1/chat/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 200

# NEW: Component Integration Test
async def test_send_message_component(
    send_message_command: SendMessage,
    test_conversation: Conversation,
):
    result = await send_message_command.execute(
        conversation_id=test_conversation.id,
        user_id=123,
        content="Hello",
    )
    assert result.message.content == "Hello"
    assert result.routing.intent == "general_conversation"
```

**Benefits**:
- ✅ Faster (no HTTP serialization)
- ✅ Clearer errors (exact component)
- ✅ Better isolation
- ✅ Easier debugging

---

### Phase 2: Create Component Test Framework (Week 3-4)

#### Component Test Fixtures

**File**: `tests/component/conftest.py` (NEW)

```python
"""
Component test fixtures.

Provides pre-configured components with test dependencies.
"""

import pytest
from dishka import make_async_container
from app.setup.ioc.provider_registry import get_providers
from app.setup.ioc.testing import get_integration_test_providers


@pytest_asyncio.fixture
async def component_container():
    """
    DI container for component tests.

    Includes:
    - Real business logic (commands, queries, services)
    - Real database (PostgreSQL test DB)
    - Mock external services (LLM, email, payments)
    """
    container = make_async_container(
        *get_providers(),
        *get_integration_test_providers(),
    )

    yield container

    await container.close()


@pytest_asyncio.fixture
async def send_message_command(component_container):
    """Provide SendMessage command with real dependencies."""
    async with component_container() as request_container:
        command = await request_container.get(SendMessage)
        yield command


@pytest_asyncio.fixture
async def intent_detector(component_container):
    """Provide IntentDetectorService with test config."""
    async with component_container() as request_container:
        detector = await request_container.get(IntentDetectorService)
        yield detector


@pytest_asyncio.fixture
async def test_conversation(async_db_session):
    """Create test conversation in database."""
    conversation = Conversation(
        user_id=123,
        title="Test Conversation",
    )
    async_db_session.add(conversation)
    await async_db_session.commit()
    await async_db_session.refresh(conversation)

    return conversation
```

---

### Phase 3: Migrate Tests (Week 5-8)

#### Migration Strategy

**Tier 1: Intent Detection** (Week 5)
- Migrate intent detection tests to component level
- Test `IntentDetectorService` directly
- Remove HTTP layer overhead

**Tier 2: Message Handling** (Week 6)
- Migrate message send/receive tests
- Test `SendMessage`, `GetMessages` commands directly
- Verify business logic without HTTP

**Tier 3: GraphRAG/Hunter/Ultra** (Week 7)
- Migrate specialized handler tests
- Test handlers directly with mock data
- Faster feedback loops

**Tier 4: Squad Tests** (Week 8)
- Migrate squad tests to component level
- Test `SendAgentSquadMessage` without HTTP
- Should resolve remaining failures

**Keep**: E2E smoke tests for critical paths

---

### Phase 4: Performance Optimization (Week 9)

#### Parallel Test Execution

```python
# pytest.ini
[tool:pytest]
addopts = -n auto  # Run tests in parallel
testpaths = tests/component
```

**Expected Speedup**: 3-5x faster than current integration tests

---

## Initiative 5: Evaluate DI Framework Alternatives

**Timeline**: 2-3 weeks
**Risk**: Low (research phase)
**Impact**: Medium (long-term maintenance)

### Phase 1: Assessment (Week 1)

#### Evaluate Dishka

**Pros**:
- ✅ Feature-rich
- ✅ Supports async
- ✅ Scopes (APP, REQUEST)

**Cons**:
- ❌ Complex precedence rules (as discovered)
- ❌ Opaque resolution (hard to debug)
- ❌ Limited documentation

**Decision Criteria**:
1. Ease of mocking in tests
2. Clear error messages
3. Performance (DI overhead)
4. Documentation quality
5. Community support

---

#### Alternative 1: Manual Dependency Injection

**Example**:

```python
# Simple factory pattern
class ServiceFactory:
    def __init__(self, is_test: bool = False):
        self._is_test = is_test

    def create_llm_gateway(self) -> LLMGateway:
        if self._is_test:
            return MockLLMGateway()
        return LLMGatewayImpl()

    def create_send_message(self) -> SendMessage:
        llm = self.create_llm_gateway()
        db = self.create_db_session()
        return SendMessage(llm_gateway=llm, db_session=db)
```

**Pros**: Simple, explicit, easy to debug
**Cons**: Boilerplate, manual wiring

---

#### Alternative 2: Dependency Injector

**Library**: `dependency-injector`

```python
from dependency_injector import containers, providers

class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    llm_gateway = providers.Factory(
        LLMGatewayImpl,
        api_key=config.llm_api_key,
    )

    send_message = providers.Factory(
        SendMessage,
        llm_gateway=llm_gateway,
    )
```

**Pros**: Popular, well-documented, clear errors
**Cons**: Different API than Dishka

---

#### Alternative 3: Keep Dishka, Improve Patterns

**Approach**: Keep Dishka but document patterns better

**Pros**: No migration, leverage existing setup
**Cons**: Doesn't solve complexity issue

**Recommendation**: Start here (Initiative 3)

---

### Phase 2: POC (Week 2)

If switching DI framework:

1. Implement small subsystem with new DI
2. Write component tests
3. Measure setup time, test time, debugging time
4. Compare with Dishka version

---

### Phase 3: Decision (Week 3)

**Decision Matrix**:

| Framework | Ease of Use | Test Mocking | Performance | Migration Cost | Decision |
|-----------|-------------|--------------|-------------|----------------|----------|
| Dishka (current) | 6/10 | 7/10 | 9/10 | N/A | ? |
| Manual DI | 9/10 | 10/10 | 10/10 | High | ? |
| dependency-injector | 8/10 | 9/10 | 9/10 | High | ? |

**Recommendation**: Keep Dishka + improve documentation (Initiative 3)

**Rationale**: Migration cost too high for marginal benefit

---

## Initiative 6: Test Infrastructure as First-Class Code

**Timeline**: 3-4 weeks (ongoing)
**Risk**: Low
**Impact**: High (maintainability)

### Principles

1. **Test Code = Production Code Quality**
   - Same standards
   - Same review process
   - Same refactoring

2. **DRY Test Helpers**
   - Shared fixtures
   - Reusable factories
   - Common assertions

3. **Clear Test Organization**
   - Consistent structure
   - Easy to find tests
   - Obvious coverage gaps

---

### Phase 1: Test Organization (Week 1)

**New Structure**:

```
tests/
├── unit/              # Pure unit tests (fast, isolated)
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── component/         # Component integration (NEW)
│   ├── chat/
│   ├── graphrag/
│   ├── hunter/
│   └── squad/
├── integration/       # Full HTTP integration
│   └── critical_paths/  # Only E2E smoke tests
├── performance/       # Load tests
├── contract/          # API contract tests
└── helpers/           # Shared test utilities
    ├── factories/     # Data factories
    ├── assertions/    # Custom assertions
    └── fixtures/      # Reusable fixtures
```

---

### Phase 2: Test Factories (Week 2)

**File**: `tests/helpers/factories/user_factory.py` (NEW)

```python
"""
User test data factory.

Provides builder pattern for creating test users.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.domain.entities.user import User, UserRole


@dataclass
class UserFactory:
    """
    Factory for creating test users.

    Usage:
        user = UserFactory().with_role("admin").build()
    """

    email: str = "test@example.com"
    first_name: str = "Test"
    last_name: str = "User"
    role: UserRole = UserRole.USER
    is_active: bool = True

    def with_email(self, email: str) -> "UserFactory":
        self.email = email
        return self

    def with_role(self, role: str) -> "UserFactory":
        self.role = UserRole(role)
        return self

    def as_admin(self) -> "UserFactory":
        return self.with_role("admin")

    def build(self) -> User:
        return User(
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            role=self.role,
            is_active=self.is_active,
        )


# Usage in tests
async def test_admin_permission():
    admin = UserFactory().as_admin().build()
    assert admin.role == UserRole.ADMIN
```

---

### Phase 3: Custom Assertions (Week 3)

**File**: `tests/helpers/assertions/chat_assertions.py` (NEW)

```python
"""
Custom assertions for chat tests.

Makes tests more readable and maintainable.
"""

def assert_intent_detected(result, expected_intent: str, min_confidence: float = 0.8):
    """
    Assert intent detection result matches expectations.

    Args:
        result: Intent detection result
        expected_intent: Expected intent value
        min_confidence: Minimum confidence threshold
    """
    assert result.intent.value == expected_intent, (
        f"Intent mismatch: expected '{expected_intent}', "
        f"got '{result.intent.value}'"
    )
    assert result.confidence >= min_confidence, (
        f"Confidence too low: {result.confidence} < {min_confidence}"
    )


def assert_message_response_valid(response: dict):
    """Assert message response has required fields."""
    assert "user_message" in response
    assert "agent_message" in response
    assert "routing" in response

    # User message validation
    user_msg = response["user_message"]
    assert "id" in user_msg
    assert "content" in user_msg
    assert user_msg["role"] == "user"

    # Agent message validation
    agent_msg = response["agent_message"]
    assert "id" in agent_msg
    assert "content" in agent_msg
    assert agent_msg["role"] == "assistant"


# Usage in tests
async def test_intent_detection():
    result = await detector.detect_intent("Hello")
    assert_intent_detected(result, "general_conversation")


async def test_send_message():
    response = await send_message(...)
    assert_message_response_valid(response)
```

---

### Phase 4: Documentation (Week 4)

**File**: `tests/README.md` (NEW)

```markdown
# Test Suite Guide

## Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit

# Component tests (medium)
pytest tests/component

# Integration tests (slow)
pytest tests/integration

# Specific test
pytest tests/component/chat/test_intent_detection.py -v
```

## Writing Tests

### Unit Tests

Test single function/class in isolation:

```python
def test_user_validation():
    user = User(email="invalid")  # No DB, no DI
    with pytest.raises(ValidationError):
        user.validate()
```

### Component Tests

Test component with real dependencies:

```python
async def test_send_message(send_message_command, test_conversation):
    result = await send_message_command.execute(...)  # Real DB, mock LLM
    assert result.message.content == "Hello"
```

### Integration Tests

Test full HTTP flow (sparingly):

```python
async def test_chat_api(client):
    response = await client.post("/chat/messages", json={...})
    assert response.status_code == 200
```

## Factories

Use factories for test data:

```python
from tests.helpers.factories import UserFactory, ConversationFactory

user = UserFactory().as_admin().build()
conversation = ConversationFactory().with_user(user).build()
```

## Custom Assertions

Use domain assertions:

```python
from tests.helpers.assertions.chat_assertions import assert_intent_detected

assert_intent_detected(result, "specialist_task")
```
```

---

## Success Metrics

### Component Tests (Initiative 4)
- [ ] 80%+ coverage with component tests
- [ ] 3-5x faster than current integration tests
- [ ] Clear failure messages
- [ ] All squad tests passing

### DI Evaluation (Initiative 5)
- [ ] Decision documented
- [ ] POC completed (if switching)
- [ ] Migration plan (if switching)

### Test Infrastructure (Initiative 6)
- [ ] Factories for all major entities
- [ ] Custom assertions for common patterns
- [ ] Comprehensive test documentation
- [ ] Developer onboarding < 30 minutes

---

## Timeline Summary

| Week | Initiative 4 | Initiative 5 | Initiative 6 |
|------|--------------|--------------|--------------|
| 1-2 | Design layers | Assess Dishka | Reorganize tests |
| 3-4 | Framework | POC/Decision | Factories |
| 5-6 | Migrate Tier 1-2 | - | Assertions |
| 7-8 | Migrate Tier 3-4 | - | Documentation |
| 9 | Optimize | - | Polish |

**Total**: 9 weeks (~2 months)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Component tests too complex | Medium | Start simple, iterate |
| DI migration breaks production | High | Thorough testing, gradual rollout |
| Test refactor takes too long | Low | Time-box each phase |

---

## Expected Outcome

**Test Coverage**: 83.8% → **100%**

**Test Speed**:
- Current: 15s for 37 tests
- Target: 5s for 100+ tests (component tests)

**Developer Experience**:
- Clear test failures
- Easy to write new tests
- Fast feedback loops
- Sustainable test suite

---

**Next**: See master roadmap for complete implementation sequence
