"""
Spanish Language Tests for Authenticated Users.

Tests all workflows with Spanish input.
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


SPANISH_TESTS = [
    # Swap
    {
        "test_id": "es_swap_001",
        "input": "quiero cambiar 50 USDC por ETH",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "spanish_swap",
        "language": "es",
    },
    {
        "test_id": "es_swap_002",
        "input": "intercambiar 1 ETH a USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "spanish_swap",
        "language": "es",
    },
    {
        "test_id": "es_swap_003",
        "input": "cambiar ethereum por usdc",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "spanish_swap",
        "language": "es",
    },
    # Lending
    {
        "test_id": "es_lend_001",
        "input": "depositar 1000 USDC en morpho",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "spanish_lending",
        "language": "es",
    },
    {
        "test_id": "es_lend_002",
        "input": "prestar ETH",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "spanish_lending",
        "language": "es",
    },
    {
        "test_id": "es_lend_003",
        "input": "ganar rendimiento con USDC",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "spanish_lending",
        "language": "es",
    },
    # Money Market
    {
        "test_id": "es_mm_001",
        "input": "comparar tasas de USDC",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "spanish_money_market",
        "language": "es",
    },
    {
        "test_id": "es_mm_002",
        "input": "mejores tasas para ETH",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "spanish_money_market",
        "language": "es",
    },
    {
        "test_id": "es_mm_003",
        "input": "donde depositar DAI",
        "expected_agent": "money_market_workflow",
        "category": "multilingual",
        "subcategory": "spanish_money_market",
        "language": "es",
    },
    # Transfer
    {
        "test_id": "es_transfer_001",
        "input": "enviar 50 USDC a 0x123456789abcdef0123456789abcdef012345678",
        "expected_agent": "transfer_workflow",
        "category": "multilingual",
        "subcategory": "spanish_transfer",
        "language": "es",
    },
    {
        "test_id": "es_transfer_002",
        "input": "transferir ETH",
        "expected_agent": "transfer_workflow",
        "category": "multilingual",
        "subcategory": "spanish_transfer",
        "language": "es",
    },
    # Buy
    {
        "test_id": "es_buy_001",
        "input": "comprar $200 de BTC",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "spanish_buy",
        "language": "es",
    },
    {
        "test_id": "es_buy_002",
        "input": "comprar ethereum con tarjeta",
        "expected_agent": "buy_workflow",
        "category": "multilingual",
        "subcategory": "spanish_buy",
        "language": "es",
    },
    # Price Queries
    {
        "test_id": "es_price_001",
        "input": "cual es el precio de bitcoin",
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "spanish_price",
        "language": "es",
    },
    {
        "test_id": "es_price_002",
        "input": "precio de ETH",
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "spanish_price",
        "language": "es",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestSpanish:
    """Tests for Spanish language support with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", SPANISH_TESTS, ids=lambda t: t["test_id"])
    async def test_spanish(self, test_case: dict):
        """Test Spanish language routing with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            language=test_case.get("language", "es"),
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
                expected_behavior=f"Response should handle Spanish query correctly and route to {test_case['expected_agent']}. Response can be in Spanish or English.",
                additional_context={
                    "test_category": "multilingual",
                    "subcategory": test_case.get("subcategory", ""),
                    "language": "es",
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
        agents = parsed.get("agents_used", "")

        # Verify correct agent routing
        expected = test_case["expected_agent"]
        assert expected in agents, f"Expected {expected} but got {agents}"
