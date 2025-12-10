# Enterprise-Grade Test Strategy

**Status**: 🚧 In Progress  
**Target**: 100% Enterprise-Grade Test Coverage  
**Last Updated**: December 10, 2025

---

## 📊 Current State Analysis

### Test Metrics Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT TEST STATUS                          │
├─────────────────────────────────────────────────────────────────┤
│  Unit/Infrastructure Tests:                                     │
│    Passing:          1,013 ✅                                   │
│    Skipped:          42 (intentional)                           │
│    Failing:          0 ✅                                       │
│                                                                 │
│  Integration Tests:                                             │
│    Status:           Pending DI setup                           │
│    Errors:           ~200 (GraphMissingFactoryError)            │
│                                                                 │
│  Collection Errors:  0 ✅                                       │
├─────────────────────────────────────────────────────────────────┤
│  TARGET:             100% passing (excluding intentional skips) │
└─────────────────────────────────────────────────────────────────┘
```

### Issue Categories

| Category | Count | Priority | Complexity |
|----------|-------|----------|------------|
| DI/Container Issues | 120+ | 🔴 Critical | Medium |
| Agent/MCP Mocking | 50+ | 🔴 Critical | High |
| Integration DB Setup | 40+ | 🟡 High | Medium |
| API Contract Mismatches | 30+ | 🟡 High | Low |
| Missing Implementations | 20+ | 🟢 Medium | Low |

---

## 🎯 Strategic Roadmap

### Phase 1: Foundation Fixes (Priority: Critical)
**Duration**: 2-3 days  
**Impact**: ~120 tests fixed

#### 1.1 Fix Dependency Injection Container
**Problem**: `GraphMissingFactoryError` in integration tests

```python
# Current Error Pattern:
dishka.registry_builder.GraphMissingFactoryError: 
    Cannot find factory for <class 'SomeGateway'>
```

**Solution**:
1. Create test-specific DI providers
2. Register mock factories for all gateways
3. Use `override_providers` pattern in test fixtures

**Files to Create/Update**:
- `tests/conftest.py` - Add test container setup
- `tests/fixtures/di_overrides.py` - Mock provider registry
- `src/app/setup/ioc/testing.py` - Test-specific providers

**Implementation**:
```python
# tests/fixtures/di_overrides.py
from dishka import Provider, provide, Scope
from unittest.mock import AsyncMock

class TestInfrastructureProvider(Provider):
    """Test provider with mocked infrastructure."""
    
    @provide(scope=Scope.REQUEST)
    def mock_user_repository(self) -> UserRepository:
        repo = AsyncMock(spec=UserRepository)
        repo.get_by_id.return_value = None
        return repo
    
    @provide(scope=Scope.REQUEST)
    def mock_conversation_gateway(self) -> ConversationQueryGateway:
        gateway = AsyncMock(spec=ConversationQueryGateway)
        return gateway
    
    # ... all other gateways

# tests/conftest.py
@pytest.fixture
def test_container():
    """Create test DI container with mocks."""
    from app.setup.ioc.testing import create_test_container
    return create_test_container()

@pytest.fixture
def app(test_container):
    """Create app with test dependencies."""
    from app.run import create_app_with_container
    return create_app_with_container(test_container)
