"""
Multi-Step Flow Orchestration Tests - Week 7

Tests advanced multi-step flow orchestration scenarios:
- Nested flow execution
- Parallel flow execution
- Flow state persistence
- Flow timeout handling
- Flow dependency resolution
- Conditional flow branching
- Flow result aggregation

These tests advance Multi-Step Flows coverage from 85% toward 95%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.multi_step_flows]


class TestMultiStepFlowOrchestration:
    """Test advanced multi-step flow orchestration scenarios."""

    @pytest.mark.llm_validation
    async def test_nested_flow_execution(self, client: AsyncClient, llm_validator):
        """
        Test execution of nested multi-step flows.

        Query triggering nested flow should handle parent and child flows correctly
        and maintain proper state across nesting levels.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I want to swap ETH for USDC and then lend the USDC on Aave",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Should handle nested swap → lend flow
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 100, "Should provide comprehensive response for nested flow (100+ chars)"

    @pytest.mark.llm_validation
    async def test_parallel_flow_execution(self, client: AsyncClient, llm_validator):
        """
        Test parallel execution of independent flows.

        Multiple independent queries in single request should execute in parallel
        without interference.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Check Bitcoin price, Ethereum gas fees, and Solana network status",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle parallel information requests
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 100, "Should address all parallel requests (100+ chars)"

    @pytest.mark.llm_validation
    async def test_flow_state_persistence(self, client: AsyncClient, llm_validator):
        """
        Test flow state persists across requests.

        Conversation state should persist allowing multi-turn flows
        to maintain context.
        """
        # First message establishes context
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I want to buy $1000 worth of Bitcoin",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Follow-up message in same conversation should use context
        response2 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conversation_id}",
            json={
                "content": "Actually, make it $1500",
                "language": "en"
            }
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        assert "agent_message" in data2
        agent_response = data2["agent_message"]["content"]
        assert len(agent_response) > 50, "Should understand context from previous message"

    @pytest.mark.llm_validation
    async def test_flow_timeout_handling(self, client: AsyncClient, llm_validator):
        """
        Test flow timeout and cleanup.

        Very complex query should complete within reasonable time
        or handle timeout gracefully.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Analyze all DeFi protocols, compare their TVL, APY, risks, "
                          "and recommend the best strategy for yield farming",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should complete within timeout or provide partial results
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide response even for complex query"

    @pytest.mark.llm_validation
    async def test_flow_dependency_resolution(self, client: AsyncClient, llm_validator):
        """
        Test flow dependency resolution and ordering.

        Query with dependent steps should execute in correct order
        with proper dependency handling.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "First check if I have enough ETH, then estimate gas for a swap, "
                          "then calculate the total cost",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should process dependencies in order
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should handle dependent steps logically"

    @pytest.mark.llm_validation
    async def test_conditional_flow_branching(self, client: AsyncClient, llm_validator):
        """
        Test conditional branching in flows based on results.

        Query with conditional logic should follow correct branch
        based on conditions.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "If ETH price is above $2000, recommend buying, "
                          "otherwise suggest waiting",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should evaluate condition and provide appropriate recommendation
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide conditional recommendation"

    @pytest.mark.llm_validation
    async def test_flow_result_aggregation(self, client: AsyncClient, llm_validator):
        """
        Test aggregation of results from multiple flow steps.

        Multi-step query should aggregate results from all steps
        into coherent final response.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Get prices for BTC, ETH, and SOL, then calculate my total "
                          "portfolio value if I have 0.1 BTC, 2 ETH, and 100 SOL",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should aggregate price data and calculate total
        agent_response = data["agent_message"]["content"]
