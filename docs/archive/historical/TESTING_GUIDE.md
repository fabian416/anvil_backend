# Comprehensive API Testing Guide

This guide documents the testing strategy, test structure, and how to run tests for the Anvil Backend API.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Test Categories and Markers](#test-categories-and-markers)
3. [Running Tests Locally](#running-tests-locally)
4. [Test Helpers and Utilities](#test-helpers-and-utilities)
5. [Test Data Builders](#test-data-builders)
6. [Writing New Tests](#writing-new-tests)
7. [CI/CD Integration](#cicd-integration)

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── helpers/                       # Test utility modules
│   ├── __init__.py
│   ├── auth_helper.py            # Authentication test utilities
│   ├── api_client.py             # Authenticated API client wrapper
│   ├── db_manager.py             # Database test management
│   ├── error_validator.py        # Error response validation
│   └── llm_verifier.py           # LLM response verification
├── builders/                      # Test data builders
│   ├── __init__.py
│   ├── user_builder.py           # User test data
│   ├── conversation_builder.py   # Conversation test data
│   ├── message_builder.py        # Message test data
│   ├── subscription_builder.py   # Subscription test data
│   └── error_test_case_builder.py # Error scenario builder
├── app/unit/                      # Domain/application unit tests
│   ├── factories/                # Test factories
│   │   ├── user_entity.py        # User entity factory
│   │   └── value_objects.py      # Value object factories
│   ├── application/              # Application layer tests
│   │   └── authz_service/        # Authorization tests
│   └── domain/                   # Domain layer tests
│       └── services/             # Domain service tests
├── unit/                          # Infrastructure unit tests
│   ├── presentation/
│   │   ├── account/              # Auth/profile controllers
│   │   ├── admin/                # Admin controllers
│   │   ├── chat/                 # Chat controllers
│   │   ├── subscription/         # Subscription controllers
│   │   ├── wallet/               # Wallet controllers
│   │   ├── graph/                # GraphRAG controllers
│   │   ├── ml/                   # ML prediction controllers
│   │   └── websocket/            # WebSocket handlers
│   └── infrastructure/
│       ├── adapters/             # DeFi adapter tests
│       │   ├── test_aave_adapter.py
│       │   ├── test_curve_adapter.py
│       │   ├── test_axelar_adapter.py
│       │   └── ... (other adapters)
│       └── agents/               # Agent tests
├── integration/                   # Integration tests
│   ├── auth/                     # Authentication flows
│   ├── user/                     # User profile management
│   ├── chat/                     # Chat functionality
│   ├── admin/                    # Admin operations
│   ├── subscription/             # Subscription lifecycle
│   ├── wallet/                   # Wallet operations
│   ├── graph/                    # GraphRAG search
│   ├── ml/                       # ML predictions
│   ├── websocket/                # WebSocket real-time
│   ├── defi/                     # DeFi integration tests
│   ├── agent_squad_tests/        # Agent Squad tests
│   ├── mcp/                      # MCP server tests
│   └── error_handling/           # Error format verification
├── e2e/                          # End-to-end tests
│   ├── user/                     # User journey tests
│   ├── admin/                    # Admin workflow tests
│   └── subscription/             # Subscription workflow tests
├── security/                      # Security tests
│   ├── auth/                     # Auth security
│   ├── admin/                    # Authorization boundaries
│   └── validation/               # Input validation security
├── templates/                     # Test templates (*.template files)
│   ├── test_endpoint_template.template
│   ├── test_entity_template.template
│   └── ... (other templates)
└── load/                         # Load and performance tests
```

> **Note**: Test templates in `tests/templates/` use `.template` extension and contain 
> placeholder patterns like `<EndpointName>`. They are not executed as tests but serve 
> as blueprints for creating new test files.

## Test Categories and Markers

Tests are organized using pytest markers for easy filtering:

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Isolated unit tests | `pytest -m unit` |
| `integration` | Integration tests with database | `pytest -m integration` |
| `e2e` | End-to-end user journey tests | `pytest -m e2e` |
| `security` | Security-focused tests | `pytest -m security` |
| `load` | Load and performance tests | `pytest -m load` |
| `auth` | Authentication tests | `pytest -m auth` |
| `chat` | Chat/conversation tests | `pytest -m chat` |
| `admin` | Admin functionality tests | `pytest -m admin` |
| `subscription` | Subscription/payment tests | `pytest -m subscription` |
| `graphrag` | GraphRAG search tests | `pytest -m graphrag` |
| `ml` | ML prediction tests | `pytest -m ml` |
| `websocket` | WebSocket tests | `pytest -m websocket` |
| `wallet` | Wallet tests | `pytest -m wallet` |
| `slow` | Tests taking >5 seconds | `pytest -m "not slow"` |

## Running Tests Locally

### Prerequisites

1. Install test dependencies:
```bash
uv pip install -e '.[dev,test]'
```

2. Set up test database:
```bash
make up.db
```

### Basic Commands

```bash
# Run all tests
make code.test

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/presentation/account/test_auth_controllers.py

# Run specific test class
pytest tests/unit/presentation/account/test_auth_controllers.py::TestSignUpController

# Run specific test method
pytest tests/unit/presentation/account/test_auth_controllers.py::TestSignUpController::test_signup_request_structure
```

### Run by Category

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Security tests only
pytest -m security

# Skip slow tests
pytest -m "not slow"

# Multiple markers (OR)
pytest -m "auth or chat"

# Multiple markers (AND)
pytest -m "integration and auth"
```

### Coverage Reports

```bash
# Generate coverage report
make code.cov

# Generate HTML coverage report
make code.cov.html
```

## Test Helpers and Utilities

### AuthHelper

Create authenticated test users and tokens:

```python
from tests.helpers.auth_helper import AuthHelper

# Create test user with default role
user, token = AuthHelper.create_test_user()

# Create admin user
admin_user, admin_token = AuthHelper.create_test_user(role="admin")

# Create super admin
super_admin, sa_token = AuthHelper.create_test_user(role="super_admin")

# Get auth headers
headers = AuthHelper.get_auth_headers(token)
```

### AuthenticatedClient

Simplified authenticated API testing:

```python
from tests.helpers.api_client import AuthenticatedClient

client = AuthenticatedClient()

# Login as regular user
client.login("user@example.com", "password")

# Make authenticated requests
response = client.get("/api/v1/account/me")

# Switch to admin
with client.as_admin():
    response = client.get("/api/v1/admin/users")
```

### ErrorValidator

Validate error responses:

```python
from tests.helpers.error_validator import ErrorValidator

# Validate error response
result = ErrorValidator.validate_error_response(
    response_data,
    expected_code="USER_001",
    expected_status=404,
)

# Validate i18n key
ErrorValidator.validate_i18n_key(error_data)
```

### LLMVerifier

Verify LLM responses:

```python
from tests.helpers.llm_verifier import LLMVerifier

# Verify response structure
LLMVerifier.verify_response_structure(response)

# Verify content relevance
LLMVerifier.verify_content_relevance(query, response)

# Verify risk disclaimers
LLMVerifier.verify_risk_disclaimers(response)
```

## Test Factories

Test factories provide consistent test data for domain entities and value objects.

### User Entity Factory

Located in `tests/app/unit/factories/user_entity.py`:

```python
from tests.app.unit.factories.user_entity import create_user
from app.domain.enums.user_role import UserRole

# Create default user
user = create_user()

# Create user with specific role
admin = create_user(role=UserRole.ADMIN)

# Create user with custom email
user = create_user(email=create_email("custom@example.com"))
```

**Important**: The factory uses `id_=` (with underscore) to match the Entity base class signature.

### Value Objects Factory

Located in `tests/app/unit/factories/value_objects.py`:

```python
from tests.app.unit.factories.value_objects import (
    create_user_id,
    create_email,
    create_first_name,
    create_last_name,
    create_password_hash,
    create_raw_password,
    create_language,
    create_user_active,
    create_user_blocked,
    create_user_verified,
)

# Create unique user IDs (auto-incrementing)
user_id_1 = create_user_id()  # UserId(1)
user_id_2 = create_user_id()  # UserId(2)

# Create with specific value
user_id = create_user_id(value=100)  # UserId(100)

# Create other value objects
email = create_email("test@example.com")
password = create_raw_password("SecureP@ss123")
```

**Note**: `create_user_id()` uses an auto-incrementing counter to ensure unique IDs across tests.

## Test Data Builders

Use fluent builders for test data:

### UserBuilder

```python
from tests.builders import a_user

user = (
    a_user()
    .with_email("test@example.com")
    .with_role("admin")
    .as_verified()
    .build()
)
```

### ConversationBuilder

```python
from tests.builders import a_conversation

conversation = (
    a_conversation()
    .with_title("Test Conversation")
    .with_messages(5)
    .for_user(user_id)
    .build()
)
```

### MessageBuilder

```python
from tests.builders import a_message

message = (
    a_message()
    .with_role("user")
    .with_content("Hello!")
    .in_conversation(conversation_id)
    .build()
)

# Create agent response
agent_message = (
    a_message()
    .with_agent_type("chat")
    .as_llm_response()
    .build()
)
```

### SubscriptionBuilder

```python
from tests.builders import a_subscription

subscription = (
    a_subscription()
    .as_premium()
    .as_active()
    .for_user(user_id)
    .build()
)
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [Feature] controllers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.helpers.auth_helper import AuthHelper


class TestFeatureController:
    """Unit tests for Feature controller."""

    @pytest.fixture
    def mock_interactor(self):
        """Create mock interactor."""
        interactor = AsyncMock()
        interactor.execute = AsyncMock(return_value={...})
        return interactor

    def test_request_structure(self):
        """Test request structure validation."""
        request_data = {...}
        assert "required_field" in request_data

    def test_response_structure(self, mock_interactor):
        """Test response structure."""
        response = {...}
        assert "expected_field" in response

    def test_error_handling(self):
        """Test error response format."""
        error_response = {
            "error": {
                "code": "FEATURE_001",
                "message": "Error message",
                "i18n_key": "errors.feature.error_type",
                "http_status": 400,
            }
        }
        assert error_response["error"]["code"] == "FEATURE_001"
```

### Integration Test Template

```python
"""
Integration tests for [Feature] functionality.
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper


@pytest.mark.integration
class TestFeatureIntegration:
    """Integration tests for Feature."""

    def test_successful_operation(self, client):
        """
        WHEN user performs operation
        THEN system SHALL succeed
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        response = client.post(
            "/api/v1/feature",
            json={...},
            headers=headers,
        )

        assert response.status_code in (200, 201)

    def test_error_scenario(self, client):
        """
        WHEN invalid request
        THEN system SHALL return error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        response = client.post(
            "/api/v1/feature",
            json={"invalid": "data"},
            headers=headers,
        )

        assert response.status_code in (400, 422)
```

## Pytest Configuration

The test suite is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow",
    "integration",
    "unit",
    "e2e",
    "load",
    "security",
    "contract",
    "auth",
    "subscription"
]
addopts = "-m 'not slow' --ignore=libs"
asyncio_default_fixture_loop_scope = "function"
norecursedirs = ["libs/*", "libs"]
```

### Key Configuration Notes

1. **`--ignore=libs`**: The `libs/` directory contains external library submodules with their own test suites. These are excluded to prevent conflicts.

2. **`norecursedirs`**: Prevents pytest from recursing into `libs/` directories.

3. **Agent Squad Tests**: Located in `tests/integration/agent_squad_tests/` (note the `_tests` suffix) to avoid module name conflicts with `libs/agent-squad/python/src/agent_squad`.

4. **Template Files**: Test templates use `.template` extension instead of `.py` to prevent pytest from treating them as test files.

## CI/CD Integration

Tests are automatically run on all pull requests via GitHub Actions.

### Pipeline Stages

1. **Lint**: Code style and type checking
2. **Unit Tests**: Fast, isolated tests
3. **Integration Tests**: Database-dependent tests
4. **Security Tests**: Security-focused tests
5. **Coverage Report**: Minimum 70% coverage required

### Running CI Locally

```bash
# Run full CI checks
make code.check

# Run lint only
make code.lint

# Run tests with coverage
make code.cov
```

### Coverage Requirements

- Domain layer: 90%+
- Application layer: 80%+
- Infrastructure layer: 70%+
- Presentation layer: 70%+

---

## Quick Reference

### Common Commands

| Command | Description |
|---------|-------------|
| `make code.test` | Run all tests |
| `pytest -m unit` | Run unit tests |
| `pytest -m integration` | Run integration tests |
| `pytest -m security` | Run security tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest --lf` | Run last failed tests |

### Test Markers

| Marker | Use Case |
|--------|----------|
| `@pytest.mark.unit` | Isolated tests |
| `@pytest.mark.integration` | Database tests |
| `@pytest.mark.e2e` | User journeys |
| `@pytest.mark.security` | Security tests |
| `@pytest.mark.load` | Performance tests |
