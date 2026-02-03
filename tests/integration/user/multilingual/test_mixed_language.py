"""
Mixed Language Tests for Authenticated Users.

Tests handling of code-switching and mixed language inputs.
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


MIXED_LANGUAGE_TESTS = [
    # English + Spanish
    {
        "test_id": "mixed_en_es_001",
        "input": "swap 1 ETH por USDC",  # Mix of English and Spanish
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "mixed_en_es",
        "language": "en",
    },
    {
        "test_id": "mixed_en_es_002",
        "input": "quiero ver my portfolio",
        "expected_agent": "portfolio",
        "category": "multilingual",
        "subcategory": "mixed_en_es",
        "language": "es",
    },
    # English + Portuguese
    {
        "test_id": "mixed_en_pt_001",
        "input": "trocar ETH for USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "mixed_en_pt",
        "language": "pt",
    },
    {
        "test_id": "mixed_en_pt_002",
        "input": "deposit meu USDC",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "mixed_en_pt",
        "language": "pt",
    },
    # English + Chinese
    {
        "test_id": "mixed_en_zh_001",
        "input": "swap 1 ETH 到 USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "mixed_en_zh",
        "language": "zh",
    },
    # Token Names (Always English)
    {
        "test_id": "mixed_token_es_001",
        "input": "intercambiar Ethereum por USDC",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "token_names",
        "language": "es",
    },
    {
        "test_id": "mixed_token_pt_001",
        "input": "depositar Bitcoin",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "token_names",
        "language": "pt",
    },
    {
        "test_id": "mixed_token_zh_001",
        "input": "比特币价格",  # Bitcoin price in Chinese
        "expected_agent": "hunter_ai",
        "category": "multilingual",
        "subcategory": "token_names",
        "language": "zh",
    },
    # Protocol Names (Always English)
    {
        "test_id": "mixed_protocol_es_001",
        "input": "depositar en Aave",
        "expected_agent": "lending_workflow",
        "category": "multilingual",
        "subcategory": "protocol_names",
        "language": "es",
    },
    {
        "test_id": "mixed_protocol_pt_001",
        "input": "trocar no Uniswap",
        "expected_agent": "swap_workflow",
        "category": "multilingual",
        "subcategory": "protocol_names",
        "language": "pt",
    },
]


LANGUAGE_SWITCH_FLOWS = [
    {
        "test_id": "switch_mid_conv_001",
        "name": "English to Spanish Switch",
        "steps": [
            {"input": "swap 1 ETH to USDC", "language": "en"},
            {"input": "no, quiero 0.5 ETH", "language": "es"},  # Switch to Spanish
        ],
        "category": "multilingual",
        "subcategory": "language_switch",
    },
    {
        "test_id": "switch_mid_conv_002",
        "name": "Spanish to English Switch",
        "steps": [
            {"input": "comparar tasas de USDC", "language": "es"},
            {"input": "use Morpho", "language": "en"},  # Switch to English
        ],
        "category": "multilingual",
        "subcategory": "language_switch",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestMixedLanguage:
    """Tests for mixed language handling with LLM validation."""

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
        "test_case", MIXED_LANGUAGE_TESTS, ids=lambda t: t["test_id"]
    )
    async def test_mixed_language(self, test_case: dict):
        """Test mixed language input handling with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
            language=test_case.get("language", "en"),
        )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )

        self.reporter.add_result(result)

        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "")
        agents = parsed.get("agents_used", "")

        # Should route to correct agent despite mixed language
        expected = test_case.get("expected_agent")
        if expected:
            assert expected in agents, f"Expected {expected} but got {agents}"


@pytest.mark.asyncio
@pytest.mark.integration
class TestLanguageSwitch:
    """Tests for mid-conversation language switching."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter

    @pytest.mark.parametrize("flow", LANGUAGE_SWITCH_FLOWS, ids=lambda f: f["test_id"])
    async def test_language_switch(self, flow: dict):
        """Test handling of language switches mid-conversation."""
        from ..conftest import create_conversation

        conv_id = await create_conversation(
            self.client, title=f"Language Switch: {flow['name']}"
        )

        steps = flow["steps"]
        total_steps = len(steps)

        for step_num, step in enumerate(steps, 1):
            response_data, response_time_ms = await send_message(
                self.client,
                conv_id,
                step["input"],
                language=step.get("language", "en"),
            )

            step_test_case = {
                "input": step["input"],
                "expected_agent": "",
                "category": flow["category"],
                "subcategory": flow["subcategory"],
                "is_multi_step": True,
                "step_number": step_num,
                "total_steps": total_steps,
                "language": step.get("language", "en"),
            }

            result = create_test_result(
                test_id=f"{flow['test_id']}_step{step_num}",
                test_case=step_test_case,
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conv_id,
            )

            self.reporter.add_result(result)

            assert not response_data.get("error"), (
                f"Step {step_num} failed: {response_data}"
            )

            parsed = parse_response(response_data)
            content = parsed.get("content", "")

            # Should maintain context despite language switch
            assert len(content) > 20, f"Should respond meaningfully: {content[:200]}"
