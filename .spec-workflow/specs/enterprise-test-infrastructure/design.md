# Design Document: Enterprise Test Infrastructure

## Overview

This document defines the technical architecture for an enterprise-grade test infrastructure that enables fully reproducible, isolated, and fast test execution. The infrastructure builds upon existing components (`conftest.py`, `AuthHelper`, `DatabaseTestManager`, builders) while introducing new capabilities for mock services, containerized databases, and CI/CD integration.

The design addresses the current **167 failing tests** by providing proper database connectivity, external service mocks, and authenticated session management.

## Steering Document Alignment

### Technical Standards (tech.md)

The design follows documented technical patterns:

- **Hexagonal Architecture**: Test infrastructure respects layer boundaries - domain tests don't require infrastructure, infrastructure tests don't pollute domain
- **Dependency Injection**: Test containers use Dishka for consistent DI in test context
- **CQRS Pattern**: Separate test factories for command models (entities) vs query models (DTOs)
- **Async-First**: All database fixtures use async SQLAlchemy with `pytest-asyncio`
- **Type Safety**: Full type hints on all factory methods and fixtures

### Project Structure (structure.md)

Implementation follows project organization conventions:

```
tests/
├── conftest.py                    # Root fixtures (ENHANCED)
├── pytest.ini                     # Pytest configuration (NEW)
├── fixtures/
│   ├── __init__.py               # Fixture exports
│   ├── database.py               # Database fixtures (NEW)
│   ├── factories/                # Factory classes (ENHANCED)
│   │   ├── __init__.py
│   │   ├── base.py              # BaseFactory class
│   │   ├── user_factory.py      # User factory
│   │   ├── conversation_factory.py
│   │   ├── message_factory.py
│   │   ├── subscription_factory.py
│   │   └── agent_factory.py
│   └── mocks/                    # Mock services (NEW)
│       ├── __init__.py
│       ├── stripe_mock.py
│       ├── mailgun_mock.py
│       ├── defi_mock.py
│       └── llm_mock.py
├── helpers/
│   ├── auth_helper.py            # Auth utilities (EXISTS - ENHANCED)
│   ├── db_manager.py             # DB manager (EXISTS - ENHANCED)
│   └── api_client.py             # Test API client (EXISTS)
├── config/
│   └── test/                     # Test-specific config (NEW)
│       ├── config.toml
│       └── .secrets.toml
└── docker/
    └── docker-compose.test.yml   # Test database container (NEW)
```

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | Enhancement |
|-----------|----------|-------------|
| **AuthHelper** | `tests/helpers/auth_helper.py` | Add database persistence for tokens |
| **DatabaseTestManager** | `tests/helpers/db_manager.py` | Add PostgreSQL support, migration runner |
| **ConversationBuilder** | `tests/builders/conversation_builder.py` | Add `create()` method for DB persistence |
| **MessageBuilder** | `tests/builders/message_builder.py` | Integrate with ConversationFactory |
| **UserBuilder** | `tests/builders/user_builder.py` | Add role-based creation |
| **conftest.py** | `tests/conftest.py` | Add session-scoped DB, factory fixtures |

### Integration Points

| System | Integration Method |
|--------|-------------------|
| **PostgreSQL** | Docker container with migration runner |
| **Redis** | `fakeredis` for caching tests |
| **Stripe** | Mock client with recorded responses |
| **Mailgun** | Mock client capturing sent emails |
| **DeFi APIs** | Mock adapters returning fixtures |
| **OpenAI/LLM** | Mock gateway with configurable responses |

---

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Test Execution"
        T[Test Functions]
        PT[Pytest Fixtures]
    end

    subgraph "Fixture Layer"
        AF[Auth Fixtures]
        DF[Database Fixtures]
        MF[Mock Fixtures]
        FF[Factory Fixtures]
    end

    subgraph "Infrastructure Layer"
        DB[(PostgreSQL Container)]
        REDIS[(fakeredis)]
        MOCKS[Mock Services]
    end

    subgraph "Factory Layer"
        UF[UserFactory]
        CF[ConversationFactory]
        SF[SubscriptionFactory]
        MsgF[MessageFactory]
    end

    T --> PT
    PT --> AF
    PT --> DF
    PT --> MF
    PT --> FF

    AF --> DB
    DF --> DB
    MF --> MOCKS
    FF --> UF
    FF --> CF
    FF --> SF
    FF --> MsgF

    UF --> DB
    CF --> DB
    SF --> DB
    MsgF --> DB
