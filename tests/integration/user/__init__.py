"""
User Integration Tests.

Comprehensive test suite for authenticated user workflows and agents.

Structure:
- agents/: Individual agent tests (hunter_ai, portfolio, etc.)
- workflows/: Multi-step workflow tests (swap, lending, etc.)
- multi_step/: Complex multi-turn conversation tests
- multilingual/: Language-specific tests (es, pt, zh)
- edge_cases/: Error handling and edge case tests

Usage:
    # Run all user tests
    JWT_TEST_TOKEN=<token> pytest tests/integration/user/ -v

    # Run specific category
    JWT_TEST_TOKEN=<token> pytest tests/integration/user/workflows/ -v

    # Run with CSV output
    JWT_TEST_TOKEN=<token> pytest tests/integration/user/ -v --tb=short
"""
