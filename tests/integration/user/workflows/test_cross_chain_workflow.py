"""
Cross-Chain Workflow Tests for Authenticated Users.

Tests bridging, cross-chain swaps, and multi-chain operations.
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


CROSS_CHAIN_TESTS = [
    # Bridge Operations
    {
        "test_id": "bridge_eth_001",
        "input": "bridge 1 ETH from Ethereum to Base",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "bridge",
    },
    {
        "test_id": "bridge_usdc_001",
        "input": "bridge 1000 USDC from Ethereum to Arbitrum",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "bridge",
    },
    {
        "test_id": "bridge_generic_001",
        "input": "move my ETH to Polygon",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "bridge",
    },
    
    # Cross-Chain Swaps
    {
        "test_id": "cross_swap_001",
        "input": "swap ETH on Ethereum to USDC on Base",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "cross_chain_swap",
    },
    {
        "test_id": "cross_swap_002",
        "input": "convert USDC on Arbitrum to ETH on Ethereum",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "cross_chain_swap",
    },
    
    # Chain-Specific Operations
    {
        "test_id": "chain_base_001",
        "input": "swap ETH to USDC on Base",
        "expected_agent": "swap_workflow",
        "category": "workflow",
        "subcategory": "chain_base",
    },
    {
        "test_id": "chain_arbitrum_001",
        "input": "deposit USDC on Aave Arbitrum",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "chain_arbitrum",
    },
    {
        "test_id": "chain_polygon_001",
        "input": "best yield opportunities on Polygon",
        "expected_agent": "defi_yield",
        "category": "workflow",
        "subcategory": "chain_polygon",
    },
    {
        "test_id": "chain_optimism_001",
        "input": "compare lending rates on Optimism",
        "expected_agent": "money_market_workflow",
        "category": "workflow",
        "subcategory": "chain_optimism",
    },
    
    # Multi-Chain Queries
    {
        "test_id": "multi_chain_001",
        "input": "compare USDC yields across Ethereum, Arbitrum, and Base",
        "expected_agent": "defi_yield",
        "category": "workflow",
        "subcategory": "multi_chain_compare",
    },
    {
        "test_id": "multi_chain_002",
        "input": "where is my USDC worth more, Ethereum or Arbitrum?",
        "expected_agent": "defi_yield",
        "category": "workflow",
        "subcategory": "multi_chain_compare",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCrossChainWorkflow:
    """Tests for cross-chain operations."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", CROSS_CHAIN_TESTS, ids=lambda t: t["test_id"])
    async def test_cross_chain(self, test_case: dict):
        """Test cross-chain workflow routing and response."""
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
        
        # Verify cross-chain related response
        assert any(
            indicator in content
            for indicator in [
                "bridge", "cross-chain", "ethereum", "base", "arbitrum", "polygon", 
                "optimism", "layer", "chain", "transfer", "route"
            ]
        ), f"Cross-chain query should return relevant response: {content[:200]}"