```

### Modular Design Principles

- **Single File Responsibility**: Each factory handles one domain entity
- **Component Isolation**: Mock services are independent and composable
- **Service Layer Separation**: Fixtures (data access) vs Factories (business logic) vs Mocks (external)
- **Utility Modularity**: Helpers focus on single purpose (auth, db, api)

---

## Components and Interfaces

### Component 1: BaseFactory

- **Purpose:** Abstract base class for all test data factories with common functionality
- **Interfaces:**
  ```python
  class BaseFactory[T]:
      @classmethod
      def build(cls, **overrides) -> T:
          """Create in-memory entity without DB persistence"""
      
      @classmethod
      async def create(cls, session: AsyncSession, **overrides) -> T:
          """Create entity and persist to database"""
      
      @classmethod
      async def create_batch(cls, session: AsyncSession, count: int, **overrides) -> list[T]:
          """Create multiple entities"""
      
      @classmethod
      def build_dict(cls, **overrides) -> dict:
          """Create dictionary representation"""
  ```
- **Dependencies:** SQLAlchemy AsyncSession, domain entities
- **Reuses:** Existing builder patterns from `tests/builders/`

### Component 2: UserFactory

- **Purpose:** Create test users with proper password hashing and role assignment
- **Interfaces:**
  ```python
  class UserFactory(BaseFactory[User]):
      @classmethod
      def build(
          cls,
          email: str | None = None,
          password: str = "TestPass123!",
          role: UserRole = UserRole.USER,
          is_active: bool = True,
          is_verified: bool = True,
          **overrides
      ) -> User
      
      @classmethod
      async def create_with_session(
          cls,
          session: AsyncSession,
          **overrides
      ) -> tuple[User, AuthSession]:
          """Create user with active auth session"""
      
      @classmethod
      async def create_admin(cls, session: AsyncSession) -> User:
          """Shortcut for admin user creation"""
      
      @classmethod
      async def create_super_admin(cls, session: AsyncSession) -> User:
          """Shortcut for super admin creation"""
  ```
- **Dependencies:** AuthHelper, bcrypt, User entity
- **Reuses:** `tests/builders/user_builder.py`, `tests/helpers/auth_helper.py`

### Component 3: ConversationFactory

- **Purpose:** Create conversations with optional messages and agent sessions
- **Interfaces:**
  ```python
  class ConversationFactory(BaseFactory[Conversation]):
      @classmethod
      async def create_with_messages(
          cls,
          session: AsyncSession,
          user_id: UUID,
          message_count: int = 5,
          include_agent_responses: bool = True,
          **overrides
      ) -> Conversation
      
      @classmethod
      async def create_with_agent_session(
          cls,
          session: AsyncSession,
          user_id: UUID,
          agent_type: AgentType,
          **overrides
      ) -> tuple[Conversation, AgentSession]
  ```
- **Dependencies:** MessageFactory, AgentSessionFactory, Conversation entity
- **Reuses:** `tests/builders/conversation_builder.py`

### Component 4: MockStripeClient

- **Purpose:** Simulate Stripe API responses without real API calls
- **Interfaces:**
  ```python
  class MockStripeClient:
      def __init__(self, default_responses: dict | None = None):
          self.calls: list[MockCall] = []
          self.responses: dict[str, Any] = default_responses or {}
      
      def set_response(self, method: str, response: dict) -> None:
          """Configure response for specific method"""
      
      def set_error(self, method: str, error: stripe.error.StripeError) -> None:
          """Configure error response"""
      
      async def create_customer(self, **kwargs) -> MockCustomer:
          """Mock customer creation"""
      
      async def create_subscription(self, **kwargs) -> MockSubscription:
          """Mock subscription creation"""
      
      async def cancel_subscription(self, subscription_id: str) -> MockSubscription:
          """Mock subscription cancellation"""
      
      def assert_called(self, method: str, times: int = 1) -> None:
          """Assert method was called expected times"""
      
      def get_calls(self, method: str) -> list[MockCall]:
          """Get all calls to specific method"""
  ```
- **Dependencies:** None (self-contained mock)
- **Reuses:** None (new implementation)

### Component 5: MockMailgunClient

- **Purpose:** Capture outgoing emails for assertion without sending
- **Interfaces:**
  ```python
  class MockMailgunClient:
      def __init__(self):
          self.sent_emails: list[MockEmail] = []
      
      async def send(
          self,
          to: str | list[str],
          subject: str,
          body: str,
          html: str | None = None,
          **kwargs
      ) -> MockEmailResponse:
          """Mock email sending, captures for assertion"""
      
      def get_emails_to(self, recipient: str) -> list[MockEmail]:
          """Get all emails sent to recipient"""
      
      def get_emails_with_subject(self, subject_contains: str) -> list[MockEmail]:
          """Get emails with subject containing string"""
      
      def assert_email_sent(
          self,
          to: str,
          subject_contains: str | None = None,
      ) -> MockEmail:
          """Assert email was sent, return it"""
      
      def clear(self) -> None:
          """Clear captured emails"""
  ```
- **Dependencies:** None (self-contained mock)
- **Reuses:** None (new implementation)

### Component 6: MockDeFiDataProvider

- **Purpose:** Provide deterministic DeFi data for testing without API calls
- **Interfaces:**
  ```python
  class MockDeFiDataProvider:
      def __init__(self):
          self._tvl_data: dict[str, float] = {}
          self._price_data: dict[str, float] = {}
          self._yield_data: dict[str, list[dict]] = {}
      
      def set_protocol_tvl(self, protocol: str, tvl: float) -> None:
          """Configure TVL for protocol"""
      
      def set_token_price(self, token: str, price: float) -> None:
          """Configure price for token"""
      
      def set_yield_pools(self, protocol: str, pools: list[dict]) -> None:
          """Configure yield pools"""
      
      async def get_protocol_tvl(self, protocol: str) -> float:
          """Get mocked TVL"""
      
      async def get_token_price(self, token: str) -> float:
          """Get mocked price"""
      
      async def get_yield_pools(self, protocol: str) -> list[dict]:
          """Get mocked yield pools"""
  ```
- **Dependencies:** None (self-contained mock)
- **Reuses:** Response structures from actual adapters

### Component 7: TestDatabaseManager (Enhanced)

- **Purpose:** Manage PostgreSQL test database lifecycle with migrations
- **Interfaces:**
  ```python
  class TestDatabaseManager:
      def __init__(
          self,
          database_url: str | None = None,
          run_migrations: bool = True,
      ):
          ...
      
      async def setup(self) -> AsyncEngine:
          """Create engine, run migrations, return engine"""
      
      async def create_session(self) -> AsyncSession:
          """Create new session with savepoint"""
      
      async def rollback_session(self, session: AsyncSession) -> None:
          """Rollback session to savepoint"""
      
      async def teardown(self) -> None:
          """Dispose engine and cleanup"""
      
      @staticmethod
      async def run_migrations(engine: AsyncEngine) -> None:
          """Apply all Alembic migrations"""
      
      @staticmethod
      def get_test_database_url() -> str:
          """Get URL from env or default to container"""
  ```
- **Dependencies:** SQLAlchemy, Alembic, existing `db_manager.py`
- **Reuses:** `tests/helpers/db_manager.py` enhanced with PostgreSQL support

---

## Data Models

### MockCall

```python
@dataclass
class MockCall:
    """Record of a mock method call"""
    method: str
    args: tuple
    kwargs: dict
    timestamp: datetime
    response: Any | None = None
    error: Exception | None = None
