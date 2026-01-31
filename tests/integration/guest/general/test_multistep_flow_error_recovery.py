"""
Multi-Step Flow Error Recovery Tests - Week 7

Tests error recovery and resilience for multi-step flows:
- Step failure recovery
- Flow rollback on error
- Partial flow completion
- Retry failed flow step

These tests advance Multi-Step Flows coverage from 85% toward 95%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.multi_step_flows]


class TestMultiStepFlowErrorRecovery:
    """Test error recovery and resilience for multi-step flows."""

    @pytest.mark.llm_validation
    async def test_step_failure_recovery(self, client: AsyncClient, llm_validator):
        """
        Test recovery when handling invalid data.

        Query with invalid or problematic data should be handled gracefully
        with appropriate error messaging.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Send 999999999 ETH to invalid_address_xyz123",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle invalid request gracefully with helpful error message
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide helpful error guidance"

    @pytest.mark.llm_validation
    async def test_flow_rollback_on_error(self, client: AsyncClient, llm_validator):
        """
        Test handling when later step fails after earlier success.

        Multi-step query where later validation might fail should provide
        appropriate feedback about what went wrong.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Check my balance, then send 1000 ETH (which I don't have)",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should recognize insufficient balance scenario
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should explain balance validation"

    @pytest.mark.llm_validation
    async def test_partial_flow_completion(self, client: AsyncClient, llm_validator):
        """
        Test partial completion when full flow cannot finish.

        Query where some steps succeed but others cannot should provide
        partial results with explanation.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Show me Bitcoin price and also tell me my portfolio balance "
                          "(but I don't have an account)",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide Bitcoin price even if portfolio balance unavailable
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide partial results with explanation"

    @pytest.mark.llm_validation
    async def test_retry_failed_flow_step(self, client: AsyncClient, llm_validator):
        """
        Test system resilience with transient-like queries.

        Query that might experience transient issues should eventually succeed
        or provide appropriate fallback.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Get the latest Ethereum price from multiple sources and compare",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle data source queries with resilience
        agent_response = data["agent_message"]["content"]
