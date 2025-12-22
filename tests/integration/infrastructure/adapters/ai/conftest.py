"""
Pytest configuration for LLM provider adapter tests.

Provides fixtures and markers for integration testing.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require API keys)"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests (no API keys)")


@pytest.fixture(scope="session")
def openai_api_key():
    """Get OpenAI API key from environment."""
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return api_key


@pytest.fixture(scope="session")
def anthropic_api_key():
    """Get Anthropic API key from environment."""
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return api_key