```

### MockEmail

```python
@dataclass
class MockEmail:
    """Captured email for assertion"""
    to: list[str]
    subject: str
    body: str
    html: str | None
    from_email: str
    sent_at: datetime
    headers: dict[str, str] = field(default_factory=dict)
```

### MockSubscription

```python
@dataclass
class MockSubscription:
    """Mock Stripe subscription"""
    id: str
    customer: str
    status: str  # active, canceled, past_due, etc.
    plan_id: str
    current_period_start: int
    current_period_end: int
    cancel_at_period_end: bool = False
```

### TestDatabaseConfig

```python
@dataclass
class TestDatabaseConfig:
    """Test database configuration"""
    host: str = "localhost"
    port: int = 5433  # Different from dev port
    database: str = "anvil_test"
    user: str = "anvil_test"
    password: str = "test_password"
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
```

---

## Error Handling

### Error Scenarios

1. **Database Connection Failure**
   - **Handling:** Skip integration tests, run unit tests only
   - **User Impact:** Clear skip message with setup instructions

2. **Migration Failure**
   - **Handling:** Fail fast with detailed migration error
   - **User Impact:** Show which migration failed and how to fix

3. **Factory Creation Failure**
   - **Handling:** Raise `FactoryError` with entity details
   - **User Impact:** Clear message about which field caused failure

4. **Mock Configuration Missing**
   - **Handling:** Return sensible defaults, warn in logs
   - **User Impact:** Test continues but may have unexpected values

5. **Session Rollback Failure**
   - **Handling:** Force close session, log error
   - **User Impact:** Test marked as error, cleanup attempted

---

## Testing Strategy

### Unit Testing

- **Factories**: Test all factory methods produce valid entities
- **Mocks**: Test mock configuration and response recording
- **Helpers**: Test AuthHelper token generation and validation
- **Approach**: No database required, pure Python tests

### Integration Testing

- **Database Fixtures**: Test session creation, rollback, cleanup
- **Factory Persistence**: Test factories create valid DB records
- **Migration Runner**: Test migrations apply cleanly
- **Approach**: Requires PostgreSQL container

### End-to-End Testing

- **Full Workflows**: Test complete user journeys with all components
- **API Integration**: Test HTTP endpoints with TestClient
- **WebSocket**: Test real-time features
- **Approach**: Full infrastructure required

---

## Configuration

### Test Configuration (config/test/config.toml)

```toml
[app]
name = "anvil-test"
env = "test"
debug = true

