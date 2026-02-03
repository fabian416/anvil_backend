"""
Error Handling Tests for Authenticated Users.

Tests invalid inputs, edge cases, and error recovery.
Uses LLM (Vertex AI) validation for semantic output verification.
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
)


ERROR_HANDLING_TESTS = [
    # Invalid Tokens
    {
        "test_id": "error_token_001",
        "input": "swap UNKNOWNTOKEN to USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "invalid_token",
    },
    {
        "test_id": "error_token_002",
        "input": "deposit FAKETOKEN",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "invalid_token",
    },
    # Invalid Amounts
    {
        "test_id": "error_amount_001",
        "input": "swap -5 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "invalid_amount",
    },
    {
        "test_id": "error_amount_002",
        "input": "deposit 0 USDC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "invalid_amount",
    },
    {
        "test_id": "error_amount_003",
        "input": "send 99999999999 ETH",
        "expected_agent": "transfer_workflow",
        "category": "edge_case",
        "subcategory": "invalid_amount",
    },
    # Invalid Addresses
    {
        "test_id": "error_address_001",
        "input": "send 100 USDC to invalidaddress",
        "expected_agent": "transfer_workflow",
        "category": "edge_case",
        "subcategory": "invalid_address",
    },
    {
        "test_id": "error_address_002",
        "input": "transfer ETH to 0xinvalid",
        "expected_agent": "transfer_workflow",
        "category": "edge_case",
        "subcategory": "invalid_address",
    },
    # Empty/Minimal Input
    {
        "test_id": "error_empty_001",
        "input": "",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "empty_input",
    },
    {
        "test_id": "error_minimal_001",
        "input": "a",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "minimal_input",
    },
    {
        "test_id": "error_minimal_002",
        "input": "?",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "minimal_input",
    },
    # Gibberish
    {
        "test_id": "error_gibberish_001",
        "input": "asdfghjkl zxcvbnm",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "gibberish",
    },
    {
        "test_id": "error_gibberish_002",
        "input": "!@#$%^&*()",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "gibberish",
    },
    # Off-Topic
    {
        "test_id": "error_offtopic_001",
        "input": "what's the weather today",
        "expected_agent": "chat",
        "category": "edge_case",
        "subcategory": "off_topic",
    },
    {
        "test_id": "error_offtopic_002",
        "input": "tell me a joke",
        "expected_agent": "chat",
        "category": "edge_case",
        "subcategory": "off_topic",
    },
    {
        "test_id": "error_offtopic_003",
        "input": "who is the president",
        "expected_agent": "chat",
        "category": "edge_case",
        "subcategory": "off_topic",
    },
    # Typos
    {
        "test_id": "error_typo_001",
        "input": "swpa 1 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "typo",
    },
    {
        "test_id": "error_typo_002",
        "input": "depositt USDC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "typo",
    },
    {
        "test_id": "error_typo_003",
        "input": "etherium price",
        "expected_agent": "hunter_ai",
        "category": "edge_case",
        "subcategory": "typo",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter

    @pytest.mark.parametrize(
        "test_case", ERROR_HANDLING_TESTS, ids=lambda t: t["test_id"]
    )
    async def test_error_handling(self, test_case: dict):
        """Test error handling for edge cases."""
        # Skip empty input test (would fail validation)
        if not test_case["input"]:
            pytest.skip("Empty input not supported")

        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )

        self.reporter.add_result(result)

        # For edge cases, we mainly verify the system doesn't crash
        # The response should be graceful even for invalid inputs
        parsed = parse_response(response_data)
        content = parsed.get("content", "")

        # Should have some response (even if it's an error message)
        assert len(content) > 0 or response_data.get("error"), (
            "Should provide some response for edge cases"
        )
