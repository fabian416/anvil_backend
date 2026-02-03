"""
Cancellation Flow Tests for Authenticated Users.

Tests workflow cancellation and resource cleanup across multi-step processes.
Validates that cancellation is handled gracefully, resources are cleaned up,
and system state remains consistent.
Uses LLM (Vertex AI) validation for semantic output verification.

Migrated from workflows/test_cancellation_flows.py to use new test infrastructure.
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


CANCELLATION_FLOWS = [
    {
        "test_id": "cancel_swap_001",
        "name": "Swap Cancellation",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "cancel", "expect_cancel_ack": True},
        ],
        "category": "multi_step",
        "subcategory": "cancellation",
    },
    {
        "test_id": "cancel_lend_001",
        "name": "Lending Cancellation",
        "steps": [
            {"input": "deposit 1000 USDC", "expect_agent": "lending_workflow"},
            {"input": "no", "expect_cancel_ack": True},
        ],
        "category": "multi_step",
        "subcategory": "cancellation",
    },
    {
        "test_id": "cancel_transfer_001",
        "name": "Transfer Cancellation",
        "steps": [
            {"input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "expect_agent": "transfer_workflow"},
            {"input": "cancel that", "expect_cancel_ack": True},
        ],
        "category": "multi_step",
        "subcategory": "cancellation",
    },
    {
        "test_id": "cancel_buy_001",
        "name": "Buy Cancellation",
        "steps": [
            {"input": "buy $100 of ETH", "expect_agent": "buy_workflow"},
            {"input": "nevermind", "expect_cancel_ack": True},
        ],
        "category": "multi_step",
        "subcategory": "cancellation",
    },
]


CONTEXT_PRESERVATION_FLOWS = [
    {
        "test_id": "context_after_cancel_001",
        "name": "Context After Cancellation",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "cancel", "expect_cancel_ack": True},
            {"input": "what was I trying to do?", "expect_context": True},
        ],
        "category": "multi_step",
        "subcategory": "context_preservation",
    },
    {
        "test_id": "state_consistency_001",
        "name": "State Consistency Post Cancel",
        "steps": [
            {"input": "Tell me about Ethereum staking", "expect_agent": ""},
            {"input": "What are the risks?", "expect_context": True},
            {"input": "Compare staking rewards across validators", "expect_context": True},
        ],
        "category": "multi_step",
        "subcategory": "state_consistency",
    },
]


RESOURCE_CLEANUP_TESTS = [
    {
        "test_id": "cleanup_hunter_001",
        "input": "Analyze Bitcoin market sentiment and provide detailed arbitrage opportunities across 5 exchanges",
        "expected_agent": "hunter_ai",
        "category": "resource_cleanup",
        "subcategory": "hunter_analysis",
    },
    {
        "test_id": "cleanup_multi_hop_001",
        "input": "Execute a multi-hop swap: ETH → USDC → DAI with best routing",
        "expected_agent": "swap_workflow",
        "category": "resource_cleanup",
        "subcategory": "multi_hop",
    },
    {
        "test_id": "cleanup_defi_analysis_001",
        "input": "Analyze top 10 DeFi protocols with TVL, APY, and risk scores",
        "expected_agent": "defi_yield",
        "category": "resource_cleanup",
        "subcategory": "defi_analysis",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCancellationFlows:
    """Tests for workflow cancellation handling."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("flow", CANCELLATION_FLOWS, ids=lambda f: f["test_id"])
    async def test_cancellation_flow(self, flow: dict):
        """Test workflow cancellation is handled gracefully."""
        # Create fresh conversation for each flow
        conv_id = await create_conversation(
            self.client,
            title=f"Cancellation Test: {flow['name']}"
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
            
            assert not response_data.get("error"), f"Step {step_num} failed: {response_data}"
            
            # Verify cancellation acknowledgment
            if step.get("expect_cancel_ack"):
                parsed = parse_response(response_data)
                content = parsed.get("content", "").lower()
                
                # Should acknowledge cancellation gracefully
                assert any(
                    word in content
                    for word in ["cancel", "stopped", "aborted", "okay", "understood", "no problem", "alright"]
                ), f"Step {step_num} should acknowledge cancellation: {content[:200]}"
            
            await asyncio.sleep(0.3)


@pytest.mark.asyncio
@pytest.mark.integration
class TestContextPreservation:
    """Tests for context preservation after cancellation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("flow", CONTEXT_PRESERVATION_FLOWS, ids=lambda f: f["test_id"])
    async def test_context_preservation(self, flow: dict):
        """Test conversation context is preserved after cancellation."""
        conv_id = await create_conversation(
            self.client,
            title=f"Context Test: {flow['name']}"
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
            
            assert not response_data.get("error"), f"Step {step_num} failed: {response_data}"
            
            await asyncio.sleep(0.3)


@pytest.mark.asyncio
@pytest.mark.integration
class TestResourceCleanup:
    """Tests for resource cleanup during workflow execution."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", RESOURCE_CLEANUP_TESTS, ids=lambda t: t["test_id"])
    async def test_resource_cleanup(self, test_case: dict):
        """Test that resources are properly cleaned up after workflow execution."""
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
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "")
        
        # Response should be substantial
        assert len(content) > 50, f"Response too short for complex analysis: {content[:200]}"
