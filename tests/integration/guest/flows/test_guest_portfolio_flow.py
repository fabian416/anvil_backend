"""
Integration tests for guest portfolio display flow.

Tests the portfolio view showing demo holdings for guests.
"""

import pytest


class TestGuestPortfolioFlow:
    """Test portfolio display flow for guests."""

    @pytest.mark.asyncio
    async def test_portfolio_displays_demo_holdings(self, client):
        """Test that portfolio shows demo holdings for guests."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show portfolio title
        assert "💼" in content or "Portfolio" in content

        # Should show demo notice
        assert "Demo" in content or "demo" in content.lower()

        # Should show demo holdings (USDC, ETH, BTC, SOL, MATIC)
        assert "USDC" in content
        assert "ETH" in content or "Ethereum" in content
        assert "BTC" in content or "Bitcoin" in content
        assert "SOL" in content or "Solana" in content
        assert "MATIC" in content or "Polygon" in content

        # Should show total value
        assert "$" in content
        assert "total" in content.lower() or "value" in content.lower()

        # Should show signup CTA
        assert "sign up" in content.lower() or "signup" in content.lower()

        # Verify enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "portfolio" in enrichment
        assert "balances" in enrichment

        # Verify registration required
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_portfolio_shows_total_value(self, client):
        """Test that portfolio shows total portfolio value."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show my portfolio", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show total value in content
        assert "$" in content
        assert any(word in content.lower() for word in ["total", "value", "portfolio"])

        # Should show total value in enrichment
        assert "portfolio" in enrichment
        assert "total_value_usd" in enrichment["portfolio"]
        assert enrichment["portfolio"]["total_value_usd"] > 0

    @pytest.mark.asyncio
    async def test_portfolio_shows_24h_change(self, client):
        """Test that portfolio shows 24h performance change."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show 24h change indicator
        assert "24h" in content.lower() or "24 h" in content.lower()
        assert any(emoji in content for emoji in ["📈", "📉", "➡️"])

        # Should have 24h change in enrichment
        assert "portfolio" in enrichment
        assert "change_24h_usd" in enrichment["portfolio"]
        assert "change_24h_pct" in enrichment["portfolio"]

    @pytest.mark.asyncio
    async def test_portfolio_shows_holdings_breakdown(self, client):
        """Test that portfolio shows detailed holdings breakdown."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show holdings section
        assert "holdings" in content.lower() or "assets" in content.lower()

        # Should show individual token amounts
        assert any(word in content for word in ["Amount", "amount", "balance"])

        # Should show individual token values
        assert "$" in content

        # Should show allocation percentages
        assert "%" in content

        # Should have balances in enrichment
        assert "balances" in enrichment
        assert len(enrichment["balances"]) > 0

        # Each balance should have required fields
        for balance in enrichment["balances"]:
            assert "token" in balance
            assert "amount" in balance
            assert "value_usd" in balance
            assert "change_24h" in balance

    @pytest.mark.asyncio
    async def test_portfolio_shows_performance_highlights(self, client):
        """Test that portfolio shows performance highlights."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show performance section
        assert any(
            word in content.lower()
            for word in ["performance", "highlights", "top performer"]
        )

        # Should identify top performer
        assert "portfolio" in enrichment
        assert "top_performer" in enrichment["portfolio"]
        top_performer = enrichment["portfolio"]["top_performer"]
        assert "token" in top_performer
        assert "change_24h" in top_performer

    @pytest.mark.asyncio
    async def test_portfolio_shows_diversification(self, client):
        """Test that portfolio shows diversification info."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "my portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should mention diversification
        assert "diversif" in content.lower() or "assets" in content.lower()

        # Should show number of assets
        assert "portfolio" in enrichment
        assert "holdings_count" in enrichment["portfolio"]
        assert enrichment["portfolio"]["holdings_count"] > 0

    @pytest.mark.asyncio
    async def test_portfolio_multilingual_spanish(self, client):
        """Test portfolio in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portafolio", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(
            word in content.lower()
            for word in ["portafolio", "portfolio", "valor", "value"]
        )

    @pytest.mark.asyncio
    async def test_portfolio_multilingual_portuguese(self, client):
        """Test portfolio in Portuguese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "carteira", "language": "pt"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Portuguese or English text (fallback)
        assert any(
            word in content.lower()
            for word in ["portfólio", "portfolio", "valor", "value"]
        )

    @pytest.mark.asyncio
    async def test_portfolio_multilingual_chinese(self, client):
        """Test portfolio in Chinese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "投资组合", "language": "zh"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Chinese or English text (fallback)
        assert any(
            word in content for word in ["投资组合", "Portfolio", "价值", "value"]
        )


class TestGuestPortfolioStorytellingQuality:
    """Test storytelling and UX quality of portfolio responses."""

    @pytest.mark.asyncio
    async def test_portfolio_uses_emojis_for_visual_appeal(self, client):
        """Test that portfolio uses emojis to enhance communication."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert "💼" in content or "💰" in content or "💵" in content

    @pytest.mark.asyncio
    async def test_portfolio_has_clear_signup_cta(self, client):
        """Test that portfolio has clear signup call-to-action."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have clear signup CTA
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert any(
            phrase in content.lower()
            for phrase in ["real portfolio", "your real", "actual"]
        )

    @pytest.mark.asyncio
    async def test_portfolio_shows_clear_formatting(self, client):
        """Test that portfolio has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "portfolio", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text
        assert "━" in content or "---" in content  # Dividers

        # Should show structured sections
        assert "\n\n" in content  # Paragraph breaks
