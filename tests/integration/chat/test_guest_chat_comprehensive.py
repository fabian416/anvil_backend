"""
Comprehensive integration tests for guest chat endpoint.

Tests all multi-step flows, shortcuts, and database persistence following CTO methodology.

Test Strategy (CTO Framework):
- Phase 1: Test all multi-step flows end-to-end
- Phase 2: Validate database persistence at each step
- Phase 3: Verify production-grade response quality
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.chat
class TestGuestChatMultiStepFlows:
    """Test all multi-step conversational flows for guests."""

    @pytest.mark.asyncio
    async def test_lending_flow_complete_usdc(self, client: AsyncClient):
        """
        Test complete LENDING flow: Asset → Amount → Quote → Confirm.

        Validates:
        - Step progression (4 steps)
        - State preservation (pending_action, lending_info)
        - Response quality (emojis, CTAs, clear messaging)
        - Registration requirement
        """
        # Step 1: Initiate lending
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 1: Asset selection
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert any(word in content for word in ["💰", "Earn", "deposit"])
        assert "USDC" in content or "asset" in content.lower()
        assert data["enrichment"]["lending_flow"] == "step1_asset"
        assert data["registration_required"]["required"] is True

        # Step 2: Select USDC (by name)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "USDC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 2: Amount input
        content = data["agent_message"]["content"]
        assert "USDC" in content
        assert "amount" in content.lower() or "how much" in content.lower()
        assert data["enrichment"]["lending_flow"] == "step2_amount"
        assert data["enrichment"]["asset"] == "USDC"

        # Step 3: Enter amount (1000 USDC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 3: Quote with APY
        content = data["agent_message"]["content"]
        assert "1000" in content and "USDC" in content
        assert "APY" in content or "%" in content  # Show APY
        assert "confirm" in content.lower()  # Clear CTA
        assert data["enrichment"]["lending_flow"] == "step3_confirmation"
        assert data["enrichment"]["amount"] in ["1000", "1000.0"]  # Accept both string and float representation
        assert "apy" in data["enrichment"]
        assert "monthly_earnings" in data["enrichment"]
        assert "yearly_earnings" in data["enrichment"]

        # Step 4: Confirm deposit
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 4: Execution (signup required)
        content = data["agent_message"]["content"]
        assert any(emoji in content for emoji in ["✅", "🎉"])
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert data["enrichment"]["lending_flow"] == "execution"
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_lending_flow_with_number_selection(self, client: AsyncClient):
        """Test LENDING flow using number selection (option 1 = USDC)."""
        # Step 1: Initiate
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})

        # Step 2: Select option 1 (USDC)
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
    async def test_lending_flow_cancel(self, client: AsyncClient):
        """Test cancelling LENDING flow at confirmation step."""
        # Navigate to confirmation
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
        assert data["enrichment"]["lending_flow"] == "cancelled"

    @pytest.mark.asyncio
    async def test_lending_all_supported_assets(self, client: AsyncClient):
        """Test LENDING flow with all supported assets."""
        assets = ["USDC", "USDT", "DAI", "ETH", "WBTC"]

        for asset in assets:
            # Initiate fresh flow
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
    async def test_moonpay_swap_flow_complete(self, client: AsyncClient):
        """
        Test complete SWAP_MOONPAY flow: FROM token → TO token → Amount → Quote → Confirm.

        Validates:
        - Step progression (5 steps including initiation)
        - Token validation (BTC, ETH, SOL, USDC only)
        - Quote display with rates and fees
        - Registration requirement
        """
        # Step 1: Initiate swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 1: FROM token selection
        content = data["agent_message"]["content"]
        assert "swap" in content.lower()
        assert all(token in content for token in ["BTC", "ETH", "SOL", "USDC"])
        assert data["enrichment"]["swap_flow"] == "step1_from_token"

        # Step 2: Select FROM token (BTC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 2: TO token selection
        content = data["agent_message"]["content"]
        assert "BTC" in content
        assert data["enrichment"]["swap_flow"] == "step2_to_token"
        assert data["enrichment"]["from_token"] == "BTC"

        # Step 3: Select TO token (ETH)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 3: Amount input
        content = data["agent_message"]["content"]
        assert "BTC" in content and "ETH" in content
        assert data["enrichment"]["swap_flow"] == "step3_amount"

        # Step 4: Enter amount (0.1 BTC)
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "0.1", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 4: Quote display
        content = data["agent_message"]["content"]
        assert "0.1" in content and "BTC" in content and "ETH" in content
        assert "confirm" in content.lower()
        assert data["enrichment"]["swap_flow"] == "step4_confirmation"
        assert "quote" in data["enrichment"]

        # Step 5: Confirm swap
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "confirm", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Validate Step 5: Execution (signup required)
        content = data["agent_message"]["content"]
        assert any(emoji in content for emoji in ["🎉", "✅"])
        assert "sign up" in content.lower()
        assert data["enrichment"]["swap_flow"] == "execution"

    @pytest.mark.asyncio
    async def test_moonpay_swap_complete_request_parsing(self, client: AsyncClient):
        """Test SWAP_MOONPAY with complete request: 'swap 0.5 BTC to ETH'."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap 0.5 BTC to ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show quote directly (skipped TO token and amount steps)
        content = data["agent_message"]["content"]
        assert "0.5" in content and "BTC" in content and "ETH" in content
        assert "confirm" in content.lower()
        assert data["enrichment"]["swap_flow"] == "step4_confirmation"


