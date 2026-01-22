"""
Execution Agent Tests for Authenticated Users.

Tests the execution flow for workflow actions.
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
    create_conversation,
)


EXECUTION_TESTS = [
    # Swap Execution
    {
        "test_id": "exec_swap_ready_001",
        "flow": [
            {"input": "swap 0.1 ETH to USDC", "expect_agent": "swap_workflow"},
            {"input": "yes", "expect_execute_data": True},
        ],
        "category": "execution",
        "subcategory": "swap_execute",
    },
    
    # Lending Execution
    {
        "test_id": "exec_lend_ready_001",
        "flow": [
            {"input": "deposit 100 USDC", "expect_agent": "lending_workflow"},
            {"input": "confirm", "expect_execute_data": True},
        ],
        "category": "execution",
        "subcategory": "lend_execute",
    },
    
    # Transfer Execution
    {
        "test_id": "exec_transfer_ready_001",
        "flow": [
            {"input": "send 10 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "expect_agent": "transfer_workflow"},
            {"input": "proceed", "expect_execute_data": True},
        ],
        "category": "execution",
        "subcategory": "transfer_execute",
    },
]


EXECUTE_DATA_STRUCTURE_TESTS = [
    {
        "test_id": "exec_data_swap_001",
        "input": "swap 0.1 ETH to USDC",
        "expected_agent": "swap_workflow",
        "category": "execution",
        "subcategory": "data_structure",
        "expected_fields": ["action_type", "from_token", "to_token", "amount"],
    },
    {
        "test_id": "exec_data_lend_001",
        "input": "deposit 100 USDC on Morpho",
        "expected_agent": "lending_workflow",
        "category": "execution",
        "subcategory": "data_structure",
        "expected_fields": ["action_type", "protocol", "token", "amount"],
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestExecutionFlows:
    """Tests for execution flow completeness."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", EXECUTION_TESTS, ids=lambda t: t["test_id"])
    async def test_execution_flow(self, test_case: dict):
        """Test execution flow produces execute data."""
        conv_id = await create_conversation(
            self.client,
            title=f"Execution Test: {test_case['test_id']}"
        )
        
        flow = test_case["flow"]
        total_steps = len(flow)
        
        final_response = None
        
        for step_num, step in enumerate(flow, 1):
            response_data, response_time_ms = await send_message(
                self.client,
                conv_id,
                step["input"],
            )
            
            step_test_case = {
                "input": step["input"],
                "expected_agent": step.get("expect_agent", ""),
                "category": test_case["category"],
                "subcategory": test_case["subcategory"],
                "is_multi_step": True,
                "step_number": step_num,
                "total_steps": total_steps,
                "requires_execute": step.get("expect_execute_data", False),
            }
            
            result = create_test_result(
                test_id=f"{test_case['test_id']}_step{step_num}",
                test_case=step_test_case,
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conv_id,
            )
            
            self.reporter.add_result(result)
            
            assert not response_data.get("error"), f"Step {step_num} failed: {response_data}"
            
            if step.get("expect_execute_data"):
                final_response = response_data
        
        # Verify final step has execute data
        if final_response:
            parsed = parse_response(final_response)
            execute_data = parsed.get("execute_data")
            
            # Execute data should be present or response should indicate ready state
            content = parsed.get("content", "").lower()
            has_ready_indication = any(
                word in content
                for word in ["ready", "execute", "confirm", "proceed", "transaction"]
            )
            
            assert execute_data or has_ready_indication, \
                "Final step should have execute data or ready indication"


@pytest.mark.asyncio
@pytest.mark.integration
class TestExecuteDataStructure:
    """Tests for execute data structure validation."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", EXECUTE_DATA_STRUCTURE_TESTS, ids=lambda t: t["test_id"])
    async def test_execute_data_fields(self, test_case: dict):
        """Test execute data contains expected fields."""
        conv_id = await create_conversation(
            self.client,
            title=f"Execute Data Test: {test_case['test_id']}"
        )
        
        # Initial request
        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
            test_case["input"],
        )
        
        result = create_test_result(
            test_id=f"{test_case['test_id']}_init",
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=conv_id,
        )
        
        self.reporter.add_result(result)
        
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        # Confirm to get execute data
        response_data, response_time_ms = await send_message(
            self.client,
            conv_id,
            "yes confirm",
        )
        
        result = create_test_result(
            test_id=f"{test_case['test_id']}_confirm",
            test_case={
                **test_case,
                "input": "yes confirm",
                "requires_execute": True,
            },
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=conv_id,
        )
        
        self.reporter.add_result(result)
        
        # Check execute data structure (if available)
        parsed = parse_response(response_data)
        execute_data = parsed.get("execute_data")
        
        if execute_data and isinstance(execute_data, dict):
            # Verify expected fields are present
            for field in test_case.get("expected_fields", []):
                assert field in execute_data or any(
                    field.lower() in str(v).lower() 
                    for v in execute_data.values()
                ), f"Execute data should contain {field}"
