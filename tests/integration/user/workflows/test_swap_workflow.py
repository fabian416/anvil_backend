"""
Swap Workflow Tests for Authenticated Users.

Tests same-chain swaps, cross-chain swaps, and swap quotes.
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


SWAP_TESTS = [
    # Basic Swaps
    {
        "test_id": "swap_basic_001",
        "input": "swap 1 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_basic",
    },
    {
        "test_id": "swap_basic_002",
        "input": "exchange 100 USDC for ETH",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_basic",
    },
    {
        "test_id": "swap_basic_003",
        "input": "convert 0.5 ETH to DAI",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_basic",
    },
    {
        "test_id": "swap_basic_004",
        "input": "swap 500 USDC to WBTC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_basic",
    },
    {
        "test_id": "swap_basic_005",
        "input": "trade 1000 USDT for USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_basic",
    },
    # Swap Quotes
    {
        "test_id": "swap_quote_001",
        "input": "get quote for 1 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_quote",
    },
    {
        "test_id": "swap_quote_002",
        "input": "how much USDC for 1 ETH",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_quote",
    },
    {
        "test_id": "swap_quote_003",
        "input": "best rate ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_quote",
    },
    # Cross-Chain Swaps
    {
        "test_id": "swap_cross_001",
        "input": "swap ETH from Ethereum to Base",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_cross_chain",
    },
    {
        "test_id": "swap_cross_002",
        "input": "bridge USDC from Arbitrum to Ethereum",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_cross_chain",
    },
    {
        "test_id": "swap_cross_003",
        "input": "transfer ETH to polygon",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_cross_chain",
    },
    # Edge Cases
    {
        "test_id": "swap_edge_001",
        "input": "swap ETH",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_edge",
    },
    {
        "test_id": "swap_edge_002",
        "input": "swap",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "swap_edge",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestSwapWorkflow:
    """Tests for Swap workflow agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", SWAP_TESTS, ids=lambda t: t["test_id"])
    async def test_swap(self, test_case: dict):
        """Test swap workflow routing and response with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )

        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            expected_behavior = self._get_expected_behavior(test_case)

            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior=expected_behavior,
                additional_context={
                    "test_category": "swap_workflow",
                    "subcategory": test_case.get("subcategory", ""),
                    "user_type": "authenticated",
                },
            )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
            llm_validation=llm_validation,
        )

        self.reporter.add_result(result)

        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        agents = parsed.get("agents_used", "")

        # Verify swap-related response
        assert any(
            indicator in content or indicator in agents.lower()
            for indicator in ["swap", "exchange", "convert", "quote", "rate", "→", "to"]
        ), f"Swap query should return swap-related response: {content[:200]}"

    def _get_expected_behavior(self, test_case: dict) -> str:
        """Get expected behavior description for LLM validation."""
        subcategory = test_case.get("subcategory", "")

        behaviors = {
            "swap_basic": "Response should present swap details including tokens, amounts, and estimated output. Should ask for confirmation or provide quote.",
            "swap_quote": "Response should provide quote/rate for the swap with expected output amount and any fees.",
            "swap_cross_chain": "Response should handle cross-chain/bridge operation with source and destination chains clearly stated.",
            "swap_edge": "Response should handle incomplete swap request by asking for missing information or providing guidance.",
        }

        return behaviors.get(
            subcategory, "Response should be relevant to swap/exchange operations."
        )

    async def test_swap_with_confirmation(self, authenticated_client, csv_reporter):
        """Test complete swap flow with confirmation."""
        # Create fresh conversation
        response = await authenticated_client.post(
            "/api/v1/conversations",
            json={"title": "Swap Confirmation Test"},
        )
        assert response.status_code in (200, 201)
        conv_id = response.json().get("id")

        # Step 1: Request swap
        response_data, time1 = await send_message(
            authenticated_client,
            conv_id,
            "swap 1 ETH to USDC",
        )

        result1 = create_test_result(
            test_id="swap_confirm_step1",
            test_case={
                "input": "swap 1 ETH to USDC",
                "expected_agent": "swap_workflow",
                "category": "workflow",
                "subcategory": "swap_confirm",
                "is_multi_step": True,
                "step_number": 1,
                "total_steps": 2,
            },
            response_data=response_data,
            response_time_ms=time1,
            conversation_id=conv_id,
        )
        csv_reporter.add_result(result1)

        assert not response_data.get("error")

        # Step 2: Confirm
        response_data, time2 = await send_message(
            authenticated_client,
            conv_id,
            "yes",
        )

        result2 = create_test_result(
            test_id="swap_confirm_step2",
            test_case={
                "input": "yes",
                "expected_agent": "swap_workflow",
                "category": "workflow",
                "subcategory": "swap_confirm",
                "is_multi_step": True,
                "step_number": 2,
                "total_steps": 2,
                "requires_execute": True,
            },
            response_data=response_data,
            response_time_ms=time2,
            conversation_id=conv_id,
        )
        csv_reporter.add_result(result2)

        # Confirmation should provide execute data or completion message
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        has_execute = bool(parsed.get("execute_data"))

        assert has_execute or any(
            word in content
            for word in ["confirm", "ready", "execute", "proceed", "complete"]
        ), "Confirmation should provide execute data or completion"