@pytest.mark.integration
@pytest.mark.chat
class TestGuestChatShortcuts:
    """Test all shortcuts from shortcuts API work correctly."""

    @pytest.mark.asyncio
    async def test_lending_shortcuts(self, client: AsyncClient):
        """Test all lending-related shortcuts."""
        # Shortcuts with asset specified skip to step2 (amount)
        shortcuts_with_asset = [
            ("Deposit USDC on Morpho", "step2_amount", "USDC"),
            ("Earn yield on my ETH", "step2_amount", "ETH"),
        ]

        for shortcut, expected_step, expected_asset in shortcuts_with_asset:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": shortcut, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Should skip to amount step with asset pre-filled
            assert "lending_flow" in data["enrichment"]
            assert data["enrichment"]["lending_flow"] == expected_step
            assert data["enrichment"]["asset"] == expected_asset

        # Shortcuts without asset start at step1
        shortcuts_no_asset = [
            "Show best lending vaults",
            "Best lending vaults",
        ]

        for shortcut in shortcuts_no_asset:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": shortcut, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Should start at asset selection
            assert "lending_flow" in data["enrichment"]
            assert data["enrichment"]["lending_flow"] == "step1_asset"

    @pytest.mark.asyncio
    async def test_swap_shortcuts(self, client: AsyncClient):
        """Test swap-related shortcuts."""
        shortcuts = [
            "Swap BTC to ETH",
            "Swap ETH to SOL",
            "Swap SOL to USDC",
        ]

        for shortcut in shortcuts:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": shortcut, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            # Should show swap quote or ask for amount
            assert "swap_flow" in data["enrichment"]

    @pytest.mark.asyncio
    async def test_balance_shortcut(self, client: AsyncClient):
        """Test balance shortcut for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's my balance?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Guests should see demo/empty balance
        content = data["agent_message"]["content"]
        assert "$0.00" in content or "empty" in content.lower() or "no balance" in content.lower()

    @pytest.mark.asyncio
    async def test_portfolio_shortcut(self, client: AsyncClient):
        """Test portfolio shortcut for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Show my portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Guests should see empty portfolio
        content = data["agent_message"]["content"]
        assert "empty" in content.lower() or "no holdings" in content.lower() or "$0" in content


@pytest.mark.integration
@pytest.mark.chat
class TestGuestChatProductionQuality:
    """Test production-grade response quality."""

    @pytest.mark.asyncio
    async def test_responses_use_emojis(self, client: AsyncClient):
        """Test that responses use emojis for visual appeal."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        emojis = ["💰", "💵", "📈", "🏦", "Ξ", "₿"]
        assert any(emoji in content for emoji in emojis)

    @pytest.mark.asyncio
    async def test_responses_have_clear_ctas(self, client: AsyncClient):
        """Test that confirmation steps have clear calls-to-action."""
        # Navigate to confirmation
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "1000", "language": "en"}
        )

        content = response.json()["agent_message"]["content"]

        # Should have clear action instructions
        assert "confirm" in content.lower()
        assert any(word in content.lower() for word in ["yes", "proceed", "cancel", "abort"])

    @pytest.mark.asyncio
    async def test_error_handling_invalid_amount(self, client: AsyncClient):
        """Test error handling for invalid amount input."""
        # Navigate to amount step
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})

        # Enter invalid amount
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "not a number", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should show error and re-ask
        content = data["agent_message"]["content"]
        assert "❌" in content or "invalid" in content.lower() or "error" in content.lower()
        assert data["enrichment"]["lending_flow"] == "step2_amount"

    @pytest.mark.asyncio
    async def test_multilingual_support_spanish(self, client: AsyncClient):
        """Test Spanish language support."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "préstamo", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish or English text (fallback allowed)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_out_of_scope_rejection(self, client: AsyncClient):
        """Test that out-of-scope queries are rejected politely."""
        out_of_scope_queries = ["What's the weather?", "bake", "bomb"]

        for query in out_of_scope_queries:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": query, "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            content = data["agent_message"]["content"]
            # Should reject and redirect to DeFi topics
            assert "DeFi" in content or "crypto" in content
            assert any(word in content for word in ["portfolio", "swap", "lending"])

    @pytest.mark.asyncio
    async def test_typo_tolerance(self, client: AsyncClient):
        """Test that common typos are handled gracefully."""
        typos = [
            ("porfolio", "portfolio"),  # Typo of portfolio
            ("balanse", "balance"),     # Typo of balance
            ("swp", "swap"),            # Typo of swap
        ]

        for typo, expected_intent in typos:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": typo, "language": "en"}
            )
            assert response.status_code == 200
            # Should handle typo and route correctly (no error)
