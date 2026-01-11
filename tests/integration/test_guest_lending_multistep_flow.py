"""
Integration tests for multi-step guest lending/deposit flow.

Tests the complete conversational flow from initiation through confirmation.
"""

import pytest


class TestGuestLendingMultiStepFlow:
    """Test multi-step lending conversational flow."""

    @pytest.mark.asyncio
    async def test_complete_lending_flow_usdc(self, client):
        """Test complete 3-step lending flow: USDC."""

        # Step 1: Initiate lending
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 1 response
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "💰" in content or "Lend" in content or "Earn" in content
        assert "asset" in content.lower() or "crypto" in content.lower()
        assert any(asset in content for asset in ["USDC", "USDT", "DAI", "ETH"])
        assert data["enrichment"]["lending_flow"] == "step1_asset"
        assert data["registration_required"]["required"] is True

        # Step 2: Select asset (USDC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "USDC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 2 response
        content = data["agent_message"]["content"]
        assert "USDC" in content
        assert "amount" in content.lower() or "how much" in content.lower()
        assert data["enrichment"]["lending_flow"] == "step2_amount"
        assert data["enrichment"]["asset"] == "USDC"

        # Step 3: Enter amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify step 3 response (quote)
        content = data["agent_message"]["content"]
        assert "1000" in content
        assert "USDC" in content
        assert "confirm" in content.lower()
        assert data["enrichment"]["lending_flow"] == "step3_confirmation"
        assert data["enrichment"]["amount"] == "1000"

        # Step 4: Confirm deposit
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
        assert data["enrichment"]["lending_flow"] == "execution"
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_complete_lending_flow_eth(self, client):
        """Test complete lending flow with Ethereum."""

        steps = [
            ("lending", "step1_asset"),
            ("ETH", "step2_amount"),
            ("5", "step3_confirmation"),
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
            assert data["enrichment"]["lending_flow"] == expected_flow

            # Verify final step
            if i == len(steps):
                assert "🎉" in data["agent_message"]["content"] or "✅" in data["agent_message"]["content"]

    @pytest.mark.asyncio
    async def test_lending_flow_cancel(self, client):
        """Test cancelling lending at confirmation."""

        # Complete flow to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "DAI", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "500", "language": "en"})

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
    async def test_lending_all_supported_assets(self, client):
        """Test lending flow with all supported assets."""

        assets = ["USDC", "USDT", "DAI", "ETH", "WBTC"]

        for asset in assets:
            # Initiate
            await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})

            # Select asset
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": asset, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify asset selection
            assert data["enrichment"]["asset"] == asset
            assert data["enrichment"]["lending_flow"] == "step2_amount"

    @pytest.mark.asyncio
    async def test_lending_demo_apy_display(self, client):
        """Test that lending shows demo APY."""

        # Complete flow to quote
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should show demo APY components
        assert "%" in content  # APY percentage
        assert "USDC" in content  # Asset
        assert "Demo" in content or "demo" in content.lower()  # Demo indicator
        # Should show earnings estimates
        assert "earn" in content.lower() or "month" in content.lower() or "year" in content.lower()

    @pytest.mark.asyncio
    async def test_lending_number_selection(self, client):
        """Test that users can select assets by number."""

        # Initiate
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})

        # Select option 1 (USDC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should select USDC
        assert data["enrichment"]["asset"] == "USDC"
        assert data["enrichment"]["lending_flow"] == "step2_amount"

    @pytest.mark.asyncio
    async def test_lending_flow_multilingual_spanish(self, client):
        """Test lending flow in Spanish."""

        # Step 1
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "préstamo", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish or English text (fallback)
        assert any(word in content.lower() for word in ["depositar", "deposit", "cripto", "crypto", "ganar", "earn"])

    @pytest.mark.asyncio
    async def test_lending_apy_breakdown(self, client):
        """Test that quote shows APY breakdown."""

        # Get to quote step
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Verify APY breakdown shown
        enrichment = data["enrichment"]
        assert "apy" in enrichment
        assert "monthly_earnings" in enrichment
        assert "yearly_earnings" in enrichment

        # Verify content shows earnings
        assert "APY" in content or "%" in content
        assert "month" in content.lower() or "year" in content.lower()


class TestGuestLendingFlowStorytellingQuality:
    """Test storytelling and UX quality of lending responses."""

    @pytest.mark.asyncio
    async def test_responses_have_clear_progression(self, client):
        """Test that each step clearly indicates progression."""

        steps = ["lending", "USDC", "1000"]
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
            json={"content": "lending", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "💰" in content or "💵" in content or "📈" in content

    @pytest.mark.asyncio
    async def test_confirmation_step_has_clear_call_to_action(self, client):
        """Test that confirmation step has clear CTAs."""

        # Get to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "DAI", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "500", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action buttons/instructions
        assert "confirm" in content.lower()
        assert "yes" in content.lower() or "proceed" in content.lower()
        assert "cancel" in content.lower() or "abort" in content.lower()

    @pytest.mark.asyncio
    async def test_quote_shows_earnings_breakdown(self, client):
        """Test that quote step shows clear earnings breakdown."""

        # Get to quote step
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should show clear earnings breakdown
        earnings_elements = [
            "APY" in content or "%" in content,
            "month" in content.lower(),
            "year" in content.lower(),
        ]
        assert sum(earnings_elements) >= 2, "Should show clear earnings breakdown"
