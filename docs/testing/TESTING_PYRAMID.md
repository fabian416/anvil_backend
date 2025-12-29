# Testing Pyramid Guide

**Initiative**: Component-Level Integration Testing (Phase 1)
**Date**: 2025-12-29
**Purpose**: Guide for choosing the right test type for different scenarios

---

## Table of Contents

1. [The Testing Pyramid](#the-testing-pyramid)
2. [Test Type Comparison](#test-type-comparison)
3. [Decision Tree](#decision-tree)
4. [Examples by Test Type](#examples-by-test-type)
5. [Anti-Patterns](#anti-patterns)
6. [Best Practices](#best-practices)

---

## The Testing Pyramid

### Visual Representation

```
                      /\
                     /  \
                    / E2E \ (10-15 tests)
                   /      \  - Full HTTP stack
                  /--------\  - Real DB + Auth
                 /          \  - Smoke tests only
                /  Integra-  \ - Validate full system
               /   tion (20)  \
              /----------------\
             /                  \
            /    Component (100) \ - Direct component calls
           /      Tests          \ - In-memory dependencies
          /                       \ - Business logic focus
         /-------------------------\
        /                           \
       /       Unit Tests (68+)      \ - Pure domain logic
      /        (Pure Logic)           \ - No dependencies
     /                                 \ - Very fast (<0.1s)
    /___________________________________\
```

### Test Distribution

**Target Distribution:**
- **Unit Tests**: 40-50% (68+ tests)
- **Component Tests**: 40-45% (80-100 tests)
- **Integration Tests**: 5-10% (10-20 tests)
- **E2E Tests**: <5% (5-10 tests)

**Current Distribution** (Before Migration):
- Unit Tests: 40% (68 tests)
- Integration Tests (actually E2E): 60% (113 tests) ⚠️
- Proper E2E: 0% ⚠️

**Problem**: Most "integration" tests are actually E2E tests!

---

## Test Type Comparison

### Quick Reference Table

| Aspect | Unit Test | Component Test | Integration Test | E2E Test |
|--------|-----------|----------------|------------------|----------|
| **Scope** | Single function/class | Single component | Multiple components | Full system |
| **Dependencies** | Mocked/stubbed | In-memory mocks | Real infrastructure | Production-like |
| **Speed** | <0.1s | <0.5s | 1-3s | 3-10s |
| **Flakiness** | Very stable | Stable | Can be flaky | Often flaky |
| **Debugging** | Trivial | Easy | Moderate | Difficult |
| **Coverage** | High (80%+) | Medium (60-70%) | Low (30-40%) | Low (10-20%) |
| **Focus** | Logic correctness | Business rules | System integration | User workflows |
| **Example** | Value object validation | Send message interactor | DB persistence + API | Login → Chat → Logout |

### Detailed Comparison

#### Unit Tests

**What**: Test single functions, methods, or classes in isolation

**When**: Testing domain entities, value objects, pure functions

**Dependencies**: All mocked/stubbed

**Speed**: Very fast (<0.1 seconds)

**Example**:
```python
def test_conversation_title_validation():
    """Unit test: Pure domain logic."""
    conversation = Conversation(
        id=uuid4(),
        user_id=123,
        title="A" * 500,  # Too long
    )
    # Test domain rule: title max length
    assert len(conversation.title) <= 255
```

**Pros:**
- ✅ Extremely fast
- ✅ Very stable (no external dependencies)
- ✅ Easy to debug
- ✅ High coverage possible

**Cons:**
- ❌ Limited scope (doesn't test integration)
- ❌ Can miss integration bugs

#### Component Tests

**What**: Test application components (interactors, services) with in-memory dependencies

**When**: Testing business logic, command/query handlers, domain services

**Dependencies**: In-memory repositories, mock gateways

**Speed**: Fast (<0.5 seconds)

**Example**:
```python
@pytest.mark.asyncio
async def test_send_message_component(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
    test_conversation,
):
    """Component test: Business logic without HTTP."""
    interactor = SendMessage(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    result = await interactor.execute(
        conversation_id=test_conversation.id,
        user_id=123,
        content="Hello",
    )

    assert result.message.content == "Hello"
    assert result.agent_response is not None
```

**Pros:**
- ✅ Fast execution (3-5x faster than E2E)
- ✅ Tests real business logic
- ✅ Easy to mock dependencies
- ✅ Clear failure messages
- ✅ Good coverage of business rules

**Cons:**
- ❌ Doesn't test HTTP layer
- ❌ Doesn't test auth middleware
- ❌ Doesn't test serialization

#### Integration Tests

**What**: Test multiple components working together with real infrastructure

**When**: Testing database persistence, external API integration, infrastructure adapters

**Dependencies**: Real database, real Redis, real external services

**Speed**: Medium (1-3 seconds)

**Example**:
```python
@pytest.mark.asyncio
async def test_conversation_repository_persistence(async_db_session):
    """Integration test: Real database."""
    repo = SQLAlchemyConversationRepository(async_db_session)

    # Create conversation
    conversation = Conversation(
        id=uuid4(),
        user_id=123,
        title="Test",
    )
    await repo.save(conversation)

    # Retrieve from DB
    retrieved = await repo.get_by_id(conversation.id)
    assert retrieved.title == "Test"
```

**Pros:**
- ✅ Tests real infrastructure
- ✅ Catches database/schema issues
- ✅ Validates adapter implementations

**Cons:**
- ❌ Slower than component tests
- ❌ Requires infrastructure setup
- ❌ Can be flaky (DB connection issues)

#### E2E Tests

**What**: Test complete user workflows through HTTP API

**When**: Smoke testing critical user flows, validating entire system

**Dependencies**: Full application stack (HTTP + DB + Auth + External APIs)

**Speed**: Slow (3-10 seconds)

**Example**:
```python
@pytest.mark.e2e
async def test_complete_chat_flow(client):
    """E2E test: Full user workflow."""
    # 1. User registers
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "secure123"},
    )
    assert register_response.status_code == 201

    # 2. User logs in
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "secure123"},
    )
    token = login_response.json()["access_token"]

    # 3. User creates conversation
    conv_response = await client.post(
        "/api/v1/chat/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "DeFi Questions"},
    )
    conversation_id = conv_response.json()["id"]

    # 4. User sends message
    msg_response = await client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "What is DeFi?"},
    )
    assert msg_response.status_code == 201
    assert "message" in msg_response.json()
```

**Pros:**
- ✅ Tests real user workflows
- ✅ Validates entire system
- ✅ Catches integration issues between layers

**Cons:**
- ❌ Very slow
- ❌ Flaky (many points of failure)
- ❌ Hard to debug (which layer failed?)
- ❌ Expensive to maintain

---

## Decision Tree

### When to Write Each Type of Test

```
START: What are you testing?
    |
    ├─ Pure domain logic (entity, value object, domain rule)?
    │   └─ ✅ UNIT TEST
    │
    ├─ Business logic (use case, command handler, query)?
    │   └─ ✅ COMPONENT TEST
    │
    ├─ Database persistence or external API adapter?
    │   └─ ✅ INTEGRATION TEST
    │
    ├─ Complete user workflow (auth → action → result)?
    │   └─ ✅ E2E TEST
    │
    └─ HTTP routing, auth middleware, serialization?
        └─ ✅ E2E TEST (or manual testing)
```

### Detailed Decision Guide

#### Write a Unit Test When:

- ✅ Testing **domain entities** (Conversation, Message, User)
- ✅ Testing **value objects** (MessageRole, ConversationStatus)
- ✅ Testing **domain services** with no external dependencies
- ✅ Testing **pure functions** (calculators, validators, formatters)
- ✅ Testing **exception handling** in domain layer
- ✅ Testing **business rules** (invariants, constraints)

**Example Scenarios:**
- "Does Conversation enforce title max length?"
- "Does MessageRole only allow valid values?"
- "Does ConversationFactory create valid entities?"

#### Write a Component Test When:

- ✅ Testing **application interactors** (SendMessage, CreateConversation)
- ✅ Testing **command handlers** (write operations)
- ✅ Testing **query handlers** (read operations)
- ✅ Testing **domain services** with dependencies
- ✅ Testing **business logic** that touches multiple entities
- ✅ Testing **error scenarios** in application layer

**Example Scenarios:**
- "Does SendMessage create user + assistant messages?"
- "Does SendMessage raise ConversationNotFoundError for invalid ID?"
- "Does CreateConversation assign user_id correctly?"
- "Does IntentClassifier route to correct agent?"

#### Write an Integration Test When:

- ✅ Testing **database repositories** with real PostgreSQL
- ✅ Testing **external API adapters** with real endpoints
- ✅ Testing **infrastructure concerns** (caching, queuing)
- ✅ Testing **SQL query performance**
- ✅ Testing **database constraints** and foreign keys

**Example Scenarios:**
- "Does ConversationRepository persist to PostgreSQL correctly?"
- "Does MessageRepository handle cascading deletes?"
- "Does LLMGateway handle API rate limits?"
- "Does Redis cache expire tokens correctly?"

#### Write an E2E Test When:

- ✅ Testing **critical user workflows** (smoke tests)
- ✅ Testing **complete feature flows** (end-to-end)
- ✅ Testing **auth flows** (login, logout, session management)
- ✅ Testing **HTTP error handling** (404, 401, 500)
- ✅ Testing **API contracts** (OpenAPI compliance)

**Example Scenarios:**
- "Can user register → login → chat → logout?"
- "Can admin manage users through API?"
- "Does subscription flow work end-to-end?"
- "Are all error codes returned correctly?"

---

## Examples by Test Type

### Example 1: Testing Conversation Creation

#### Unit Test (Domain Layer)

```python
# tests/unit/domain/entities/test_conversation.py

def test_conversation_requires_user_id():
    """Unit: Domain rule validation."""
    with pytest.raises(ValueError):
        Conversation(
            id=uuid4(),
            user_id=None,  # Invalid!
            title="Test",
        )
```

**What it tests**: Domain invariants (entity rules)
**Speed**: <0.1s
**When to use**: Validating entity creation rules

#### Component Test (Application Layer)

```python
# tests/component/chat/test_create_conversation.py

@pytest.mark.asyncio
async def test_create_conversation_assigns_user_id(
    conversation_repository,
    user_repository,
    test_user,
):
    """Component: Business logic."""
    interactor = CreateConversation(
        conversation_repo=conversation_repository,
        user_repo=user_repository,
    )

    conversation = await interactor.execute(
        user_id=test_user.id,
        title="DeFi Questions",
    )

    assert conversation.user_id == test_user.id
    assert conversation.title == "DeFi Questions"
```

**What it tests**: Application interactor logic
**Speed**: <0.5s
**When to use**: Testing use case implementation

#### Integration Test (Infrastructure Layer)

```python
# tests/integration/database/test_conversation_repository_integration.py

@pytest.mark.asyncio
async def test_conversation_repository_saves_to_database(async_db_session):
    """Integration: Real database persistence."""
    repo = SQLAlchemyConversationRepository(async_db_session)

    conversation = Conversation(
        id=uuid4(),
        user_id=123,
        title="Test",
    )

    await repo.save(conversation)

    # Query database directly
    result = await async_db_session.execute(
        select(conversations_table).where(conversations_table.c.id == conversation.id)
    )
    row = result.fetchone()

    assert row.title == "Test"
    assert row.user_id == 123
```

**What it tests**: Database persistence adapter
**Speed**: 1-2s
**When to use**: Validating repository implementations

#### E2E Test (Full Stack)

```python
# tests/integration/flows/test_chat_flow_complete.py

@pytest.mark.e2e
async def test_user_can_create_conversation_via_api(client, auth_headers):
    """E2E: Full HTTP flow."""
    response = await client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={"title": "DeFi Questions"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "DeFi Questions"
```

**What it tests**: HTTP API endpoint + auth + persistence
**Speed**: 3-5s
**When to use**: Smoke testing critical flows

### Example 2: Testing Message Sending

#### Unit Test

```python
# tests/unit/domain/entities/test_message.py

def test_message_requires_content():
    """Unit: Domain validation."""
    with pytest.raises(ValueError):
        Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role=MessageRole.USER,
            content="",  # Invalid!
        )
```

#### Component Test

```python
# tests/component/chat/test_send_message.py

@pytest.mark.asyncio
async def test_send_message_creates_user_and_assistant_messages(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
    test_conversation,
):
    """Component: Business logic."""
    mock_llm_gateway.set_default_response({
        "content": "DeFi is decentralized finance...",
    })

    interactor = SendMessage(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    result = await interactor.execute(
        conversation_id=test_conversation.id,
        user_id=123,
        content="What is DeFi?",
    )

    messages = await message_repository.list_by_conversation(test_conversation.id)
    assert len(messages) == 2  # User + assistant
```

#### Integration Test

```python
# tests/integration/chat/test_llm_gateway_integration.py

@pytest.mark.asyncio
@pytest.mark.slow
async def test_llm_gateway_calls_real_api():
    """Integration: Real LLM API."""
    gateway = OpenAILLMGateway(api_key=os.getenv("OPENAI_API_KEY"))

    response = await gateway.generate(
        messages=[{"role": "user", "content": "Hello"}],
        model="gpt-4",
    )

    assert "content" in response
    assert len(response["content"]) > 0
```

#### E2E Test

```python
# tests/integration/flows/test_chat_flow_complete.py

@pytest.mark.e2e
async def test_user_can_send_message_and_receive_response(
    client,
    auth_headers,
    test_conversation_id,
):
    """E2E: Full chat flow."""
    response = await client.post(
        f"/api/v1/chat/conversations/{test_conversation_id}/messages",
        headers=auth_headers,
        json={"content": "What is DeFi?"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"]["content"] == "What is DeFi?"
    assert "agent_response" in data
```

---

## Anti-Patterns

### Anti-Pattern 1: Testing HTTP in Component Tests

❌ **Bad** (component test with HTTP):
```python
async def test_send_message_component(client):
    """Component test should NOT use HTTP client!"""
    response = await client.post(...)  # Wrong!
    assert response.status_code == 200
```

✅ **Good** (component test without HTTP):
```python
async def test_send_message_component(interactor, test_conversation):
    """Component test calls interactor directly."""
    result = await interactor.execute(...)  # Right!
    assert result.message.content == "Hello"
```

### Anti-Pattern 2: Testing Business Logic in E2E Tests

❌ **Bad** (E2E test for business logic):
```python
@pytest.mark.e2e
async def test_conversation_not_found_returns_404(client, auth_headers):
    """E2E test for business logic - too slow!"""
    response = await client.post(
        f"/api/v1/chat/conversations/{uuid4()}/messages",
        headers=auth_headers,
        json={"content": "Hello"},
    )
    assert response.status_code == 404  # Testing business rule via HTTP!
```

✅ **Good** (component test for business logic):
```python
async def test_send_message_to_nonexistent_conversation_raises_error(interactor):
    """Component test for business logic - fast!"""
    with pytest.raises(ConversationNotFoundError):
        await interactor.execute(
            conversation_id=uuid4(),  # Doesn't exist
            user_id=123,
            content="Hello",
        )
```

### Anti-Pattern 3: Mocking Too Much in Unit Tests

❌ **Bad** (unit test with too many mocks):
```python
def test_conversation_creation(mock_repo, mock_user_service, mock_validator):
    """Unit test shouldn't need this many mocks!"""
    # Too complex for a unit test
```

✅ **Good** (unit test with no mocks):
```python
def test_conversation_creation():
    """Unit test: Pure domain logic, no mocks."""
    conversation = Conversation(
        id=uuid4(),
        user_id=123,
        title="Test",
    )
    assert conversation.user_id == 123
```

### Anti-Pattern 4: Too Many E2E Tests

❌ **Bad** (113 E2E tests):
```
Integration tests (all E2E):
- test_send_message_http
- test_send_empty_message_http
- test_send_message_to_nonexistent_conversation_http
- test_send_message_unauthorized_http
- ... (109 more E2E tests)
```

✅ **Good** (10 E2E smoke tests + 100 component tests):
```
E2E tests (10):
- test_complete_chat_flow
- test_complete_auth_flow
- test_complete_payment_flow
- ...

Component tests (100):
- test_send_message_component
- test_send_message_to_nonexistent_conversation_component
- test_send_message_with_context_component
- ...
```

---

## Best Practices

### 1. Follow the Pyramid

**Rule**: Write more tests at the bottom, fewer at the top

```
Many unit tests      (fast, stable, focused)
  ↓
Some component tests (fast, isolated, business logic)
  ↓
Few integration tests (real infrastructure)
  ↓
Very few E2E tests   (smoke tests only)
```

### 2. Test at the Right Level

**Rule**: Test each concern at the appropriate level

- Domain rules → Unit tests
- Business logic → Component tests
- Infrastructure → Integration tests
- User workflows → E2E tests

### 3. Optimize for Feedback Speed

**Rule**: Faster tests run more often

```
Unit tests:      Run on every save (<1 minute)
Component tests: Run on every commit (<2 minutes)
Integration:     Run on PR creation (<5 minutes)
E2E tests:       Run on deployment (<10 minutes)
```

### 4. Clear Test Names

**Rule**: Test names should describe behavior, not implementation

❌ Bad:
```python
def test_function_returns_true()
```

✅ Good:
```python
def test_send_message_creates_user_and_assistant_messages()
```

### 5. AAA Pattern

**Rule**: Arrange, Act, Assert

```python
async def test_send_message():
    # Arrange
    interactor = SendMessage(...)
    conversation = create_test_conversation()

    # Act
    result = await interactor.execute(...)

    # Assert
    assert result.message.content == "Hello"
```

### 6. One Assertion per Test Concept

**Rule**: Test one behavior per test

❌ Bad:
```python
def test_everything():
    # Tests 5 different things
    assert conversation.title == "Test"
    assert conversation.user_id == 123
    assert len(messages) == 2
    assert response.status_code == 200
    assert token is not None
```

✅ Good:
```python
def test_conversation_assigns_user_id():
    assert conversation.user_id == 123

def test_send_message_creates_two_messages():
    assert len(messages) == 2
```

---

## Summary

### Quick Reference

| Test Type | When to Use | Speed | Example |
|-----------|-------------|-------|---------|
| **Unit** | Domain logic, pure functions | <0.1s | Entity validation |
| **Component** | Business logic, interactors | <0.5s | Send message |
| **Integration** | Database, external APIs | 1-3s | Repository persistence |
| **E2E** | User workflows, smoke tests | 3-10s | Complete chat flow |

### Golden Rules

1. **Write unit tests for domain logic** (entities, value objects)
2. **Write component tests for business logic** (interactors, commands, queries)
3. **Write integration tests for infrastructure** (repositories, gateways)
4. **Write E2E tests sparingly** (critical flows only)
5. **Optimize for fast feedback** (run tests frequently)

### Migration Target

**Before**:
```
Unit:        68 tests (40%)
E2E:         113 tests (60%) ← Too many!
```

**After**:
```
Unit:        68 tests (35%)
Component:   100 tests (50%) ← NEW!
Integration: 15 tests (8%)
E2E:         12 tests (6%)   ← Reduced!
```

---

**Next**: Implement component test infrastructure and start migration!