```

#### 1.2 Fix Agent/MCP Server Tests
**Problem**: Missing `setup_tools` implementations, incorrect mocking

**Solution**:
1. Implement `setup_tools()` in all MCP servers
2. Create proper async mock fixtures
3. Use `AsyncMock` consistently

**Files to Update**:
- `src/app/infrastructure/mcp/servers/*.py` - Add `setup_tools()`
- `tests/infrastructure/mcp/conftest.py` - Proper fixtures
- `tests/infrastructure/agno/conftest.py` - Agent fixtures

---

### Phase 2: Integration Test Infrastructure (Priority: High)
**Duration**: 2-3 days  
**Impact**: ~100 tests fixed

#### 2.1 Test Database Setup
**Problem**: Tests fail due to missing database fixtures

**Solution**:
1. Create in-memory SQLite for unit tests
2. Use PostgreSQL testcontainers for integration
3. Implement proper transaction rollback

**Implementation**:
```python
# tests/fixtures/database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    # Use SQLite for fast unit tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(test_engine):
    """Create transactional test session."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

#### 2.2 API Client Fixtures
**Problem**: Inconsistent API testing patterns

**Solution**:
1. Create `AuthenticatedTestClient` class
2. Implement proper token management
3. Add response validation helpers

**Implementation**:
```python
# tests/fixtures/api_client.py
from fastapi.testclient import TestClient

class AuthenticatedTestClient:
    """Test client with authentication support."""
    
    def __init__(self, app, user_role: str = "user"):
        self.client = TestClient(app)
        self.token = self._get_test_token(user_role)
    
    def _get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def get(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self._get_auth_headers())
        return self.client.get(url, **kwargs)
    
    def post(self, url: str, **kwargs):
        kwargs.setdefault("headers", {}).update(self._get_auth_headers())
        return self.client.post(url, **kwargs)
```

---

### Phase 3: Test Pattern Standardization (Priority: Medium)
**Duration**: 1-2 days  
**Impact**: ~50 tests fixed

#### 3.1 Standardize Test Structure
**Pattern**: Arrange-Act-Assert with clear sections

```python
@pytest.mark.unit
class TestFeature:
    """Unit tests for Feature."""
    
    @pytest.fixture
    def sut(self, mock_dependency):
        """System Under Test."""
        return Feature(dependency=mock_dependency)
    
    def test_successful_operation(self, sut):
        """
        GIVEN valid input
        WHEN operation is called
        THEN should return expected result
        """
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = sut.operation(input_data)
        
        # Assert
        assert result.status == "success"
```

#### 3.2 Error Test Patterns
**Pattern**: Consistent error scenario testing

```python
@pytest.mark.unit
class TestFeatureErrors:
    """Error scenarios for Feature."""
    
    @pytest.mark.parametrize("invalid_input,expected_error", [
        (None, "INPUT_001"),
        ("", "INPUT_002"),
        ({"missing": "field"}, "INPUT_003"),
    ])
    def test_rejects_invalid_input(self, sut, invalid_input, expected_error):
        """
        GIVEN invalid input
        WHEN operation is called
        THEN should raise appropriate error
        """
        with pytest.raises(ValidationError) as exc:
            sut.operation(invalid_input)
        
        assert exc.value.code == expected_error
```

---

### Phase 4: Coverage Gaps (Priority: Medium)
**Duration**: 2-3 days  
**Impact**: Enterprise-grade coverage

#### 4.1 Missing Test Coverage

| Module | Current | Target | Tests Needed |
|--------|---------|--------|--------------|
| Domain Entities | 85% | 95% | ~15 |
| Application Interactors | 70% | 90% | ~30 |
| Infrastructure Adapters | 60% | 85% | ~40 |
| Presentation Controllers | 75% | 90% | ~25 |

#### 4.2 Critical Path Testing

```
User Journey Coverage:
├── Authentication Flow      ✅ 95%
├── Chat/Conversation Flow   🟡 75%
├── Wallet Operations        🟡 70%
├── Subscription Flow        🟡 65%
├── Admin Operations         🟡 70%
└── DeFi Integrations        🔴 50%
```

---

## 🛠️ Implementation Plan

### Week 1: Foundation (Days 1-5)

| Day | Task | Tests Fixed |
|-----|------|-------------|
| 1 | Create test DI container with mock providers | +50 |
| 2 | Fix MCP server `setup_tools` implementations | +30 |
| 3 | Implement database fixtures | +40 |
| 4 | Fix agent/router tests | +30 |
| 5 | API client fixtures + validation | +20 |

**Week 1 Target**: 170 tests fixed → 2,235 passing

### Week 2: Integration (Days 6-10)

| Day | Task | Tests Fixed |
|-----|------|-------------|
| 6 | Fix auth flow integration tests | +25 |
| 7 | Fix admin integration tests | +25 |
| 8 | Fix chat/conversation tests | +25 |
| 9 | Fix subscription tests | +20 |
| 10 | Fix remaining integration tests | +25 |

**Week 2 Target**: 120 tests fixed → 2,355 passing

### Week 3: Polish (Days 11-15)

| Day | Task | Tests Fixed |
|-----|------|-------------|
| 11 | Fix e2e tests | +20 |
| 12 | Fix security tests | +15 |
| 13 | Fix load tests | +10 |
| 14 | Add missing coverage tests | +30 |
| 15 | Final cleanup + documentation | - |

**Week 3 Target**: 100% passing (2,755+ tests)

---

## 📋 Immediate Action Items

### Priority 1: Today (4-6 hours)

```bash
# 1. Create test DI container
touch tests/fixtures/di_overrides.py
touch src/app/setup/ioc/testing.py

# 2. Fix MCP servers
# Add setup_tools() to all servers in:
# - src/app/infrastructure/mcp/servers/

# 3. Update conftest.py with proper fixtures
```

### Priority 2: This Week

1. **Fix all 221 ERROR tests** (DI/import issues)
2. **Fix all 170 FAILED tests** (logic/mocking issues)
3. **Add missing test fixtures**
4. **Document testing patterns**

---

## 🎯 Success Criteria

### Enterprise-Grade Test Suite

| Metric | Target | Current |
|--------|--------|---------|
| Pass Rate | 100% | 75% |
| Coverage (Domain) | 95% | ~85% |
| Coverage (Application) | 90% | ~70% |
| Coverage (Infrastructure) | 85% | ~60% |
| Coverage (Presentation) | 90% | ~75% |
| Collection Errors | 0 | 0 ✅ |
| Flaky Tests | 0 | ~5 |
| Test Execution Time | <5min | ~6min |

### Quality Gates

```yaml
# .github/workflows/test.yml
quality_gates:
  - name: "All tests pass"
    condition: "failures == 0 && errors == 0"
  
  - name: "Coverage threshold"
    condition: "coverage >= 85%"
  
  - name: "No flaky tests"
    condition: "flaky_count == 0"
  
  - name: "Fast execution"
    condition: "duration <= 300s"
```

---

## 📚 References

- [Testing Guide](./TESTING_GUIDE.md)
- [DeFi Adapters Guide](../features/defi-adapters/DEFI_ADAPTERS_GUIDE.md)
- [Architecture Overview](../architecture/technical_architecture.md)
- [CI/CD Configuration](../../.github/workflows/)
