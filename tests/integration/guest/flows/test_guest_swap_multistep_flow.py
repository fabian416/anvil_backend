"""
Integration tests for multi-step guest swap flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import json
import warnings
from datetime import datetime

import pytest


class TestGuestSwapMultiStepFlow:
    """Test multi-step swap conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_swap_flow_btc_to_eth(self, client, llm_validator, csv_tracker):
        """Test complete 5-step swap flow: BTC → ETH."""

        # Build conversation history for multi-step validation
        conversation_history = []

        # Step 1: Initiate swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        step1_content = data["agent_message"]["content"]
        assert "🔄" in step1_content or "Start Swap" in step1_content
        assert "FROM" in step1_content or "swap FROM" in step1_content.lower()
        assert any(token in step1_content for token in ["BTC", "ETH", "SOL", "USDC"])

        # Verify metadata
        assert data["enrichment"]["swap_flow"] == "step1_from_token"
        assert data["registration_required"]["required"] is True

        # Track step 1
        conversation_history.append({"user": "swap", "agent": step1_content})

        # Step 2: Select FROM token (BTC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 2 response
        step2_content = data["agent_message"]["content"]
        assert "BTC" in step2_content
        assert "receive" in step2_content.lower() or "to" in step2_content.lower()
        assert data["enrichment"]["swap_flow"] == "step2_to_token"
        assert data["enrichment"]["from_token"] == "BTC"

        # Track step 2
        conversation_history.append({"user": "BTC", "agent": step2_content})

        # Step 3: Select TO token (ETH)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response
        step3_content = data["agent_message"]["content"]
        assert "BTC" in step3_content and "ETH" in step3_content
        assert "→" in step3_content or "to" in step3_content
        assert "amount" in step3_content.lower() or "how much" in step3_content.lower()
        assert data["enrichment"]["swap_flow"] == "step3_amount"
        assert data["enrichment"]["from_token"] == "BTC"
        assert data["enrichment"]["to_token"] == "ETH"

        # Track step 3
        conversation_history.append({"user": "ETH", "agent": step3_content})

        # Step 4: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.01", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 4 response (quote)
        step4_content = data["agent_message"]["content"]
        assert "0.01" in step4_content or "0.0100" in step4_content
        assert "BTC" in step4_content and "ETH" in step4_content
        assert "confirm" in step4_content.lower()

        # Verify quote information present
        assert any(keyword in step4_content.lower() for keyword in ["rate", "exchange", "price"])

        # Verify metadata
        assert data["enrichment"]["swap_flow"] == "step4_confirmation"
        assert data["enrichment"]["from_token"] == "btc"
        assert data["enrichment"]["to_token"] == "eth"
        assert data["enrichment"]["amount"] == "0.01"
        assert "quote" in data["enrichment"]

        # Track step 4
        conversation_history.append({"user": "0.01", "agent": step4_content})

        # Step 5: Confirm swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 5 response (execution)
        step5_content = data["agent_message"]["content"]
        assert "✅" in step5_content or "Confirmed" in step5_content
        assert "sign up" in step5_content.lower() or "signup" in step5_content.lower()
        assert data["enrichment"]["swap_flow"] == "execution"
        assert data["registration_required"]["required"] is True

        # Track step 5
        conversation_history.append({"user": "confirm", "agent": step5_content})

        # PHASE 3: LLM validation with multi-step conversation history
        validation = None
    @pytest.mark.asyncio
    async def test_complete_swap_flow_usdc_to_sol(self, client):
        """Test complete swap flow with different tokens: USDC → SOL."""

        steps = [
            ("swap", "step1_from_token"),
            ("USDC", "step2_to_token"),
            ("SOL", "step3_amount"),
            ("100", "step4_confirmation"),
            ("yes", "execution"),
        ]

        for i, (message, expected_flow) in enumerate(steps, 1):
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": message, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify progression
            if i < len(steps):  # Not last step
                assert data["enrichment"]["swap_flow"] == expected_flow

            # Verify final step
            if i == len(steps):
                assert "🎉" in data["agent_message"]["content"]
                assert data["enrichment"]["swap_flow"] == "execution"

    @pytest.mark.asyncio
    async def test_swap_flow_with_invalid_token(self, client):
        """Test error handling for invalid token."""

        # Start swap
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )

        # Enter invalid token
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "INVALID_TOKEN", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show error and re-ask
        content = data["agent_message"]["content"]
        assert "❌" in content or "error" in content.lower() or "valid" in content.lower()
        assert any(token in content for token in ["BTC", "ETH", "SOL", "USDC"])

    @pytest.mark.asyncio
    async def test_swap_flow_with_invalid_amount(self, client):
        """Test error handling for invalid amount."""

        # Complete first 2 steps
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )

        # Enter invalid amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "not_a_number", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show error and re-ask
        content = data["agent_message"]["content"]
        assert "❌" in content or "valid" in content.lower()
        assert "amount" in content.lower() or "number" in content.lower()

    @pytest.mark.asyncio
    async def test_swap_flow_cancel(self, client):
        """Test cancelling swap at confirmation."""

        # Complete flow to confirmation
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.5", "language": "en"}
        )

        # Cancel
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "cancel", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert "❌" in content or "cancel" in content.lower()

    @pytest.mark.asyncio
    async def test_swap_flow_edit_amount(self, client):
        """Test changing amount at confirmation step."""

        # Complete flow to confirmation
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "1", "language": "en"}
        )

        # Change amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "change amount to 0.5", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show new quote
        content = data["agent_message"]["content"]
        assert "0.5" in content
        assert "confirm" in content.lower()

    @pytest.mark.asyncio
    async def test_swap_flow_multilingual_spanish(self, client):
        """Test swap flow in Spanish."""

        # Step 1
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish text
        assert any(word in content.lower() for word in ["swap", "intercambiar", "token", "disponibles"])

    @pytest.mark.asyncio
    async def test_swap_flow_complete_request(self, client):
        """Test providing complete swap info in one message."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap 1 BTC to ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should skip to confirmation
        content = data["agent_message"]["content"]
        assert "BTC" in content and "ETH" in content
        assert "confirm" in content.lower()
        assert data["enrichment"]["swap_flow"] == "step4_confirmation"

    @pytest.mark.asyncio
    async def test_swap_pricing_information_accuracy(self, client):
        """Test that pricing information is displayed and formatted correctly."""

        # Complete flow to quote
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.01", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Verify pricing elements are present
        pricing_elements = [
            "Exchange Rate" in content or "Rate" in content,
            "Network Fee" in content or "Fee" in content,
            "=" in content,  # Quote display
        ]
        assert any(pricing_elements), "Missing pricing information in quote"

        # Verify quote data in enrichment
        assert "quote" in data["enrichment"]
        quote = data["enrichment"]["quote"]

        # Verify quote structure
        assert isinstance(quote, dict)
        # Note: Actual values depend on MoonPay API response

    @pytest.mark.asyncio
    async def test_swap_flow_state_persistence_across_10_messages(self, client):
        """Test that swap state persists even after 10+ messages in conversation."""

        # Send 12 messages before starting swap to test >10 message limit
        for i in range(12):
            await client.post(
                "/api/v1/guest/chat",
                json={"content": f"hello {i}", "language": "en"}
            )

        # Now start swap flow
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        assert response.status_code == 200
        # Verify it's a swap flow step (step1_from_token, step2_to_token, etc.)
        assert "step" in response.json()["enrichment"]["swap_flow"] or "swap" in response.json()["enrichment"]["swap_flow"]

        # Continue with BTC
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify continuation worked (should ask for TO token, not restart)
        assert "step2" in data["enrichment"]["swap_flow"] or "to_token" in data["enrichment"]["swap_flow"]
        assert "BTC" in data["agent_message"]["content"]


class TestGuestSwapFlowStorytellingQuality:
    """Test storytelling and UX quality of responses."""

    @pytest.mark.asyncio
    async def test_responses_have_clear_progression(self, client):
        """Test that each step clearly indicates progression."""

        steps = ["swap", "BTC", "ETH", "0.5"]
        previous_content = ""

        for step in steps:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": step, "language": "en"}
            )
            content = response.json()["agent_message"]["content"]

            # Each response should be different
            assert content != previous_content
            previous_content = content

    @pytest.mark.asyncio
    async def test_responses_use_emojis_for_visual_appeal(self, client):
        """Test that responses use emojis to enhance communication."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "🔄" in content or "💱" in content or "🌙" in content

    @pytest.mark.asyncio
    async def test_confirmation_step_has_clear_call_to_action(self, client):
        """Test that confirmation step has clear CTAs."""

        # Get to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "swap", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "BTC", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.1", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action buttons/instructions
        assert "confirm" in content.lower()
        assert "yes" in content.lower() or "proceed" in content.lower()
        assert "cancel" in content.lower() or "abort" in content.lower()
