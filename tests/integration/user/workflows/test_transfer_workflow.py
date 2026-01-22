"""
Transfer Workflow Tests for Authenticated Users.

Tests send/transfer operations to addresses.
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
)


TRANSFER_TESTS = [
    # Basic Transfers
    {
        "test_id": "transfer_basic_001",
        "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_basic",
    },
    {
        "test_id": "transfer_basic_002",
        "input": "transfer 0.5 ETH to my friend",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_basic",
    },
    {
        "test_id": "transfer_basic_003",
        "input": "send 50 USDC",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_basic",
    },
    {
        "test_id": "transfer_basic_004",
        "input": "transfer ETH to 0x1234567890abcdef1234567890abcdef12345678",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_basic",
    },
    {
        "test_id": "transfer_basic_005",
        "input": "send 1000 USDT to wallet",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_basic",
    },
    
    # Edge Cases
    {
        "test_id": "transfer_edge_001",
        "input": "send ETH",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_edge",
    },
    {
        "test_id": "transfer_edge_002",
        "input": "transfer",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_edge",
    },
    {
        "test_id": "transfer_edge_003",
        "input": "send crypto",
        "expected_agent": "transfer_workflow",
        "category": "workflow",
        "subcategory": "transfer_edge",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestTransferWorkflow:
    """Tests for Transfer workflow agent."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", TRANSFER_TESTS, ids=lambda t: t["test_id"])
    async def test_transfer(self, test_case: dict):
        """Test transfer workflow routing and response."""
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
        
        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        agents = parsed.get("agents_used", "")
        
        # Verify transfer-related response
        assert any(
            indicator in content or indicator in agents.lower()
            for indicator in ["send", "transfer", "recipient", "address", "wallet"]
        ), f"Transfer query should return transfer-related response: {content[:200]}"