[database]
host = "localhost"
port = 5433
name = "anvil_test"
user = "anvil_test"
pool_size = 5
max_overflow = 10

[redis]
enabled = false  # Use fakeredis

[external_apis]
stripe_enabled = false
mailgun_enabled = false
defi_apis_enabled = false

[testing]
parallel_workers = 4
timeout_seconds = 30
coverage_threshold = 80
```

### Docker Compose for Test Database (docker/docker-compose.test.yml)

```yaml
version: '3.8'

services:
  test-postgres:
    image: postgres:15-alpine
    container_name: anvil_test_db
    environment:
      POSTGRES_USER: anvil_test
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: anvil_test
    ports:
      - "5433:5432"
    volumes:
      - test_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U anvil_test"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  test_postgres_data:
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: anvil_test
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: anvil_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e '.[dev,test]'
      
      - name: Run migrations
        run: alembic upgrade head
        env:
          DATABASE_URL: postgresql://anvil_test:test_password@localhost:5433/anvil_test
      
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml -n 4
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://anvil_test:test_password@localhost:5433/anvil_test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

---

## Performance Considerations

| Aspect | Target | Implementation |
|--------|--------|----------------|
| Test DB Setup | <5s | Connection pooling, cached migrations |
| Factory Creation | <10ms per entity | Lazy attribute evaluation |
| Test Isolation | <50ms overhead | Savepoint rollback (not full recreate) |
| Parallel Execution | 4 workers | Unique DB schemas per worker |
| Full Suite | <5 minutes | Parallel + categorized execution |

---

## Migration Path

### Phase 1: Foundation (Tasks 1-3)
- Create test configuration structure
- Implement BaseFactory and enhance existing factories
- Set up Docker test database

### Phase 2: Mocks (Tasks 4-6)
- Implement MockStripeClient
- Implement MockMailgunClient
- Implement MockDeFiDataProvider

### Phase 3: Integration (Tasks 7-9)
- Enhance conftest.py with new fixtures
- Implement TestDatabaseManager with migrations
- Create pytest plugins for parallel execution

### Phase 4: CI/CD (Tasks 10-12)
- Create GitHub Actions workflow
- Implement coverage enforcement
- Add flaky test detection and retry logic
