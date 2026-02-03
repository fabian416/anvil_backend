"""
Money Market Workflow Tests for Authenticated Users.

Tests rate comparisons across Aave, Compound, and Morpho.
Uses LLM (Vertex AI) validation for semantic output verification.

Migrated from: tests/integration/user/workflows/test_money_market_workflow.py
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ...conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    validate_with_llm,
)


MONEY_MARKET_TESTS = [
    # Rate Comparisons
    {
        "test_id": "mm_compare_001",
        "input": "compare USDC rates",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    {
        "test_id": "mm_compare_002",
        "input": "best lending rates for ETH",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    {
        "test_id": "mm_compare_003",
        "input": "where should I deposit DAI",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    {
        "test_id": "mm_compare_004",
        "input": "compare aave compound morpho",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    {
        "test_id": "mm_compare_005",
        "input": "USDC APY comparison",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    {
        "test_id": "mm_compare_006",
        "input": "best deposit rates",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_compare",
    },
    # Protocol-Specific Queries
    {
        "test_id": "mm_protocol_001",
        "input": "aave vs compound for USDC",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_protocol",
    },
    {
        "test_id": "mm_protocol_002",
        "input": "morpho rates",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_protocol",
    },
    {
        "test_id": "mm_protocol_003",
        "input": "aave ETH supply rate",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_protocol",
    },
    # Asset-Specific
    {
        "test_id": "mm_asset_001",
        "input": "stablecoin lending rates",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_asset",
    },
    {
        "test_id": "mm_asset_002",
        "input": "ETH deposit APY",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_asset",
    },
    {
        "test_id": "mm_asset_003",
        "input": "WBTC lending options",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "money_market_asset",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestMoneyMarketWorkflow:
    """Tests for Money Market workflow agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize(
        "test_case", MONEY_MARKET_TESTS, ids=lambda t: t["test_id"]
    )
    async def test_money_market(self, test_case: dict):
        """Test money market workflow routing and response with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )

        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior="Response should compare lending rates across protocols (Aave, Compound, Morpho) with APY percentages.",
                additional_context={
                    "test_category": "money_market_workflow",
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

        # Verify money market response contains rate data
        assert any(
            indicator in content or indicator in agents.lower()
            for indicator in [
                "rate",
                "apy",
                "%",
                "compare",
                "aave",
                "compound",
                "morpho",
                "money_market",
            ]
        ), f"Money market query should return rate comparison: {content[:200]}"

    async def test_money_market_then_deposit(self, authenticated_client, csv_reporter):
        """Test complete money market flow: compare then deposit."""
        # Create fresh conversation
        response = await authenticated_client.post(
            "/api/v1/conversations",
            json={"title": "Money Market Flow Test"},
        )
        assert response.status_code in (200, 201)
        conv_id = response.json().get("id")

        # Step 1: Compare rates
        response_data, time1 = await send_message(
            authenticated_client,
            conv_id,
            "compare USDC rates",
        )

        result1 = create_test_result(
            test_id="mm_flow_step1",
            test_case={
                "input": "compare USDC rates",
                "expected_agent": "money_market_workflow",
                "category": "workflow",
                "subcategory": "money_market_flow",
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

        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()

        # Should show rate comparison
        assert any(proto in content for proto in ["aave", "compound", "morpho", "%"]), (
            "Should show protocol rates"
        )

        # Step 2: Select protocol
        response_data, time2 = await send_message(
            authenticated_client,
            conv_id,
            "morpho",
        )

        result2 = create_test_result(
            test_id="mm_flow_step2",
            test_case={
                "input": "morpho",
                "expected_agent": "money_market_workflow",
                "category": "workflow",
                "subcategory": "money_market_flow",
                "is_multi_step": True,
                "step_number": 2,
                "total_steps": 2,
            },
            response_data=response_data,
            response_time_ms=time2,
            conversation_id=conv_id,
        )
        csv_reporter.add_result(result2)
