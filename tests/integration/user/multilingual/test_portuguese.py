"""
Portuguese Language Tests for Authenticated Users.

Tests all workflows with Portuguese input.
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


PORTUGUESE_TESTS = [
    # Swap
    {
        "test_id": "pt_swap_001",
        "input": "trocar 1 ETH por USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_swap",
        "language": "pt",
    },
    {
        "test_id": "pt_swap_002",
        "input": "converter 100 USDC para ETH",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_swap",
        "language": "pt",
    },
    
    # Lending
    {
        "test_id": "pt_lend_001",
        "input": "depositar 500 USDC",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_lending",
        "language": "pt",
    },
    {
        "test_id": "pt_lend_002",
        "input": "emprestar ETH",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_lending",
        "language": "pt",
    },
    
    # Money Market
    {
        "test_id": "pt_mm_001",
        "input": "comparar taxas de USDC",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_money_market",
        "language": "pt",
    },
    {
        "test_id": "pt_mm_002",
        "input": "melhores taxas para ETH",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_money_market",
        "language": "pt",
    },
    {
        "test_id": "pt_mm_003",
        "input": "onde depositar DAI",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_money_market",
        "language": "pt",
    },
    
    # Buy
    {
        "test_id": "pt_buy_001",
        "input": "comprar $100 de ETH",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_buy",
        "language": "pt",
    },
    {
        "test_id": "pt_buy_002",
        "input": "comprar bitcoin com cartao",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "portuguese_buy",
        "language": "pt",
    },
    
    # Price
    {
        "test_id": "pt_price_001",
        "input": "qual o preco do bitcoin",
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "portuguese_price",
        "language": "pt",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestPortuguese:
    """Tests for Portuguese language support with LLM validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator
    
    @pytest.mark.parametrize("test_case", PORTUGUESE_TESTS, ids=lambda t: t["test_id"])
    async def test_portuguese(self, test_case: dict):
        """Test Portuguese language routing with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            language=test_case.get("language", "pt"),
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
                expected_behavior=f"Response should handle Portuguese query correctly and route to {test_case['expected_agent']}. Response can be in Portuguese or English.",
                additional_context={"test_category": "multilingual", "subcategory": test_case.get("subcategory", ""), "language": "pt", "user_type": "authenticated"}
            )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            llm_validation=llm_validation,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )
        
        self.reporter.add_result(result)
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
