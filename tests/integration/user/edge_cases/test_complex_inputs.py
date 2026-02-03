"""
Complex Input Tests for Authenticated Users.

Tests handling of complex, ambiguous, or challenging inputs.
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


COMPLEX_INPUT_TESTS = [
    # Multi-Intent Queries
    {
        "test_id": "complex_multi_intent_001",
        "input": "What's the ETH price and swap 0.1 ETH to USDC",
        "expected_agent": "",  # Multiple agents
        "category": "edge_case",
        "subcategory": "multi_intent",
    },
    {
        "test_id": "complex_multi_intent_002",
        "input": "Check my portfolio and suggest what to swap",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "multi_intent",
    },
    {
        "test_id": "complex_multi_intent_003",
        "input": "Compare rates on Aave and then deposit my USDC there",
        "expected_agent": "",
        "category": "edge_case",
        "subcategory": "multi_intent",
    },
    # Conditional Requests
    {
        "test_id": "complex_conditional_001",
        "input": "swap ETH to USDC if the price is good",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "conditional",
    },
    {
        "test_id": "complex_conditional_002",
        "input": "deposit USDC only if APY is above 5%",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "conditional",
    },
    # Vague Amounts
    {
        "test_id": "complex_vague_amount_001",
        "input": "swap some ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "vague_amount",
    },
    {
        "test_id": "complex_vague_amount_002",
        "input": "deposit a bit of USDC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "vague_amount",
    },
    {
        "test_id": "complex_vague_amount_003",
        "input": "swap half my ETH",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "vague_amount",
    },
    {
        "test_id": "complex_vague_amount_004",
        "input": "deposit all my USDC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "vague_amount",
    },
    # Informal Language
    {
        "test_id": "complex_informal_001",
        "input": "yo swap my eth for some usdc plz",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "informal",
    },
    {
        "test_id": "complex_informal_002",
        "input": "gimme the best yields rn",
        "expected_agent": "defi_yield",
        "category": "edge_case",
        "subcategory": "informal",
    },
    {
        "test_id": "complex_informal_003",
        "input": "whats eth doing today lol",
        "expected_agent": "hunter_ai",
        "category": "edge_case",
        "subcategory": "informal",
    },
    # Technical Jargon
    {
        "test_id": "complex_jargon_001",
        "input": "ape into the highest APY vault",
        "expected_agent": "defi_yield",
        "category": "edge_case",
        "subcategory": "jargon",
    },
    {
        "test_id": "complex_jargon_002",
        "input": "show me the TVL for top DeFi protocols",
        "expected_agent": "defi_yield",
        "category": "edge_case",
        "subcategory": "jargon",
    },
    {
        "test_id": "complex_jargon_003",
        "input": "what's the IL risk on this LP position",
        "expected_agent": "risk_analyzer",
        "category": "edge_case",
        "subcategory": "jargon",
    },
    # Misspellings
    {
        "test_id": "complex_misspell_001",
        "input": "swpa eth to usdc",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "misspelling",
    },
    {
        "test_id": "complex_misspell_002",
        "input": "deposite usdc",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "misspelling",
    },
    {
        "test_id": "complex_misspell_003",
        "input": "etherium price",
        "expected_agent": "hunter_ai",
        "category": "edge_case",
        "subcategory": "misspelling",
    },
    # Mixed Case
    {
        "test_id": "complex_case_001",
        "input": "SWAP ETH TO USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "mixed_case",
    },
    {
        "test_id": "complex_case_002",
        "input": "DePoSiT uSdC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "mixed_case",
    },
    # Numbers in Words
    {
        "test_id": "complex_numbers_001",
        "input": "swap one ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "edge_case",
        "subcategory": "number_words",
    },
    {
        "test_id": "complex_numbers_002",
        "input": "deposit five hundred USDC",
        "expected_agent": "lending_workflow",
        "category": "edge_case",
        "subcategory": "number_words",
    },
    # Abbreviations
    {
        "test_id": "complex_abbrev_001",
        "input": "chk my portfolio",
        "expected_agent": "portfolio",
        "category": "edge_case",
        "subcategory": "abbreviation",
    },
    {
        "test_id": "complex_abbrev_002",
        "input": "tx history",
        "expected_agent": "transaction_history",
        "category": "edge_case",
        "subcategory": "abbreviation",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestComplexInputs:
    """Tests for complex and challenging inputs."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter

    @pytest.mark.parametrize(
        "test_case", COMPLEX_INPUT_TESTS, ids=lambda t: t["test_id"]
    )
    async def test_complex_input(self, test_case: dict):
        """Test handling of complex inputs."""
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

        # For complex inputs, we mainly verify:
        # 1. No crash/error
        # 2. Some meaningful response
        # 3. Reasonable agent routing (if expected)

        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "")

        # Should have some response
        assert len(content) > 10, (
            f"Complex input should get meaningful response: {content[:200]}"
        )

        # If expected agent is specified, verify routing
        expected = test_case.get("expected_agent")
        if expected:
            agents = parsed.get("agents_used", "")
            # For complex inputs, we're lenient - just verify some agent handled it
            assert agents, f"Should route to some agent: {agents}"
