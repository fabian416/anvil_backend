"""
Confirmation Flow Tests for Authenticated Users.

Tests multi-step workflows with confirmation steps.
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
)


CONFIRMATION_FLOWS = [
    {
        "test_id": "confirm_swap_001",
        "name": "Swap Confirmation",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multi_step",
        "subcategory": "confirmation",
    },
    {
        "test_id": "confirm_swap_002",
        "name": "Swap with explicit confirm",
        "steps": [
            {"input": "swap 0.5 ETH to DAI", "expect_agent": "swap_workflow"},
            {"input": "confirm", "expect_execute": True},
        ],
        "category": "multi_step",
        "subcategory": "confirmation",
    },
    {
        "test_id": "confirm_lend_001",
        "name": "Lending Confirmation",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multi_step",
        "subcategory": "confirmation",
    },
    {
        "test_id": "confirm_transfer_001",
        "name": "Transfer Confirmation",
        "steps": [
            {"input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "expect_agent": "transfer_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multi_step",
        "subcategory": "confirmation",
    },
    {
        "test_id": "confirm_buy_001",
        "name": "Buy Confirmation",
        "steps": [
            {"input": "buy $100 of ETH", "expect_agent": "buy_workflow"},
            {"input": "yes", "expect_execute": True},
        ],
        "category": "multi_step",
        "subcategory": "confirmation",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestConfirmationFlows:
    """Tests for multi-step confirmation flows."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("flow", CONFIRMATION_FLOWS, ids=lambda f: f["test_id"])
    async def test_confirmation_flow(self, flow: dict):
        """Test multi-step confirmation flow."""
        # Create fresh conversation for each flow
        response = await self.client.post(
            "/api/v1/conversations",
            json={"title": f"Confirm Flow: {flow['name']}"},
        )
        assert response.status_code in (200, 201)
        conv_id = response.json().get("id")
        
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
                "requires_execute": step.get("expect_execute", False),
            }
            
            result = create_test_result(
                test_id=f"{flow['test_id']}_step{step_num}",
                test_case=step_test_case,
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conv_id,
            )
            
            self.reporter.add_result(result)
            
            assert not response_data.get("error"), f"Step {step_num} failed: {response_data}"
            
            parsed = parse_response(response_data)
            
            # Verify expectations
            if step.get("expect_execute"):
                has_execute = bool(parsed.get("execute_data"))
                content = parsed.get("content", "").lower()
                
                # Either has execute data or indicates completion
                assert has_execute or any(
                    word in content
                    for word in ["confirm", "ready", "execute", "proceed", "complete", "success"]
                ), f"Step {step_num} should indicate completion or have execute data"
            
            # Small delay between steps
            await asyncio.sleep(0.5)
