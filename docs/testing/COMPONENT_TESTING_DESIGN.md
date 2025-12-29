# Component Testing Layer Design

**Initiative**: Component-Level Integration Testing (Phase 1)
**Date**: 2025-12-29
**Purpose**: Detailed design for component testing layer, fixtures, and migration patterns

---

## Table of Contents

1. [Component Testing Philosophy](#component-testing-philosophy)
2. [Directory Structure](#directory-structure)
3. [Fixture Architecture](#fixture-architecture)
4. [Mock Implementations](#mock-implementations)
5. [Test Data Factories](#test-data-factories)
6. [Component Test Patterns](#component-test-patterns)
7. [Migration Guidelines](#migration-guidelines)

---

## Component Testing Philosophy

### What is a Component Test?

A **component test** validates the behavior of an application component (interactor, service, or domain aggregate) **without the HTTP layer**.

**Key Principles:**

1. **Direct Invocation**: Call interactors/services directly, not through HTTP
2. **In-Memory Dependencies**: Use in-memory repositories, mock external APIs
3. **Business Logic Focus**: Test domain rules, not HTTP routing or serialization
4. **Fast Execution**: <0.5 seconds per test (no DB, no network)
5. **Clear Failures**: Exact component that failed, not "HTTP 500"

### Component Test Scope

**What to Test:**
- Application interactors (commands/queries)
- Domain services (business logic)
- Repository integration (with in-memory repos)
- External API integration (with mocks)

**What NOT to Test:**
- HTTP routing (that's E2E)
- Request/response serialization (that's E2E)
- Authentication middleware (that's E2E)
- Database schema (that's unit/integration)

### Testing Pyramid Position

```
          /\
         /  \  E2E Tests (10-15)
        /----\  - Full HTTP stack
       /      \  - Real DB + Auth
      /--------\  - Smoke tests only
     /          \
    /  Component \ Integration Tests (80-100)
   /     Tests    \ - Direct interactor calls
  /               \ - In-memory dependencies
 /-----------------\ - Business logic focus
/                   \
/    Unit Tests      \ (68+)
/   (Pure Logic)      \
```

---

## Directory Structure

### Proposed Structure

```
tests/
├── component/                           # NEW: Component tests
│   ├── conftest.py                     # Component fixtures
│   ├── mocks/                          # Mock implementations
│   │   ├── __init__.py
│   │   ├── repositories.py             # In-memory repositories
│   │   ├── gateways.py                 # Mock external API gateways
│   │   └── services.py                 # Mock infrastructure services
│   │
│   ├── factories/                      # Test data factories
│   │   ├── __init__.py
│   │   ├── chat_factories.py          # Conversation, Message factories
│   │   ├── user_factories.py          # User, Session factories
│   │   └── agent_factories.py         # Agent, Intent factories
│   │
│   ├── chat/                           # Chat component tests
│   │   ├── test_send_message.py       # SendMessage interactor
│   │   ├── test_create_conversation.py
│   │   └── test_message_queries.py
│   │
│   ├── agent_squad/                    # Agent Squad component tests
│   │   ├── test_intent_classification.py
│   │   ├── test_agent_orchestration.py
│   │   └── test_context_preservation.py
│   │
│   ├── hunter/                         # Hunter AI component tests
│   │   ├── test_sentiment_analysis.py
│   │   ├── test_risk_analysis.py
│   │   └── test_trading_signals.py
│   │
│   └── ... (other domains)
│
├── integration/                        # REDUCED: E2E smoke tests only
│   ├── flows/                          # Business flow E2E tests
│   │   ├── test_auth_flow_complete.py
│   │   ├── test_chat_flow_complete.py
│   │   └── test_payment_flow_complete.py
│   └── api/                            # API contract tests
│       └── test_openapi_schema.py
│
├── unit/                               # UNCHANGED: Pure unit tests
│   └── ... (existing unit tests)
│
└── fixtures/                           # ENHANCED: Shared fixtures
    ├── domain_factories.py            # Domain entity factories (existing)
    ├── mock_services.py               # Mock service implementations (existing)
    └── component_fixtures.py          # NEW: Component test fixtures
```

### File Naming Conventions

**Component Tests:**
- `test_<interactor_name>.py` - For testing specific interactors
- `test_<service_name>.py` - For testing domain services
- `test_<feature>_queries.py` - For testing query handlers

**Mock Implementations:**
- `InMemory<Entity>Repository` - In-memory repository (e.g., InMemoryConversationRepository)
- `Mock<Gateway>Gateway` - Mock external API gateway (e.g., MockLLMGateway)
- `Fake<Service>` - Fake infrastructure service (e.g., FakeEmailService)

---

## Fixture Architecture

### Component Test Fixtures (`tests/component/conftest.py`)

```python
"""
Component test fixtures.

Provides:
- In-memory repositories
- Mock gateways
- Test data factories
- Component test utilities
"""

import pytest
import pytest_asyncio
from uuid import UUID, uuid4
from typing import Dict, List

from tests.component.mocks.repositories import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
    InMemoryUserRepository,
)
from tests.component.mocks.gateways import (
    MockLLMGateway,
    MockIntentDetectionGateway,
    MockGraphRAGGateway,
)
from tests.component.factories.chat_factories import (
    ConversationFactory,
    MessageFactory,
)
from tests.component.factories.user_factories import UserFactory


# ============================================================================
# Repository Fixtures (In-Memory)
# ============================================================================

@pytest.fixture
def conversation_repository():
    """In-memory conversation repository for component tests."""
    return InMemoryConversationRepository()


@pytest.fixture
def message_repository():
    """In-memory message repository for component tests."""
    return InMemoryMessageRepository()


@pytest.fixture
def user_repository():
    """In-memory user repository for component tests."""
    return InMemoryUserRepository()


# ============================================================================
# Gateway Fixtures (Mocks)
# ============================================================================

@pytest.fixture
def mock_llm_gateway():
    """Mock LLM gateway with configurable responses."""
    gateway = MockLLMGateway()
    # Default response
    gateway.set_default_response({
        "content": "This is a mock LLM response.",
        "model": "mock-model",
        "tokens_used": 50,
    })
    return gateway


@pytest.fixture
def mock_intent_gateway():
    """Mock intent detection gateway."""
    gateway = MockIntentDetectionGateway()
    gateway.set_default_intent({
        "agent_type": "CHAT",
        "confidence": 0.95,
        "reasoning": "Default chat intent",
    })
    return gateway


@pytest.fixture
def mock_graphrag_gateway():
    """Mock GraphRAG gateway."""
    return MockGraphRAGGateway()


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def conversation_factory():
    """Factory for creating test conversations."""
    return ConversationFactory()


@pytest.fixture
def message_factory():
    """Factory for creating test messages."""
    return MessageFactory()


@pytest.fixture
def user_factory():
    """Factory for creating test users."""
    return UserFactory()


# ============================================================================
# Pre-Populated Test Data
# ============================================================================

@pytest_asyncio.fixture
async def test_user(user_repository, user_factory):
    """Create a test user in the repository."""
    user = user_factory.create(
        id=123,
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    await user_repository.save(user)
    return user


@pytest_asyncio.fixture
async def test_conversation(
    conversation_repository,
    conversation_factory,
    test_user,
):
    """Create a test conversation in the repository."""
    conversation = conversation_factory.create(
        user_id=test_user.id,
        title="Test Conversation",
    )
    await conversation_repository.save(conversation)
    return conversation


@pytest_asyncio.fixture
async def conversation_with_messages(
    test_conversation,
    message_repository,
    message_factory,
):
    """Create a conversation with pre-populated messages."""
    messages = [
        message_factory.create(
            conversation_id=test_conversation.id,
            role="user",
            content="Hello",
        ),
        message_factory.create(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Hi! How can I help you?",
        ),
    ]
    for msg in messages:
        await message_repository.save(msg)

    return test_conversation, messages


# ============================================================================
# Component Test Utilities
# ============================================================================

class ComponentTestContext:
    """
    Helper for component tests.

    Provides utilities for:
    - Setting up test scenarios
    - Verifying outcomes
    - Debugging failures
    """

    def __init__(
        self,
        conversation_repo: InMemoryConversationRepository,
        message_repo: InMemoryMessageRepository,
        user_repo: InMemoryUserRepository,
    ):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.user_repo = user_repo

    async def setup_conversation_scenario(
        self,
        user_id: int,
        num_messages: int = 0,
    ):
        """
        Create a conversation with N messages.

        Returns:
            (conversation, messages)
        """
        from tests.component.factories.chat_factories import (
            ConversationFactory,
            MessageFactory,
        )

        conv_factory = ConversationFactory()
        msg_factory = MessageFactory()

        conversation = conv_factory.create(user_id=user_id)
        await self.conversation_repo.save(conversation)

        messages = []
        for i in range(num_messages):
            role = "user" if i % 2 == 0 else "assistant"
            msg = msg_factory.create(
                conversation_id=conversation.id,
                role=role,
                content=f"Message {i+1}",
            )
            await self.message_repo.save(msg)
            messages.append(msg)

        return conversation, messages

    async def assert_message_count(
        self,
        conversation_id: UUID,
        expected_count: int,
    ):
        """Assert conversation has expected number of messages."""
        messages = await self.message_repo.list_by_conversation(conversation_id)
        actual_count = len(messages)
        assert actual_count == expected_count, \
            f"Expected {expected_count} messages, found {actual_count}"

    async def assert_last_message_content(
        self,
        conversation_id: UUID,
        expected_content: str,
    ):
        """Assert last message has expected content."""
        messages = await self.message_repo.list_by_conversation(conversation_id)
        assert len(messages) > 0, "No messages found"
        last_message = messages[-1]
        assert last_message.content == expected_content, \
            f"Expected '{expected_content}', got '{last_message.content}'"


@pytest.fixture
def component_context(
    conversation_repository,
    message_repository,
    user_repository,
):
    """Component test context helper."""
    return ComponentTestContext(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        user_repo=user_repository,
    )
```

---

## Mock Implementations

### In-Memory Repositories (`tests/component/mocks/repositories.py`)

```python
"""
In-memory repository implementations for component tests.

These repositories implement the same port interfaces as production
repositories but store data in memory for fast, isolated testing.
"""

from typing import List, Optional, Dict
from uuid import UUID
from copy import deepcopy

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.entities.user import User
from app.domain.ports.repositories.conversation_repository import ConversationRepository
from app.domain.ports.repositories.message_repository import MessageRepository
from app.domain.ports.repositories.user_repository import UserRepository


class InMemoryConversationRepository(ConversationRepository):
    """
    In-memory conversation repository.

    Stores conversations in a dictionary for fast access.
    Implements the same interface as SQLAlchemyConversationRepository.
    """

    def __init__(self):
        self._storage: Dict[UUID, Conversation] = {}

    async def save(self, conversation: Conversation) -> Conversation:
        """Save conversation to in-memory storage."""
        # Deep copy to prevent mutations
        self._storage[conversation.id] = deepcopy(conversation)
        return conversation

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        conversation = self._storage.get(conversation_id)
        return deepcopy(conversation) if conversation else None

    async def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Conversation]:
        """List conversations for a user."""
        user_convs = [
            c for c in self._storage.values()
            if c.user_id == user_id
        ]
        # Sort by created_at descending
        user_convs.sort(key=lambda c: c.created_at, reverse=True)
        return [deepcopy(c) for c in user_convs[offset:offset + limit]]

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete conversation."""
        if conversation_id in self._storage:
            del self._storage[conversation_id]
            return True
        return False

    async def exists(self, conversation_id: UUID) -> bool:
        """Check if conversation exists."""
        return conversation_id in self._storage

    def clear(self):
        """Clear all data (test utility)."""
        self._storage.clear()


class InMemoryMessageRepository(MessageRepository):
    """
    In-memory message repository.

    Stores messages in a list for chronological ordering.
    """

    def __init__(self):
        self._storage: List[Message] = []

    async def save(self, message: Message) -> Message:
        """Save message to in-memory storage."""
        # Remove existing message with same ID
        self._storage = [m for m in self._storage if m.id != message.id]
        # Add new message
        self._storage.append(deepcopy(message))
        return message

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID."""
        for msg in self._storage:
            if msg.id == message_id:
                return deepcopy(msg)
        return None

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """List messages for a conversation."""
        conv_messages = [
            m for m in self._storage
            if m.conversation_id == conversation_id
        ]
        # Sort by created_at ascending (chronological)
        conv_messages.sort(key=lambda m: m.created_at)

        if limit:
            conv_messages = conv_messages[:limit]

        return [deepcopy(m) for m in conv_messages]

    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        return sum(
            1 for m in self._storage
            if m.conversation_id == conversation_id
        )

    def clear(self):
        """Clear all data (test utility)."""
        self._storage.clear()


class InMemoryUserRepository(UserRepository):
    """In-memory user repository."""

    def __init__(self):
        self._storage: Dict[int, User] = {}

    async def save(self, user: User) -> User:
        """Save user to in-memory storage."""
        self._storage[user.id] = deepcopy(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        user = self._storage.get(user_id)
        return deepcopy(user) if user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self._storage.values():
            if user.email == email:
                return deepcopy(user)
        return None

    async def exists(self, user_id: int) -> bool:
        """Check if user exists."""
        return user_id in self._storage

    def clear(self):
        """Clear all data (test utility)."""
        self._storage.clear()
```

### Mock Gateways (`tests/component/mocks/gateways.py`)

```python
"""
Mock gateway implementations for component tests.

These gateways mock external API calls (LLM, GraphRAG, etc.)
for fast, deterministic testing.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4

from app.domain.ports.gateways.llm_gateway import LLMGateway
from app.domain.ports.gateways.intent_detection_gateway import IntentDetectionGateway
from app.domain.ports.gateways.graphrag_gateway import GraphRAGGateway


class MockLLMGateway(LLMGateway):
    """
    Mock LLM gateway for testing.

    Allows configuring responses without making actual API calls.
    """

    def __init__(self):
        self._default_response = {
            "content": "This is a mock response.",
            "model": "mock-model-v1",
            "tokens_used": 50,
        }
        self._response_queue: List[Dict[str, Any]] = []
        self._call_history: List[Dict[str, Any]] = []

    def set_default_response(self, response: Dict[str, Any]):
        """Set the default response for all calls."""
        self._default_response = response

    def queue_response(self, response: Dict[str, Any]):
        """Queue a response (FIFO). Used for multi-turn scenarios."""
        self._response_queue.append(response)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate mock response."""
        # Record call for assertions
        self._call_history.append({
            "messages": messages,
            "model": model,
            "kwargs": kwargs,
        })

        # Return queued response or default
        if self._response_queue:
            return self._response_queue.pop(0)
        return self._default_response

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of calls (for assertions)."""
        return self._call_history

    def assert_called_once(self):
        """Assert gateway was called exactly once."""
        assert len(self._call_history) == 1, \
            f"Expected 1 call, got {len(self._call_history)}"

    def assert_called_with(self, **kwargs):
        """Assert last call had specific parameters."""
        assert len(self._call_history) > 0, "Gateway was not called"
        last_call = self._call_history[-1]
        for key, value in kwargs.items():
            assert key in last_call, f"Parameter '{key}' not found in call"
            assert last_call[key] == value, \
                f"Expected {key}={value}, got {last_call[key]}"


class MockIntentDetectionGateway(IntentDetectionGateway):
    """Mock intent detection gateway."""

    def __init__(self):
        self._default_intent = {
            "agent_type": "CHAT",
            "confidence": 0.95,
            "reasoning": "Default intent",
        }
        self._intent_queue: List[Dict[str, Any]] = []

    def set_default_intent(self, intent: Dict[str, Any]):
        """Set default intent classification result."""
        self._default_intent = intent

    def queue_intent(self, intent: Dict[str, Any]):
        """Queue an intent result (FIFO)."""
        self._intent_queue.append(intent)

    async def classify(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Classify intent (mock)."""
        if self._intent_queue:
            return self._intent_queue.pop(0)
        return self._default_intent


class MockGraphRAGGateway(GraphRAGGateway):
    """Mock GraphRAG gateway."""

    def __init__(self):
        self._default_results = [
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Mock Protocol",
                "similarity_score": 0.9,
                "risk_score": 2.5,
            }
        ]

    def set_search_results(self, results: List[Dict[str, Any]]):
        """Set mock search results."""
        self._default_results = results

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Mock search."""
        return self._default_results[:limit]
```

---

## Test Data Factories

### Chat Factories (`tests/component/factories/chat_factories.py`)

```python
"""
Test data factories for chat domain.

Provides convenient factory methods for creating test conversations,
messages, and related entities.
"""

from uuid import uuid4, UUID
from datetime import datetime, timezone

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole


class ConversationFactory:
    """Factory for creating test conversations."""

    def create(
        self,
        id: Optional[UUID] = None,
        user_id: int = 123,
        title: Optional[str] = "Test Conversation",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Conversation:
        """Create a test conversation."""
        return Conversation(
            id=id or uuid4(),
            user_id=user_id,
            title=title,
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
        )

    def create_batch(self, count: int, **kwargs) -> List[Conversation]:
        """Create multiple conversations."""
        return [self.create(**kwargs) for _ in range(count)]


class MessageFactory:
    """Factory for creating test messages."""

    def create(
        self,
        id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        role: str = "user",
        content: str = "Test message",
        created_at: Optional[datetime] = None,
    ) -> Message:
        """Create a test message."""
        return Message(
            id=id or uuid4(),
            conversation_id=conversation_id or uuid4(),
            role=MessageRole(role),
            content=content,
            created_at=created_at or datetime.now(timezone.utc),
        )

    def create_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """Create a user message."""
        return self.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    def create_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """Create an assistant message."""
        return self.create(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
        )

    def create_conversation_history(
        self,
        conversation_id: UUID,
        turns: List[tuple[str, str]],
    ) -> List[Message]:
        """
        Create a conversation history.

        Args:
            conversation_id: Conversation UUID
            turns: List of (user_message, assistant_response) tuples

        Returns:
            List of Message entities
        """
        messages = []
        for user_msg, assistant_msg in turns:
            messages.append(self.create_user_message(conversation_id, user_msg))
            messages.append(self.create_assistant_message(conversation_id, assistant_msg))
        return messages
```

---

## Component Test Patterns

### Pattern 1: Test Happy Path

```python
"""
Component test: SendMessage interactor - Happy path
"""

import pytest
from uuid import uuid4

from app.application.chat.commands.send_message import SendMessage
from tests.component.mocks.repositories import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
)
from tests.component.mocks.gateways import MockLLMGateway


@pytest.mark.asyncio
async def test_send_message_creates_user_and_assistant_messages(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
    test_conversation,
):
    """
    WHEN user sends a message to existing conversation
    THEN system SHALL create user message and generate assistant response
    """
    # Arrange
    mock_llm_gateway.set_default_response({
        "content": "DeFi stands for Decentralized Finance...",
        "model": "gpt-4",
        "tokens_used": 120,
    })

    interactor = SendMessage(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    # Act
    result = await interactor.execute(
        conversation_id=test_conversation.id,
        user_id=test_conversation.user_id,
        content="What is DeFi?",
    )

    # Assert
    assert result.message.content == "What is DeFi?"
    assert result.message.role == "user"
    assert result.agent_response is not None
    assert "DeFi stands for" in result.agent_response.content

    # Verify messages saved
    messages = await message_repository.list_by_conversation(test_conversation.id)
    assert len(messages) == 2  # User + assistant
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
```

### Pattern 2: Test Error Scenarios

```python
"""
Component test: SendMessage interactor - Error scenarios
"""

import pytest
from uuid import uuid4

from app.application.chat.commands.send_message import SendMessage
from app.domain.exceptions.chat import ConversationNotFoundError


@pytest.mark.asyncio
async def test_send_message_to_nonexistent_conversation_raises_error(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
):
    """
    WHEN user sends message to non-existent conversation
    THEN system SHALL raise ConversationNotFoundError
    """
    # Arrange
    fake_conversation_id = uuid4()
    interactor = SendMessage(
        conversation_repo=conversation_repository,  # Empty!
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    # Act & Assert
    with pytest.raises(ConversationNotFoundError) as exc_info:
        await interactor.execute(
            conversation_id=fake_conversation_id,
            user_id=123,
            content="Hello",
        )

    assert exc_info.value.conversation_id == fake_conversation_id
```

### Pattern 3: Test with Context

```python
"""
Component test: SendMessage interactor - Conversation context
"""

import pytest

from app.application.chat.commands.send_message import SendMessage


@pytest.mark.asyncio
async def test_send_message_includes_conversation_history(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
    conversation_with_messages,
):
    """
    WHEN user sends message in conversation with history
    THEN system SHALL include previous messages in LLM context
    """
    # Arrange
    test_conversation, existing_messages = conversation_with_messages

    interactor = SendMessage(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    # Act
    await interactor.execute(
        conversation_id=test_conversation.id,
        user_id=test_conversation.user_id,
        content="Tell me more",
    )

    # Assert: Verify LLM was called with history
    mock_llm_gateway.assert_called_once()
    call_history = mock_llm_gateway.get_call_history()
    llm_messages = call_history[0]["messages"]

    # Should include previous messages + new message
    assert len(llm_messages) >= 3  # Previous 2 + new 1
```

### Pattern 4: Test Integration Between Components

```python
"""
Component test: Agent Squad orchestration
"""

import pytest
from app.application.agent_squad.commands.orchestrate_response import OrchestrateChatResponse


@pytest.mark.asyncio
async def test_orchestrate_response_classifies_intent_and_routes_correctly(
    conversation_repository,
    message_repository,
    mock_intent_gateway,
    mock_llm_gateway,
    test_conversation,
):
    """
    WHEN orchestrator receives message
    THEN system SHALL classify intent and route to correct agent
    """
    # Arrange
    mock_intent_gateway.set_default_intent({
        "agent_type": "HUNTER_AI",
        "confidence": 0.94,
        "reasoning": "Market sentiment query",
    })

    orchestrator = OrchestrateChatResponse(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        intent_gateway=mock_intent_gateway,
        llm_gateway=mock_llm_gateway,
    )

    # Act
    result = await orchestrator.execute(
        conversation_id=test_conversation.id,
        user_id=test_conversation.user_id,
        content="What's the sentiment for ETH?",
    )

    # Assert
    assert result.agent_type == "HUNTER_AI"
    assert result.confidence >= 0.9
    # Verify intent classification was called
    # Verify correct agent handler was invoked
```

---

## Migration Guidelines

### Step-by-Step Migration Process

#### Step 1: Identify HTTP Integration Test to Migrate

**Current HTTP Integration Test:**
```python
# tests/integration/chat/test_message_handling.py

def test_send_message_returns_response(self, client):
    conversation_id = str(uuid4())
    response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        json={"content": "Hello, what is DeFi?"}
    )

    if response.status_code == 201:
        data = response.json()
        assert "user_message" in data or "message" in data
```

#### Step 2: Create Component Test

**New Component Test:**
```python
# tests/component/chat/test_send_message.py

@pytest.mark.asyncio
async def test_send_message_creates_message(
    conversation_repository,
    message_repository,
    mock_llm_gateway,
    test_conversation,
):
    """Component test: Focus on business logic."""
    # Arrange
    interactor = SendMessage(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
        llm_gateway=mock_llm_gateway,
    )

    # Act
    result = await interactor.execute(
        conversation_id=test_conversation.id,
        user_id=test_conversation.user_id,
        content="Hello, what is DeFi?",
    )

    # Assert
    assert result.message.content == "Hello, what is DeFi?"
    assert result.agent_response is not None
```

#### Step 3: Verify Equivalence

**Checklist:**
- [ ] Component test covers same business logic
- [ ] Component test validates same outcomes
- [ ] Component test runs faster (<0.5s)
- [ ] Component test has clearer assertions

#### Step 4: Remove or Simplify HTTP Test

**Options:**

**Option A: Delete HTTP test** (if pure business logic)
```python
# Delete test_send_message_returns_response from integration/
```

**Option B: Convert to E2E smoke test** (if validates HTTP concerns)
```python
# Move to integration/flows/test_chat_flow_complete.py
# Simplify to high-level E2E validation
```

### Migration Checklist

**Before Migration:**
- [ ] Read HTTP integration test
- [ ] Identify business logic being tested
- [ ] Identify HTTP-specific concerns (auth, routing, serialization)
- [ ] List all dependencies (repos, gateways, services)

**During Migration:**
- [ ] Create in-memory repositories if needed
- [ ] Create mock gateways if needed
- [ ] Write component test with direct interactor call
- [ ] Use fixtures for setup (test_conversation, test_user)
- [ ] Focus assertions on business outcomes

**After Migration:**
- [ ] Run component test (verify <0.5s execution)
- [ ] Verify test passes
- [ ] Verify test covers same logic as HTTP test
- [ ] Delete or simplify HTTP test
- [ ] Update test documentation

### Common Migration Patterns

**Pattern 1: Simple Command**
```
HTTP Test → Component Test (1:1 mapping)
Delete HTTP test after migration
```

**Pattern 2: Query with Pagination**
```
HTTP Test → Component Test (business logic)
Keep simplified E2E test (HTTP pagination validation)
```

**Pattern 3: Complex Flow**
```
HTTP Test → Multiple Component Tests (one per step)
Keep simplified E2E test (full flow validation)
```

**Pattern 4: Auth-Heavy Test**
```
HTTP Test → Component Test (business logic)
Keep HTTP test (auth validation is HTTP concern)
```

---

## Next Steps

### Phase 2: Implementation (Week 3-4)

1. **Create Component Test Infrastructure**
   - Implement `tests/component/conftest.py`
   - Implement in-memory repositories
   - Implement mock gateways
   - Implement test data factories

2. **Validate with Pilot Migration**
   - Migrate 1-2 tests from `test_intent_classification.py`
   - Validate fixture patterns work
   - Measure performance improvement
   - Refine design based on learnings

3. **Document Patterns**
   - Create component test examples
   - Document common pitfalls
   - Create migration guide for developers

### Phase 3: Migration (Week 5-8)

- **Week 5**: Tier 1 (Agent Squad - 10 tests)
- **Week 6**: Tier 2 (Chat - 15 tests)
- **Week 7**: Tier 3 (Hunter/Ultra/GraphRAG - 20 tests)
- **Week 8**: Tier 4 (Auth/Admin - 15 tests)

---

## Conclusion

Component testing layer provides:
- ✅ **3-5x faster** tests (no HTTP overhead)
- ✅ **Clearer failures** (exact component location)
- ✅ **Better isolation** (one component at a time)
- ✅ **Easier mocking** (direct dependency injection)

**Example already exists**: `test_intent_classification.py` is already component-level!

**Next**: Implement component test infrastructure and start Tier 1 migration.
