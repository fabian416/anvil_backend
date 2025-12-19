# Testing Guidelines

**Comprehensive guide for writing and maintaining tests in the Anvil Backend project.**

---

## 📋 **TABLE OF CONTENTS**

1. [Overview](#overview)
2. [Test Organization](#test-organization)
3. [Writing Tests](#writing-tests)
4. [Test Data](#test-data)
5. [Running Tests](#running-tests)
6. [Best Practices](#best-practices)
7. [Advanced Techniques](#advanced-techniques)

---

## 🎯 **OVERVIEW**

### **Test Coverage Goals**

```
Current Coverage:      ~80%
Target Coverage:       85%+

Domain Layer:          85-90%
Application Layer:     80-85%
Infrastructure:        75-80%
Presentation:          80-85%
Integration:           75-80%
```

### **Test Categories**

- **Unit Tests**: Fast, isolated component tests
- **Integration Tests**: Tests with real dependencies
- **E2E Tests**: Full user journey tests
- **Performance Tests**: Speed and load tests
- **Security Tests**: Vulnerability tests

---

## 📁 **TEST ORGANIZATION**

### **Directory Structure**

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain entity/value object tests
│   ├── application/        # Application layer tests
│   ├── infrastructure/     # Infrastructure adapter tests
│   └── presentation/       # Presentation layer tests
├── integration/            # Integration tests
│   ├── database/          # Database integration tests
│   ├── flows/             # Business flow tests
│   └── workflows/         # Complex workflow tests
├── e2e/                    # End-to-end tests
│   ├── endpoints/         # API endpoint tests
│   └── scenarios/         # User scenario tests
├── performance/            # Performance tests
├── security/               # Security tests
├── advanced/               # Advanced test techniques
├── builders/               # Test data builders
├── fixtures/               # Reusable test fixtures
└── templates/              # Test templates
```

### **File Naming**

- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

---

## ✍️ **WRITING TESTS**

### **Test Structure (AAA Pattern)**

```python
def test_example():
    """Test description following Google style."""
    # Arrange: Set up test data
    user_id = 12345
    conversation = create_conversation(user_id)
    
    # Act: Execute the code under test
    result = conversation.add_message("Hello")
    
    # Assert: Verify the results
    assert result is not None
    assert result.content == "Hello"
```

### **Test Markers**

```python
import pytest

@pytest.mark.unit           # Fast, isolated test
@pytest.mark.integration    # Tests with dependencies
@pytest.mark.slow           # Slow-running test
@pytest.mark.asyncio        # Async test
@pytest.mark.performance    # Performance test
@pytest.mark.security       # Security test
```

### **Using Test Builders**

```python
from tests.builders.user_builder import a_user, an_admin
from tests.builders.conversation_builder import a_conversation
from tests.builders.message_builder import a_user_message

def test_with_builders():
    """Test using fluent builders."""
    # Create test data easily
    user = a_user().with_email("test@example.com").build_dict()
    admin = an_admin().with_id(999).build_dict()
    
    conversation = (a_conversation()
                   .with_user_id(user["id"])
                   .with_title("Test Chat")
                   .build_dict())
    
    message = (a_user_message()
              .with_conversation_id(conversation["id"])
              .with_content("Hello")
              .build_dict())
```

---

## 🏗️ **TEST DATA**

### **Test Data Builders**

Use builders for complex test data:

```python
# Simple, fluent interface
user = a_user().as_admin().build_dict()

# Chainable methods
conversation = (a_conversation()
               .with_user_id(123)
               .with_title("DeFi Discussion")
               .build_dict())
```

### **Fixtures**

```python
@pytest.fixture
def test_user():
    """Fixture providing test user."""
    return {"id": 123, "email": "test@example.com"}

def test_with_fixture(test_user):
    """Test using fixture."""
    assert test_user["id"] == 123
```

### **Factory Functions**

```python
def create_test_conversation(user_id=123, title=None):
    """Factory for test conversations."""
    return {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": title,
        "created_at": datetime.utcnow().isoformat()
    }
```

---

## 🚀 **RUNNING TESTS**

### **Basic Commands**

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/domain/test_conversation.py

# Run specific test
pytest tests/unit/domain/test_conversation.py::test_create_conversation

# Run tests by marker
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m "unit and not slow"  # Combined markers

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show slowest tests
pytest --durations=10
```

### **Coverage Reports**

```bash
# Run with coverage
pytest --cov=src/app

# HTML coverage report
pytest --cov=src/app --cov-report=html
# View: htmlcov/index.html

# Terminal coverage report
pytest --cov=src/app --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src/app --cov-fail-under=70
```

### **Parallel Execution**

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run in parallel (auto-detect cores)
pytest -n auto

# Run on 4 cores
pytest -n 4
```

---

## 💡 **BEST PRACTICES**

### **Test Independence**

✅ **DO:**
- Each test should be independent
- Tests should not depend on execution order
- Clean up after each test

❌ **DON'T:**
- Share mutable state between tests
- Rely on test execution order
- Leave test data behind

### **Test Speed**

✅ **DO:**
- Keep unit tests fast (< 100ms each)
- Use mocks for external dependencies
- Use in-memory databases

❌ **DON'T:**
- Call real external APIs
- Use slow operations in unit tests
- Create unnecessary test data

### **Test Clarity**

✅ **DO:**
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Test one thing per test
- Write clear assertions

❌ **DON'T:**
- Write vague test names
- Test multiple things in one test
- Use magic numbers without explanation

### **Test Coverage**

✅ **DO:**
- Test happy paths
- Test error conditions
- Test edge cases and boundaries
- Test security-critical code thoroughly

❌ **DON'T:**
- Chase 100% coverage blindly
- Test framework code
- Test trivial getters/setters

---

## 🎓 **ADVANCED TECHNIQUES**

### **Property-Based Testing**

```python
# Test properties that should always hold
def test_list_length_property():
    """Test adding item increases length."""
    original = [1, 2, 3]
    with_added = original + [4]
    assert len(with_added) == len(original) + 1
```

### **Mutation Testing**

```python
# Verify tests catch introduced bugs
# Use mutmut or similar tools
# pytest --mutate
```

### **Contract Testing**

```python
# Ensure API matches frontend expectations
def test_api_contract():
    """Test API response matches contract."""
    response = {"id": "uuid", "name": "str"}
    assert "id" in response
    assert "name" in response
```

### **Snapshot Testing**

```python
# Capture complex responses
def test_response_snapshot():
    """Test response matches snapshot."""
    # First run creates snapshot
    # Subsequent runs compare
    pass
```

---

## 📊 **TEST METRICS**

### **Current Statistics**

```
Total Tests:           1,033+
Pass Rate:             100%
Execution Time:        < 1 second
Test Speed:            1,300+ tests/second
Coverage:              ~80%
```

### **Quality Indicators**

- ✅ **Fast execution**: < 1 second full suite
- ✅ **High coverage**: 80% (target: 85%+)
- ✅ **No flaky tests**: 100% pass rate
- ✅ **Well organized**: Clear directory structure
- ✅ **Good documentation**: This guide!

---

## 🔧 **TROUBLESHOOTING**

### **Test Failures**

1. **Read error message carefully**
2. **Run single failing test**: `pytest path/to/test.py::test_name -v`
3. **Add debug output**: Use `-s` flag or `print()` statements
4. **Check test isolation**: Run test alone vs with others
5. **Verify test data**: Check fixtures and builders

### **Slow Tests**

1. **Identify slow tests**: `pytest --durations=10`
2. **Profile tests**: Use `pytest-profiling`
3. **Mock external calls**: Don't hit real APIs
4. **Use simpler test data**: Minimal data for test
5. **Parallelize**: Use `pytest -n auto`

### **Coverage Gaps**

1. **Run coverage**: `pytest --cov=src/app --cov-report=term-missing`
2. **Identify uncovered lines**: Check report
3. **Write tests**: Focus on critical paths first
4. **Don't chase 100%**: Focus on value

---

## 📚 **ADDITIONAL RESOURCES**

- **pytest documentation**: https://docs.pytest.org/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Test templates**: `tests/templates/`
- **Test fixtures**: `tests/fixtures/`
- **Test builders**: `tests/builders/`

---

## ✅ **CHECKLIST FOR NEW TESTS**

- [ ] Test follows AAA pattern
- [ ] Test has clear, descriptive name
- [ ] Test uses appropriate markers
- [ ] Test is independent and isolated
- [ ] Test uses builders/fixtures for data
- [ ] Test has clear assertions
- [ ] Test includes docstring
- [ ] Test runs fast (< 100ms for unit tests)
- [ ] Test passes consistently
- [ ] Test adds value to suite

---

**Last Updated**: December 2, 2025  
**Version**: 1.0  
**Coverage**: 80% (Target: 85%+)
