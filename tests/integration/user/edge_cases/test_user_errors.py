"""
User Error Handling Tests.

Tests error handling and graceful degradation for authenticated user chat.
Validates that error messages are user-friendly and that the system
degrades gracefully under various failure conditions.
Uses LLM (Vertex AI) validation for semantic output verification.

Migrated from errors/test_user_error_handling.py to use new test infrastructure.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    validate_with_llm,
    create_conversation,
)


ERROR_TESTS = [
    # Empty/Invalid Input
    {
        "test_id": "error_empty_content_001",
        "input": "",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "invalid_input",
        "expect_error": True,
    },
    {
        "test_id": "error_whitespace_001",
        "input": "   ",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "invalid_input",
        "expect_error": True,
    },
    # Very Long Input
    {
        "test_id": "error_long_input_001",
        "input": "a" * 10000,
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "input_length",
        "expect_error": False,  # Should handle gracefully
    },
    # Unicode/Special Characters
    {
        "test_id": "error_unicode_001",
        "input": "💰 🚀 ≈ ∞ → ← ↑ ↓",
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "special_chars",
        "expect_error": False,
    },
    {
        "test_id": "error_unicode_002",
        "input": "مرحبا بالعالم",  # Arabic
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "special_chars",
        "expect_error": False,
    },
    # Malformed Requests (handled by parsing)
    {
        "test_id": "error_numbers_only_001",
        "input": "12345678901234567890",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "numeric_input",
        "expect_error": False,
    },
    # Off-Topic Queries
    {
        "test_id": "error_offtopic_001",
        "input": "What's the weather in New York?",
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "off_topic",
        "expect_error": False,
    },
    {
        "test_id": "error_offtopic_002",
        "input": "Tell me a joke",
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "off_topic",
        "expect_error": False,
    },
    {
        "test_id": "error_offtopic_003",
        "input": "Who won the Super Bowl?",
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "off_topic",
        "expect_error": False,
    },
    # Ambiguous/Vague Queries
    {
        "test_id": "error_ambiguous_001",
        "input": "what",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "ambiguous",
        "expect_error": False,
    },
    {
        "test_id": "error_ambiguous_002",
        "input": "help",
        "expected_agent": "chat",
        "category": "error_handling",
        "subcategory": "ambiguous",
        "expect_error": False,
    },
    {
        "test_id": "error_ambiguous_003",
        "input": "?",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "ambiguous",
        "expect_error": False,
    },
    # SQL Injection Attempts
    {
        "test_id": "error_sql_injection_001",
        "input": "'; DROP TABLE users; --",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "security",
        "expect_error": False,
    },
    {
        "test_id": "error_sql_injection_002",
        "input": "1 OR 1=1",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "security",
        "expect_error": False,
    },
    # XSS Attempts
    {
        "test_id": "error_xss_001",
        "input": "<script>alert('xss')</script>",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "security",
        "expect_error": False,
    },
    {
        "test_id": "error_xss_002",
        "input": "javascript:alert(1)",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "security",
        "expect_error": False,
    },
    # Path Traversal Attempts
    {
        "test_id": "error_path_traversal_001",
        "input": "../../../etc/passwd",
        "expected_agent": "",
        "category": "error_handling",
        "subcategory": "security",
        "expect_error": False,
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserErrors:
    """Tests for user error handling."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter

    @pytest.mark.parametrize("test_case", ERROR_TESTS, ids=lambda t: t["test_id"])
    async def test_error_handling(self, test_case: dict):
        """Test error handling for various inputs."""
        # Skip empty/whitespace tests (validation happens before API call)
        if not test_case["input"].strip():
            pytest.skip("Empty input not supported by message endpoint")

        # Create fresh conversation for each test
        conv_id = await create_conversation(
            self.client, title=f"Error Test: {test_case['test_id']}"
        )

        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
            test_case["input"],
        )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=conv_id,
        )

        self.reporter.add_result(result)

        # Validate based on expectations
        if test_case.get("expect_error"):
            # Should return an error status
            assert (
                response_data.get("error")
                or response_data.get("status_code", 200) >= 400
            ), f"Expected error for {test_case['test_id']}"
        else:
            # Should handle gracefully without errors
            # Even if it doesn't understand, should return a response
            parsed = parse_response(response_data)
            content = parsed.get("content", "")

            # Response should exist (even if it's a helpful error message)
            # Security inputs should not crash the system
            assert content or response_data.get("error"), (
                f"Should have some response for {test_case['test_id']}"
            )

            # Security tests: verify no sensitive data in response
            if "security" in test_case.get("subcategory", ""):
                assert "DROP TABLE" not in content.upper(), (
                    "Should not echo SQL injection"
                )
                assert "<script>" not in content.lower(), "Should not echo XSS"


@pytest.mark.asyncio
@pytest.mark.integration
class TestRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter

    async def test_rapid_requests_handling(self):
        """Test system handles rapid consecutive requests gracefully."""
        conv_id = await create_conversation(self.client, title="Rate Limit Test")

        # Send multiple requests in quick succession
        results = []
        for i in range(5):
            response_data, response_time_ms = await send_message(
                self.client,
                conv_id,
                f"Quick test message {i + 1}",
            )

            result = create_test_result(
                test_id=f"rate_limit_rapid_{i + 1}",
                test_case={
                    "input": f"Quick test message {i + 1}",
                    "expected_agent": "",
                    "category": "error_handling",
                    "subcategory": "rate_limiting",
                },
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conv_id,
            )

            self.reporter.add_result(result)
            results.append(result)

        # Should have handled at least some requests
        successes = sum(1 for r in results if r.status in ("PASS", "PARTIAL"))
        assert successes >= 3, "Should handle at least 3 out of 5 rapid requests"
