"""
Integration tests for multi-step guest send flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import pytest


class TestGuestSendMultiStepFlow:
    """Test multi-step send conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_send_flow_eth(self, client):
        """Test complete 4-step send flow: ETH."""

        # Step 1: Initiate send
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "send", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "📤" in content or "Send" in content
        assert "token" in content.lower() or "crypto" in content.lower()
        assert any(token in content for token in ["BTC", "ETH", "SOL", "USDC"])

        # Verify metadata
        assert data["enrichment"]["send_flow"] == "step1_token"
        assert data["registration_required"]["required"] is True

        # Step 2: Select token (ETH)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 2 response
        content = data["agent_message"]["content"]
        assert "ETH" in content or "Ethereum" in content
        assert "amount" in content.lower() or "how much" in content.lower()
        assert data["enrichment"]["send_flow"] == "step2_amount"
        assert data["enrichment"]["token"] == "ETH"

        # Step 3: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.5", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response
        content = data["agent_message"]["content"]
        assert "0.5" in content
        assert "ETH" in content
        assert "address" in content.lower() or "destination" in content.lower()
        assert data["enrichment"]["send_flow"] == "step3_address"
        assert data["enrichment"]["amount"] == "0.5"

        # Step 4: Enter address
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 4 response (review)
        content = data["agent_message"]["content"]
        assert "0.5" in content
        assert "ETH" in content
        assert "0x742d" in content  # Address snippet
        assert "confirm" in content.lower()
        assert data["enrichment"]["send_flow"] == "step4_confirmation"

        # Step 5: Confirm send
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 5 response (execution)
        content = data["agent_message"]["content"]
        assert "✅" in content or "Confirmed" in content or "🎉" in content
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert data["enrichment"]["send_flow"] == "execution"
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_complete_send_flow_btc(self, client):
        """Test complete send flow with Bitcoin."""

        steps = [
            ("send", "step1_token"),
            ("BTC", "step2_amount"),
            ("0.01", "step3_address"),
            ("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "step4_confirmation"),
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
                assert data["enrichment"]["send_flow"] == expected_flow

            # Verify final step
            if i == len(steps):
                assert "🎉" in data["agent_message"]["content"] or "✅" in data["agent_message"]["content"]
                assert data["enrichment"]["send_flow"] == "execution"

    @pytest.mark.asyncio
    async def test_send_flow_with_invalid_address(self, client):
        """Test error handling for invalid address."""

        # Complete flow to address step
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "1", "language": "en"})

        # Enter invalid address
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "invalid_address", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show error and re-ask
        content = data["agent_message"]["content"]
        assert "❌" in content or "error" in content.lower() or "valid" in content.lower()

    @pytest.mark.asyncio
    async def test_send_flow_cancel(self, client):
        """Test cancelling send at confirmation."""

        # Complete flow to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "1", "language": "en"})
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
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
    async def test_send_flow_multilingual_spanish(self, client):
        """Test send flow in Spanish."""

        # Step 1
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "send", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish or English text (fallback)
        assert any(word in content.lower() for word in ["send", "enviar", "token", "cripto"])

    @pytest.mark.asyncio
    async def test_send_security_warnings(self, client):
        """Test that security warnings are displayed."""

        # Get to address step
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.5", "language": "en"}
        )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Verify security warnings
        security_elements = [
            "⚠️" in content or "WARNING" in content.upper(),
            "address" in content.lower(),
            "cannot" in content.lower() or "permanent" in content.lower() or "irreversible" in content.lower(),
        ]
        assert any(security_elements), "Missing security warnings"


class TestGuestSendFlowStorytellingQuality:
    """Test storytelling and UX quality of send responses."""

    @pytest.mark.asyncio
    async def test_responses_have_clear_progression(self, client):
        """Test that each step clearly indicates progression."""

        steps = ["send", "ETH", "0.5", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"]
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
            json={"content": "send", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "📤" in content or "💸" in content or "🚀" in content

    @pytest.mark.asyncio
    async def test_confirmation_step_has_clear_call_to_action(self, client):
        """Test that confirmation step has clear CTAs."""

        # Get to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "send", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "0.1", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action buttons/instructions
        assert "confirm" in content.lower()
        assert "yes" in content.lower() or "proceed" in content.lower()
        assert "cancel" in content.lower() or "abort" in content.lower()
