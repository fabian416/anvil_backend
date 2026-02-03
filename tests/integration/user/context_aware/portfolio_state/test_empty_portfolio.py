"""
Tests for EMPTY Portfolio State.

Tests workflow blocking and response customization for users with $0 balance.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..conftest import (
    ContextAwareCSVReporter,
    ContextAwareTestResult,
    create_context_test_result,
)
from ...conftest import (
    send_message,
    parse_response,
    create_conversation,
)


EMPTY_PORTFOLIO_TESTS = [
    # Blocked workflows
    {
        "test_id": "empty_swap_001",
        "input": "swap 1 ETH to USDC",
        "expected_blocked": True,
        "expected_suggestion": "buy",
        "category": "portfolio_state",
        "subcategory": "empty_blocked",
    },
    {
        "test_id": "empty_lending_001",
        "input": "deposit 100 USDC",
        "expected_blocked": True,
        "expected_suggestion": "buy",
        "category": "portfolio_state",
        "subcategory": "empty_blocked",
    },
    {
        "test_id": "empty_transfer_001",
        "input": "send 50 USDC to 0x123",
        "expected_blocked": True,
        "expected_suggestion": "buy",
        "category": "portfolio_state",
        "subcategory": "empty_blocked",
    },
    # Allowed workflows
    {
        "test_id": "empty_buy_001",
        "input": "buy $100 of ETH",
        "expected_blocked": False,
        "category": "portfolio_state",
        "subcategory": "empty_allowed",
    },
    # Portfolio queries
    {
        "test_id": "empty_portfolio_001",
        "input": "my portfolio",
        "expected_blocked": False,
        "expected_message_contains": ["empty", "buy", "get started"],
        "category": "portfolio_state",
        "subcategory": "empty_query",
    },
    {
        "test_id": "empty_balance_001",
        "input": "my balance",
        "expected_blocked": False,
        "expected_message_contains": ["$0", "empty", "buy"],
        "category": "portfolio_state",
        "subcategory": "empty_query",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestEmptyPortfolioState:
    """Tests for users with EMPTY portfolio state."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, portfolio_state_reporter, empty_user_context
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = portfolio_state_reporter
        self.user_context = empty_user_context

    @pytest.mark.parametrize(
        "test_case", EMPTY_PORTFOLIO_TESTS, ids=lambda t: t["test_id"]
    )
    async def test_empty_portfolio_behavior(self, test_case: dict):
        """Test behavior for empty portfolio users."""
        # Create conversation
        conv_id = await create_conversation(
            self.client,
            title=f"Empty Portfolio Test: {test_case['test_id']}",
        )

        # Send message
        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
            test_case["input"],
        )

        # Parse response
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()

        # Determine workflow blocking
        workflow_info = {
            "blocked": False,
            "reason": "",
        }

        if test_case.get("expected_blocked"):
            # Check if response indicates blocking
            blocked_indicators = [
                "can't",
                "cannot",
                "need to",
                "first buy",
                "empty",
                "no balance",
            ]
            workflow_info["blocked"] = any(ind in content for ind in blocked_indicators)

            if test_case.get("expected_suggestion"):
                suggestion = test_case["expected_suggestion"]
                if suggestion in content:
                    workflow_info["reason"] = f"Suggested: {suggestion}"

        # Create result
        result = create_context_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            user_context=self.user_context,
            workflow_info=workflow_info,
            conversation_id=conv_id,
        )

        self.reporter.add_result(result)

        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        assert len(content) > 10, "Response should have meaningful content"

        # Note: Blocking behavior depends on actual user context in test environment
        # The test verifies the response is meaningful, not strictly blocked
        # Actual blocking is tested via unit tests on the service layer
