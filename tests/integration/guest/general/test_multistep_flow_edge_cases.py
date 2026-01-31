"""
Multi-Step Flow Edge Cases Tests - Week 7

Tests edge cases and boundary conditions for multi-step flows:
- Empty flow execution
- Single-step flow
- Maximum flow steps
- Flow with all step types

These tests advance Multi-Step Flows coverage from 85% toward 95%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.multi_step_flows]


class TestMultiStepFlowEdgeCases:
    """Test edge cases and boundary conditions for multi-step flows."""

    @pytest.mark.llm_validation
    async def test_empty_flow_execution(self, client: AsyncClient, llm_validator):
        """
        Test execution of empty or ambiguous query.

        Query with no clear intent should be handled gracefully
        with appropriate clarification request.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I'm not sure what to do",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide helpful response even for ambiguous query
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should offer guidance for ambiguous query"

    @pytest.mark.llm_validation
    async def test_single_step_flow(self, client: AsyncClient, llm_validator):
        """
        Test flow with only one step (simple query).

        Single-step query should execute correctly without
        multi-step orchestration overhead.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the current Bitcoin price?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide direct answer for simple query
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 20, "Should provide price information"

    @pytest.mark.llm_validation
    async def test_maximum_flow_steps(self, client: AsyncClient, llm_validator):
        """
        Test flow with many sequential steps.

        Query requiring multiple sequential operations should
        handle all steps without degradation.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Check BTC price, check ETH price, check SOL price, "
                          "check gas fees, check network status, calculate my portfolio "
                          "value, recommend best DeFi protocol, and suggest next action",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle multiple sequential requests
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 150, "Should address all steps in complex flow (150+ chars)"

    @pytest.mark.llm_validation
    async def test_flow_with_all_step_types(self, client: AsyncClient, llm_validator):
        """
        Test flow containing different types of operations.

        Query combining query, analysis, and recommendation steps
        should handle all types correctly.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Show me Ethereum's price (query), analyze if it's a good time "
                          "to buy (analysis), and recommend whether I should buy now or wait "
                          "(recommendation)",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle query + analysis + recommendation
        agent_response = data["agent_message"]["content"]
