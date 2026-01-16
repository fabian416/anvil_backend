"""
Integration tests for multi-step guest swap flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import pytest


class TestGuestSwapMultiStepFlow:
    """Test multi-step swap conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_swap_flow_btc_to_eth(self, client):
        """Test complete 5-step swap flow: BTC → ETH."""

        # Step 1: Initiate swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "🔄" in content or "Start Swap" in content
        assert "FROM" in content or "swap FROM" in content.lower()
        assert any(token in content for token in ["BTC", "ETH", "SOL", "USDC"])

        # Verify metadata
        assert data["enrichment"]["swap_flow"] == "step1_from_token"
        assert data["registration_required"]["required"] is True

        # Step 2: Select FROM token (BTC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 2 response
        content = data["agent_message"]["content"]
        assert "BTC" in content
        assert "receive" in content.lower() or "to" in content.lower()
        assert data["enrichment"]["swap_flow"] == "step2_to_token"
        assert data["enrichment"]["from_token"] == "BTC"

        # Step 3: Select TO token (ETH)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response
        content = data["agent_message"]["content"]
        assert "BTC" in content and "ETH" in content
        assert "→" in content or "to" in content
        assert "amount" in content.lower() or "how much" in content.lower()
        assert data["enrichment"]["swap_flow"] == "step3_amount"
        assert data["enrichment"]["from_token"] == "BTC"
        assert data["enrichment"]["to_token"] == "ETH"

        # Step 4: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.01", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 4 response (quote)
        content = data["agent_message"]["content"]
        assert "0.01" in content or "0.0100" in content
        assert "BTC" in content and "ETH" in content
        assert "confirm" in content.lower()

        # Verify quote information present
        assert any(keyword in content.lower() for keyword in ["rate", "exchange", "price"])

        # Verify metadata
        assert data["enrichment"]["swap_flow"] == "step4_confirmation"
        assert data["enrichment"]["from_token"] == "btc"
        assert data["enrichment"]["to_token"] == "eth"
        assert data["enrichment"]["amount"] == "0.01"
        assert "quote" in data["enrichment"]

        # Step 5: Confirm swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 5 response (execution)
        content = data["agent_message"]["content"]
        assert "✅" in content or "Confirmed" in content
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert data["enrichment"]["swap_flow"] == "execution"
        assert data["registration_required"]["required"] is True

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
