"""
Buy Workflow Tests for Authenticated Users.

Tests fiat on-ramp flows for purchasing crypto.
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


BUY_TESTS = [
    # Basic Buys
    {
        "test_id": "buy_basic_001",
        "input": "buy $100 of ETH",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_basic",
    },
    {
        "test_id": "buy_basic_002",
        "input": "purchase 50 dollars of USDC",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_basic",
    },
    {
        "test_id": "buy_basic_003",
        "input": "buy BTC with card",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_basic",
    },
    {
        "test_id": "buy_basic_004",
        "input": "purchase ethereum",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_basic",
    },
    {
        "test_id": "buy_basic_005",
        "input": "buy $500 worth of bitcoin",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_basic",
    },
    
    # Generic Buys
    {
        "test_id": "buy_generic_001",
        "input": "buy crypto",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_generic",
    },
    {
        "test_id": "buy_generic_002",
        "input": "purchase cryptocurrency",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_generic",
    },
    {
        "test_id": "buy_generic_003",
        "input": "I want to buy crypto",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_generic",
    },
    
    # Edge Cases
    {
        "test_id": "buy_edge_001",
        "input": "buy",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_edge",
    },
    {
        "test_id": "buy_edge_002",
        "input": "how to buy ETH",
        "expected_agent": "buy_workflow",
        "category": "workflow",
        "subcategory": "buy_edge",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestBuyWorkflow:
    """Tests for Buy workflow agent with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", BUY_TESTS, ids=lambda t: t["test_id"])
    async def test_buy(self, test_case: dict):
        """Test buy workflow routing and response with LLM validation."""
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
                expected_behavior="Response should handle fiat-to-crypto purchase by showing payment options, amounts, or on-ramp providers.",
                additional_context={"test_category": "buy_workflow", "subcategory": test_case.get("subcategory", ""), "user_type": "authenticated"}
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
        
        # Verify buy-related response
        assert any(
            indicator in content or indicator in agents.lower()
            for indicator in ["buy", "purchase", "payment", "card", "$", "usd", "moonpay"]
        ), f"Buy query should return buy-related response: {content[:200]}"
