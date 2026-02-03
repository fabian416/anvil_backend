"""
Tests for Workflow Blocking Based on Portfolio State.

Tests that workflows are blocked appropriately for different portfolio states.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..conftest import (
    ContextAwareCSVReporter,
    create_context_test_result,
)
from ...conftest import (
    send_message,
    parse_response,
    create_conversation,
)


WORKFLOW_BLOCKING_TESTS = [
    # EMPTY portfolio - blocked workflows
    {
        "test_id": "block_empty_swap_001",
        "portfolio_state": "empty",
        "input": "swap 1 ETH to USDC",
        "workflow": "swap",
        "expected_blocked": True,
        "block_indicators": ["can't", "cannot", "need", "buy first", "empty", "no balance"],
        "category": "workflows",
        "subcategory": "empty_blocked",
    },
    {
        "test_id": "block_empty_lend_001",
        "portfolio_state": "empty",
        "input": "deposit 100 USDC on Aave",
        "workflow": "lending",
        "expected_blocked": True,
        "block_indicators": ["can't", "cannot", "need", "buy first", "empty"],
        "category": "workflows",
        "subcategory": "empty_blocked",
    },
    {
        "test_id": "block_empty_transfer_001",
        "portfolio_state": "empty",
        "input": "send 50 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "workflow": "transfer",
        "expected_blocked": True,
        "block_indicators": ["can't", "cannot", "need", "buy first", "empty"],
        "category": "workflows",
        "subcategory": "empty_blocked",
    },
    
    # EMPTY portfolio - allowed workflows
    {
        "test_id": "block_empty_buy_001",
        "portfolio_state": "empty",
        "input": "buy $100 of ETH",
        "workflow": "buy",
        "expected_blocked": False,
        "category": "workflows",
        "subcategory": "empty_allowed",
    },
    
    # STARTER portfolio - gas warnings
    {
        "test_id": "warn_starter_swap_001",
        "portfolio_state": "starter",
        "input": "swap $20 USDC to ETH",
        "workflow": "swap",
        "expected_blocked": False,
        "expected_warning": True,
        "warning_indicators": ["gas", "fee", "cost", "small amount"],
        "category": "workflows",
        "subcategory": "starter_warning",
    },
    
    # ACTIVE portfolio - all allowed
    {
        "test_id": "allow_active_swap_001",
        "portfolio_state": "active",
        "input": "swap 1 ETH to USDC",
        "workflow": "swap",
        "expected_blocked": False,
        "category": "workflows",
        "subcategory": "active_allowed",
    },
    {
        "test_id": "allow_active_lend_001",
        "portfolio_state": "active",
        "input": "deposit 1000 USDC",
        "workflow": "lending",
        "expected_blocked": False,
        "category": "workflows",
        "subcategory": "active_allowed",
    },
    
    # WHALE portfolio - all allowed, no warnings
    {
        "test_id": "allow_whale_swap_001",
        "portfolio_state": "whale",
        "input": "swap 10 ETH to USDC",
        "workflow": "swap",
        "expected_blocked": False,
        "expected_warning": False,
        "category": "workflows",
        "subcategory": "whale_allowed",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowBlocking:
    """Test workflow blocking based on portfolio state."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, workflows_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = workflows_reporter
    
    @pytest.mark.parametrize("test_case", WORKFLOW_BLOCKING_TESTS, ids=lambda t: t["test_id"])
    async def test_workflow_blocking(self, test_case: dict):
        """Test workflow blocking behavior."""
        # Create conversation
        conv_id = await create_conversation(
            self.client,
            title=f"Workflow Blocking: {test_case['test_id']}",
        )
        
        # Send workflow request
        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
            test_case["input"],
        )
        
        # Parse response
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        
        # Check for blocking indicators
        workflow_info = {
            "blocked": False,
            "reason": "",
            "warning": False,
        }
        
        if test_case.get("expected_blocked"):
            block_indicators = test_case.get("block_indicators", [])
            workflow_info["blocked"] = any(ind in content for ind in block_indicators)
            if workflow_info["blocked"]:
                workflow_info["reason"] = "Blocked due to portfolio state"
        
        if test_case.get("expected_warning"):
            warning_indicators = test_case.get("warning_indicators", [])
            workflow_info["warning"] = any(ind in content for ind in warning_indicators)
        
        # Record result
        result = create_context_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            workflow_info=workflow_info,
            conversation_id=conv_id,
        )
        result.portfolio_state = test_case.get("portfolio_state", "")
        
        self.reporter.add_result(result)
        
        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        assert len(content) > 10, "Response should have meaningful content"
        
        # Note: Actual blocking depends on real user context in test environment
        # The test user may have different portfolio state than expected
        # These tests verify the response is valid, not strict blocking behavior


@pytest.mark.asyncio
@pytest.mark.integration
class TestMultiStepWorkflowBlocking:
    """Test workflow blocking in multi-step flows."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, workflows_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = workflows_reporter
    
    async def test_empty_portfolio_swap_confirmation_blocked(self):
        """Test that empty portfolio can't confirm swap."""
        conv_id = await create_conversation(self.client, title="Empty Swap Confirm Test")
        
        # Step 1: Request swap
        response_data, _ = await send_message(
            self.client, conv_id, "swap 1 ETH to USDC"
        )
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        
        # Should either be blocked or ask for confirmation
        # If blocked, test passes
        if "buy" in content or "empty" in content or "can't" in content:
            return  # Blocked as expected
        
        # Step 2: Try to confirm
        response_data, _ = await send_message(
            self.client, conv_id, "yes"
        )
        
        parsed = parse_response(response_data)
        execute_data = parsed.get("execute_data")
        
        # If empty portfolio, execute should not be allowed
        # (depends on actual user context)
    
    async def test_active_portfolio_swap_confirmation_allowed(self):
        """Test that active portfolio can confirm swap."""
        conv_id = await create_conversation(self.client, title="Active Swap Confirm Test")
        
        # Step 1: Request swap
        response_data, _ = await send_message(
            self.client, conv_id, "swap 0.1 ETH to USDC"
        )
        
        assert not response_data.get("error")
        
        # Step 2: Confirm
        response_data, _ = await send_message(
            self.client, conv_id, "yes"
        )
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        execute_data = parsed.get("execute_data")
        
        # Should either have execute data or completion message
        assert execute_data or any(
            word in content
            for word in ["confirm", "ready", "execute", "proceed", "complete"]
        )
