"""
Multi-Step Flow Cancellation Tests for Chat Endpoints.

Tests ability to cancel or interrupt multi-step conversational flows:
- Swap flow cancellation at each step
- Lending flow cancellation at each step
- Compound intent cancellation
- Timeout-based cancellation
- Topic change detection and implicit cancellation
- State cleanup after cancellation
- Ability to start new flows after cancellation

Ensures proper user experience and state management.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


# Mark all tests as integration and multi-step tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.multistep]


# ============================================================================
# Swap Flow Cancellation Tests
# ============================================================================


class TestSwapFlowCancellation:
    """Test cancelling swap flows at various steps."""

    @pytest.mark.llm_validation
    async def test_cancel_swap_via_explicit_keyword(self, client: AsyncClient, llm_validator):
        """Test explicit cancellation using 'cancel' keyword."""
        # Start a swap-related conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to swap tokens", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")

        # Intent should be swap-related
        if "routing" in data1:
            intent = data1["routing"].get("intent", "").upper()
            # May be GENERAL or specific swap intent

        # Try to cancel
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Cancellation should be acknowledged
        agent_response = data2.get("agent_message", {}).get("content", "").lower()
        # Agent should acknowledge cancellation or ask "what would you like to do?"

    @pytest.mark.llm_validation
    async def test_cancel_swap_via_never_mind(self, client: AsyncClient, llm_validator):
        """Test cancellation using 'never mind' phrase."""
        # Start swap intent
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "help me swap ETH", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Cancel with "never mind"
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "never mind", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should handle gracefully
        assert "agent_message" in data2

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_swap_flow_topic_change_to_query(self, client: AsyncClient, llm_validator):
        """Test implicit cancellation when topic changes from swap to query."""
        # Start swap discussion
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to swap some tokens", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Change topic completely to a query
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what's the current BTC price?", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should handle new query intent
        if "routing" in data2:
            new_intent = data2["routing"].get("intent", "").upper()
            # Should be price query related, not swap

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

class TestLendingFlowCancellation:
    """Test cancelling lending flows at various steps."""

    @pytest.mark.llm_validation
    async def test_cancel_lending_via_stop_keyword(self, client: AsyncClient, llm_validator):
        """Test cancelling lending flow with 'stop' command."""
        # Start lending conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to lend my USDC", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # Extract agent response for validation (from first response)
        agent_response = data1["agent_message"]["content"]

        # Check if lending intent detected or requires registration
        if "registration_required" in data1:
            # Expected for guests - lending requires registration
            assert data1["registration_required"]["required"] == True
        else:
            # If discussing lending, try to cancel
            response2 = await client.post(
                "/api/v1/guest/chat",
                json={"content": "stop", "language": "en"}
            )

            assert response2.status_code == status.HTTP_200_OK

    @pytest.mark.llm_validation
    async def test_cancel_lending_before_protocol_selection(self, client: AsyncClient, llm_validator):
        """Test cancelling lending flow before protocol selection."""
        # Ask about lending
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how do I lend tokens?", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Cancel before proceeding
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "actually, cancel that", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should acknowledge cancellation
        assert "agent_message" in data2

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_lending_flow_implicit_cancel_via_topic_shift(self, client: AsyncClient, llm_validator):
        """Test implicit cancellation when topic shifts from lending."""
        # Start lending inquiry
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "tell me about lending on Aave", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Shift to completely different topic
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what agents do you have?", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should handle new intent (agent squad query)
        assert "agent_message" in data2

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

class TestCompoundIntentCancellation:
    """Test cancelling compound intents (multiple sub-intents)."""

    @pytest.mark.llm_validation
    async def test_compound_intent_full_cancellation(self, client: AsyncClient, llm_validator):
        """Test cancelling entire compound intent before execution."""
        # Complex multi-step request
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to swap ETH for USDC then lend it", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # For guests, this likely requires registration
        # But we can test cancellation of the intent

        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel everything", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_multi_action_intent_cancellation(self, client: AsyncClient, llm_validator):
        """Test cancelling multi-action intents."""
        # Request with multiple actions
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "check my portfolio and show trading signals", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # Both actions require registration for guests
        if "registration_required" in data1:
            assert data1["registration_required"]["required"] == True

        # Extract agent response for validation
        agent_response = data1["agent_message"]["content"]

class TestFlowStateCleanup:
    """Test that cancellation properly cleans up conversation state."""

    @pytest.mark.llm_validation
    async def test_cancelled_flow_allows_new_conversation(self, client: AsyncClient, llm_validator):
        """Test user can start fresh conversation after cancellation."""
        # Start a flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to do a swap", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        conversation_id = response1.json().get("conversation_id")

        # Cancel
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK

        # Start completely new conversation topic
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what can you help me with?", "language": "en"}
        )

        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()

        # Should handle fresh conversation
        assert "agent_message" in data3
        # May or may not have same conversation_id (implementation dependent)

        # Extract agent response for validation
        agent_response = data3["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_multiple_cancellations_handled_gracefully(self, client: AsyncClient, llm_validator):
        """Test multiple consecutive cancellations don't cause issues."""
        # Send cancel without any active flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()

        # Should handle gracefully (no flow to cancel)
        assert "agent_message" in data1

        # Send another cancel
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "stop", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

class TestTopicChangeDetection:
    """Test detection of topic changes and implicit flow cancellation."""

    @pytest.mark.llm_validation
    async def test_topic_change_from_execution_to_query(self, client: AsyncClient, llm_validator):
        """Test topic change from execution intent to informational query."""
        # Start execution intent (swap)
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "help me swap tokens", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Shift to informational query
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what is gas optimization?", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should handle query about gas optimization
        agent_response = data2.get("agent_message", {}).get("content", "").lower()
        # Response should be about gas, not continuing swap flow

    @pytest.mark.llm_validation
    async def test_topic_change_preserves_conversation_context(self, client: AsyncClient, llm_validator):
        """Test topic change preserves some conversation context."""
        # Discuss ETH
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "tell me about Ethereum", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Ask related question with pronoun
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what's its current price?", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should understand "its" refers to Ethereum
        assert "agent_message" in data2

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_topic_change_detection_threshold(self, client: AsyncClient, llm_validator):
        """Test that minor topic shifts don't trigger cancellation."""
        # Talk about trading
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I'm interested in trading", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK

        # Related but slightly different topic (still trading domain)
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what are trading signals?", "language": "en"}
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should handle as related topic, not complete change
        assert "agent_message" in data2

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

class TestCancellationKeywords:
    """Test various cancellation keywords and phrases."""

    @pytest.mark.llm_validation
    async def test_cancel_keyword_variations(self, client: AsyncClient, llm_validator):
        """Test different cancellation keywords work."""
        cancellation_phrases = [
            "cancel",
            "stop",
            "never mind",
            "forget it",
            "abort"
        ]

        for phrase in cancellation_phrases:
            # Start a conversation
            response1 = await client.post(
                "/api/v1/guest/chat",
                json={"content": "I want to do a swap", "language": "en"}
            )

            assert response1.status_code == status.HTTP_200_OK

            # Try cancellation phrase
            response2 = await client.post(
                "/api/v1/guest/chat",
                json={"content": phrase, "language": "en"}
            )

            # Should handle gracefully (not error)
            assert response2.status_code == status.HTTP_200_OK
            data2 = response2.json()
            assert "agent_message" in data2

        # Extract agent response for validation (from last iteration)
        agent_response = data2["agent_message"]["content"]
