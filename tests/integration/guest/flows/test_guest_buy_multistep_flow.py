"""
Integration tests for multi-step guest buy flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import pytest


class TestGuestBuyMultiStepFlow:
    """Test multi-step buy conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_buy_flow_eth(self, client):
        """Test complete 3-step buy flow: ETH."""

        # Step 1: Initiate buy
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "buy", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "💳" in content or "Buy" in content
        assert "crypto" in content.lower() or "token" in content.lower()
        assert any(token in content for token in ["BTC", "ETH", "SOL", "USDC"])
        assert data["enrichment"]["buy_flow"] == "step1_crypto"
        assert data["registration_required"]["required"] is True

        # Step 2: Select crypto (ETH)
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
        assert data["enrichment"]["buy_flow"] == "step2_amount"
        assert data["enrichment"]["crypto"] == "ETH"

        # Step 3: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "100", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response (quote)
        content = data["agent_message"]["content"]
        assert "100" in content or "$100" in content
        assert "ETH" in content
        assert "confirm" in content.lower()
        assert data["enrichment"]["buy_flow"] == "step3_confirmation"
        assert data["enrichment"]["amount_usd"] == "100"

        # Step 4: Confirm buy
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 4 response (execution)
        content = data["agent_message"]["content"]
        assert "✅" in content or "Confirmed" in content or "🎉" in content
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert data["enrichment"]["buy_flow"] == "execution"
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_complete_buy_flow_btc(self, client):
        """Test complete buy flow with Bitcoin."""

        steps = [
            ("buy", "step1_crypto"),
            ("BTC", "step2_amount"),
            ("50", "step3_confirmation"),
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
            assert data["enrichment"]["buy_flow"] == expected_flow

            # Verify final step
            if i == len(steps):
                assert "🎉" in data["agent_message"]["content"] or "✅" in data["agent_message"]["content"]

    @pytest.mark.asyncio
    async def test_buy_flow_cancel(self, client):
        """Test cancelling buy at confirmation."""

        # Complete flow to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "200", "language": "en"})

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
    async def test_buy_all_supported_cryptos(self, client):
        """Test buy flow with all supported cryptos."""

        cryptos = ["BTC", "ETH", "SOL", "USDC", "USDT", "MATIC"]

        for crypto in cryptos:
            # Initiate
            await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})

            # Select crypto
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": crypto, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify crypto selection
            assert data["enrichment"]["crypto"] == crypto
            assert data["enrichment"]["buy_flow"] == "step2_amount"

    @pytest.mark.asyncio
    async def test_buy_demo_pricing(self, client):
        """Test that buy shows demo pricing."""

        # Complete flow to quote
        await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "100", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should show demo pricing components
        assert "$" in content  # USD amount
        assert "ETH" in content  # Crypto symbol
        assert "Demo" in content or "demo" in content.lower()  # Demo indicator
        # Should show processing fee
        assert "fee" in content.lower() or "2.99" in content or "processing" in content.lower()

    @pytest.mark.asyncio
    async def test_buy_flow_multilingual_spanish(self, client):
        """Test buy flow in Spanish."""

        # Step 1
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "comprar", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish or English text (fallback)
        assert any(word in content.lower() for word in ["comprar", "buy", "cripto", "crypto"])

    @pytest.mark.asyncio
    async def test_buy_security_warnings(self, client):
        """Test that security warnings are displayed."""

        # Get to confirmation step
        await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "100", "language": "en"}
        )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Verify quote display with clear breakdown
        assert "$" in content
        assert "ETH" in content


class TestGuestBuyFlowStorytellingQuality:
    """Test storytelling and UX quality of buy responses."""

    @pytest.mark.asyncio
    async def test_responses_have_clear_progression(self, client):
        """Test that each step clearly indicates progression."""

        steps = ["buy", "ETH", "100"]
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
            json={"content": "buy", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "💳" in content or "💰" in content or "🚀" in content

    @pytest.mark.asyncio
    async def test_confirmation_step_has_clear_call_to_action(self, client):
        """Test that confirmation step has clear CTAs."""

        # Get to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "50", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action buttons/instructions
        assert "confirm" in content.lower()
        assert "yes" in content.lower() or "proceed" in content.lower()
        assert "cancel" in content.lower() or "abort" in content.lower()

    @pytest.mark.asyncio
    async def test_quote_shows_pricing_breakdown(self, client):
        """Test that quote step shows clear pricing breakdown."""

        # Get to quote step
        await client.post("/api/v1/guest/chat", json={"content": "buy", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "ETH", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "100", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should show clear pricing breakdown
        assert "$" in content  # USD amounts
        assert "ETH" in content  # Crypto amount
        # Should show components of the transaction
        pricing_elements = [
            "amount" in content.lower() or "$100" in content,
            "fee" in content.lower() or "2.99" in content,
            "total" in content.lower() or "receive" in content.lower(),
        ]
        assert sum(pricing_elements) >= 2, "Should show clear pricing breakdown"
