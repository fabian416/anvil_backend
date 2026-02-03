"""
DeFi Yield Agent Tests for Authenticated Users.

Tests yield queries, APY comparisons, and farming opportunities.
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


YIELD_TESTS = [
    {
        "test_id": "yield_001",
        "input": "best yield for USDC",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_002",
        "input": "highest APY stablecoins",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_003",
        "input": "yield farming opportunities",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_004",
        "input": "best ETH staking yield",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_005",
        "input": "top DeFi yields",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_006",
        "input": "where can I earn the most on DAI",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_007",
        "input": "compare stablecoin yields",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
    {
        "test_id": "yield_008",
        "input": "passive income crypto",
        "expected_agent": "defi_yield",
        "category": "agent",
        "subcategory": "yield",
    },
]


RISK_TESTS = [
    {
        "test_id": "risk_001",
        "input": "analyze risk of Aave",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
    },
    {
        "test_id": "risk_002",
        "input": "is Compound safe",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
    },
    {
        "test_id": "risk_003",
        "input": "Morpho protocol risks",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
    },
    {
        "test_id": "risk_004",
        "input": "risk assessment for Uniswap",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
    },
    {
        "test_id": "risk_005",
        "input": "how safe is this vault",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk",
    },
]


RESEARCH_TESTS = [
    {
        "test_id": "research_001",
        "input": "tell me about Aave protocol",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
    {
        "test_id": "research_002",
        "input": "what is Uniswap",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
    {
        "test_id": "research_003",
        "input": "explain DeFi lending",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
    {
        "test_id": "research_004",
        "input": "how does Compound work",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
    {
        "test_id": "research_005",
        "input": "what are liquidity pools",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
    {
        "test_id": "research_006",
        "input": "explain impermanent loss",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestDefiYield:
    """Tests for DeFi Yield agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", YIELD_TESTS, ids=lambda t: t["test_id"])
    async def test_yield(self, test_case: dict):
        """Test yield queries with LLM validation."""
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
                expected_behavior="Response should provide yield/APY information with rates, protocol names, and earning opportunities.",
                additional_context={
                    "test_category": "defi_yield",
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

        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()

        # Yield responses should mention APY or yield
        assert any(
            word in content
            for word in ["apy", "yield", "%", "earn", "rate", "interest"]
        ), f"Yield response should contain APY data: {content[:200]}"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestRiskAnalyzer:
    """Tests for Risk Analyzer agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", RISK_TESTS, ids=lambda t: t["test_id"])
    async def test_risk(self, test_case: dict):
        """Test risk analysis queries with LLM validation."""
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
                expected_behavior="Response should provide risk analysis including safety assessment, TVL, audit status, or potential vulnerabilities.",
                additional_context={
                    "test_category": "risk_analyzer",
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

        assert not response_data.get("error"), f"Request failed: {response_data}"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestResearch:
    """Tests for Research agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", RESEARCH_TESTS, ids=lambda t: t["test_id"])
    async def test_research(self, test_case: dict):
        """Test research queries with LLM validation."""
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
                expected_behavior="Response should provide educational/informative content about the requested DeFi topic or protocol.",
                additional_context={
                    "test_category": "research",
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

        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "")

        # Research responses should be informative
        assert len(content) > 50, f"Research response too short: {content[:200]}"
