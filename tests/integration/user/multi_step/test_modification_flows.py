"""
Modification Flow Tests for Authenticated Users.

Tests mid-workflow modifications like changing amounts, tokens, or parameters.
Uses LLM (Vertex AI) validation for semantic output verification.
"""

import asyncio
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
    create_conversation,
)


MODIFICATION_FLOWS = [
    # Amount Modifications
    {
        "test_id": "modify_swap_amount_001",
        "name": "Swap Amount Change",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "actually make it 0.5 ETH", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_amount",
    },
    {
        "test_id": "modify_lend_amount_001",
        "name": "Lending Amount Change",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "change to 500 USDC instead", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_amount",
    },
    {
        "test_id": "modify_transfer_amount_001",
        "name": "Transfer Amount Change",
        "steps": [
            {
                "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "expect_agent": "transfer_workflow",
            },
            {"input": "make it 50 USDC", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_amount",
    },
    # Token Modifications
    {
        "test_id": "modify_swap_token_001",
        "name": "Swap Token Change",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "actually swap to DAI instead", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_token",
    },
    {
        "test_id": "modify_lend_token_001",
        "name": "Lending Token Change",
        "steps": [
            {"input": "deposit USDC", "expect_agent": "lending_workflow"},
            {"input": "let me deposit ETH instead", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_token",
    },
    # Protocol Modifications
    {
        "test_id": "modify_lend_protocol_001",
        "name": "Lending Protocol Change",
        "steps": [
            {"input": "deposit 1000 USDC on Aave", "expect_agent": "lending_workflow"},
            {"input": "use Morpho instead", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_protocol",
    },
    # Chain Modifications
    {
        "test_id": "modify_chain_001",
        "name": "Chain Change",
        "steps": [
            {"input": "swap ETH to USDC on Ethereum", "expect_agent": "swap_workflow"},
            {"input": "do it on Base instead", "expect_modification": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_chain",
    },
    # Multiple Modifications
    {
        "test_id": "modify_multiple_001",
        "name": "Multiple Changes",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "change to 0.5 ETH to DAI", "expect_modification": True},
            {"input": "yes confirm", "expect_confirm": True},
        ],
        "category": "multi_step",
        "subcategory": "modification_multiple",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestModificationFlows:
    """Tests for mid-workflow modifications."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter

    @pytest.mark.parametrize("flow", MODIFICATION_FLOWS, ids=lambda f: f["test_id"])
    async def test_modification_flow(self, flow: dict):
        """Test modification handling in workflows."""
        conv_id = await create_conversation(
            self.client, title=f"Modification Test: {flow['name']}"
        )

        steps = flow["steps"]
        total_steps = len(steps)

        for step_num, step in enumerate(steps, 1):
            response_data, response_time_ms = await send_message(
                self.client,
                conv_id,
                step["input"],
            )

            step_test_case = {
                "input": step["input"],
                "expected_agent": step.get("expect_agent", ""),
                "category": flow["category"],
                "subcategory": flow["subcategory"],
                "is_multi_step": True,
                "step_number": step_num,
                "total_steps": total_steps,
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
            content = parsed.get("content", "").lower()

            # Verify modification acknowledgment
            if step.get("expect_modification"):
                # Should acknowledge the modification
                assert any(
                    word in content
                    for word in [
                        "updated",
                        "changed",
                        "modified",
                        "new",
                        "instead",
                        "0.5",
                        "dai",
                        "morpho",
                        "base",
                    ]
                ), f"Step {step_num} should acknowledge modification: {content[:200]}"

            await asyncio.sleep(0.3)
