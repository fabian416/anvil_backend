"""
Integration tests for guest balance flow.

Tests the balance inquiry with storytelling enhancements.
"""

import pytest


class TestGuestBalanceFlow:
    """Test balance inquiry flow."""

    @pytest.mark.asyncio
    async def test_balance_response_structure(self, client):
        """Test balance response has correct structure."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "💰" in content or "Balance" in content
        assert data["registration_required"]["required"] is True

        # Verify enrichment data
        assert "enrichment" in data
        assert "balances" in data["enrichment"]
        assert "total_value" in data["enrichment"]

    @pytest.mark.asyncio
    async def test_balance_shows_demo_balances(self, client):
        """Test that balance shows demo data for guests."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should show demo mode indicator
        assert "Demo" in content or "demo" in content.lower()

        # Should show multiple tokens
        token_indicators = ["USDC", "ETH", "BTC", "SOL"]
        tokens_found = sum(1 for token in token_indicators if token in content)
        assert tokens_found >= 3, "Should show at least 3 different tokens"

        # Should show values in USD
        assert "$" in content

    @pytest.mark.asyncio
    async def test_balance_has_signup_cta(self, client):
        """Test that balance includes signup CTA for guests."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should have signup CTA
        assert any(
            phrase in content.lower()
            for phrase in ["sign up", "signup", "get started", "register"]
        )
        assert "/signup" in content

    @pytest.mark.asyncio
    async def test_balance_multilingual_spanish(self, client):
        """Test balance in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish text or fallback to English
        assert any(
            word in content for word in ["Saldo", "Balance", "Portfolio", "Portafolio"]
        )

    @pytest.mark.asyncio
    async def test_balance_multilingual_portuguese(self, client):
        """Test balance in Portuguese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "saldo", "language": "pt"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert any(
            word in content for word in ["Saldo", "Balance", "Portfólio", "Portfolio"]
        )

    @pytest.mark.asyncio
    async def test_balance_multilingual_french(self, client):
        """Test balance in French."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "solde", "language": "fr"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert any(
            word in content
            for word in ["Solde", "Balance", "Portefeuille", "Portfolio"]
        )

    @pytest.mark.asyncio
    async def test_balance_multilingual_chinese(self, client):
        """Test balance in Chinese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "余额", "language": "zh"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Chinese characters or fallback
        assert "余额" in content or "Balance" in content


class TestGuestBalanceStorytellingQuality:
    """Test storytelling and UX quality of balance responses."""

    @pytest.mark.asyncio
    async def test_response_uses_emojis(self, client):
        """Test that response uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        emoji_indicators = ["💰", "📊", "💵", "Ξ", "₿", "◎"]
        emojis_found = sum(1 for emoji in emoji_indicators if emoji in content)
        assert emojis_found >= 3, "Should use multiple emojis for visual appeal"

    @pytest.mark.asyncio
    async def test_response_has_clear_structure(self, client):
        """Test that response has clear visual structure."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have section dividers
        assert "━" in content or "---" in content or "\n\n" in content

        # Should have clear labels
        assert "Total" in content or "Balances" in content

    @pytest.mark.asyncio
    async def test_response_is_encouraging(self, client):
        """Test that response has encouraging tone."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "balance", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have friendly/encouraging language
        encouraging_phrases = ["Let me", "your", "You", "Ready", "Get started"]
        has_encouraging = any(phrase in content for phrase in encouraging_phrases)
        assert has_encouraging, "Should have encouraging tone"
