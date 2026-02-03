"""
ULTRA Agent Tests for Authenticated Users.

Tests arbitrage detection, flash loans, MEV protection, and auto executor.
Uses LLM (Vertex AI) validation for semantic output verification.

Migrated from: tests/integration/user/test_user_ultra_advanced.py
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
    create_conversation,
)


ULTRA_TESTS = [
    # Flash Loans (from shortcuts.md patterns)
    {
        "test_id": "ultra_flash_001",
        "input": "flash loan 100 ETH",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_flash_loan",
    },
    {
        "test_id": "ultra_flash_002",
        "input": "flash loan info for USDC",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_flash_loan",
    },
    {
        "test_id": "ultra_flash_003",
        "input": "borrow 50000 USDC",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_flash_loan",
    },
    {
        "test_id": "ultra_flash_004",
        "input": "best flash loan rate for DAI",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_flash_loan",
    },
    # Arbitrage Discovery (from shortcuts.md patterns)
    {
        "test_id": "ultra_arb_001",
        "input": "find arbitrage opportunities",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_arbitrage",
    },
    {
        "test_id": "ultra_arb_002",
        "input": "arbitrage for ETH",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_arbitrage",
    },
    {
        "test_id": "ultra_arb_003",
        "input": "scan for arbitrage with $10000",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_arbitrage",
    },
    {
        "test_id": "ultra_arb_004",
        "input": "find profitable trades",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_arbitrage",
    },
    # MEV Protection (from shortcuts.md patterns)
    {
        "test_id": "ultra_mev_001",
        "input": "check mev protection",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_mev",
    },
    {
        "test_id": "ultra_mev_002",
        "input": "flashbots status",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_mev",
    },
    {
        "test_id": "ultra_mev_003",
        "input": "protect my trade",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_mev",
    },
    {
        "test_id": "ultra_mev_004",
        "input": "enable sandwich protection",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_mev",
    },
    # Auto Executor (from shortcuts.md patterns)
    {
        "test_id": "ultra_exec_001",
        "input": "auto executor status",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_executor",
    },
    {
        "test_id": "ultra_exec_002",
        "input": "check trading bot",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_executor",
    },
    {
        "test_id": "ultra_exec_003",
        "input": "arbitrage bot metrics",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_executor",
    },
    # Multi-Language: Spanish
    {
        "test_id": "ultra_es_001",
        "input": "buscar oportunidades de arbitraje",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_spanish",
    },
    {
        "test_id": "ultra_es_002",
        "input": "verificar protección MEV",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_spanish",
    },
    # Multi-Language: Portuguese
    {
        "test_id": "ultra_pt_001",
        "input": "encontrar oportunidades de arbitragem",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_portuguese",
    },
    # Multi-Language: Chinese
    {
        "test_id": "ultra_zh_001",
        "input": "寻找套利机会",
        "expected_agent": "ultra",
        "category": "agent",
        "subcategory": "ultra_chinese",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestUltraAgent:
    """Tests for ULTRA arbitrage bot agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter, llm_validator):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", ULTRA_TESTS, ids=lambda t: t["test_id"])
    async def test_ultra(self, test_case: dict):
        """Test ULTRA agent queries with LLM validation."""
        conv_id = await create_conversation(
            self.client, title=f"ULTRA Test: {test_case['test_id']}"
        )

        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
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
                    "test_category": "ultra",
                    "subcategory": test_case.get("subcategory", ""),
                    "user_type": "authenticated",
                },
            )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=conv_id,
            llm_validation=llm_validation,
        )

        self.reporter.add_result(result)

        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "")

        # ULTRA responses should be substantive
        assert len(content) > 50, f"ULTRA response too short: {content[:200]}"

    def _get_expected_behavior(self, test_case: dict) -> str:
        """Get expected behavior description for LLM validation."""
        subcategory = test_case.get("subcategory", "")

        behaviors = {
            "ultra_flash_loan": "Response should explain flash loan mechanics, arbitrage opportunities, and associated risks clearly.",
            "ultra_mev": "Response should explain MEV protection strategies including Flashbots, private transactions, and practical steps.",
            "ultra_arbitrage": "Response should explain arbitrage discovery across DEXes with potential paths and profit opportunities.",
            "ultra_executor": "Response should explain auto-execution capabilities for automated trading strategies.",
        }

        return behaviors.get(
            subcategory,
            "Response should be relevant to advanced DeFi trading strategies.",
        )
