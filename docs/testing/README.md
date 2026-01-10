# Testing Documentation

**Purpose**: Comprehensive testing documentation and guides
**Audience**: Developers, QA Engineers, CI/CD Engineers

---

## 📚 Testing Documentation

### Test Architecture & Strategy
- **[Testing Architecture Analysis](./TESTING_ARCHITECTURE_ANALYSIS.md)** - Complete analysis of testing approach
- **[Testing Pyramid](./TESTING_PYRAMID.md)** - Test pyramid design and implementation
- **[Component Testing Design](./COMPONENT_TESTING_DESIGN.md)** - Component-level testing strategy

### Integration Tests
- **[Multi-Step Flow Tests](./multi-step-flows/README.md)** - Multi-step conversation flow tests for shortcuts
  - 60 comprehensive tests (14 multi-step + 46 edge cases)
  - Guest and authenticated user coverage
  - Full CTO.md framework analysis
  - Test execution results and performance metrics

### Test Fixes & Maintenance
- **[Test Fixes README](./TEST_FIXES_README.md)** - Guide to fixing common test issues
- **[Test Fixes Session Summary](./TEST_FIXES_SESSION_SUMMARY.md)** - Historical test fix summaries

### Testing Guides
See [`guides/`](./guides/) subfolder for additional testing guides.

---

## 🚀 Quick Start

### Run All Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/integration/
pytest tests/unit/
```

### Run Shortcuts Multi-Step Tests
```bash
# All multi-step flow tests
pytest tests/integration/chat/test_multi_step_flows.py -v

# All edge case tests
pytest tests/integration/chat/test_shortcuts_edge_cases.py -v

# See multi-step-flows/README.md for more commands
```

---

## 📖 Related Documentation

See [Main Documentation Index](../README.md) for complete documentation.

---

**Last Updated**: January 10, 2026
