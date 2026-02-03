"""
Integration tests for guest receive flow.

Tests the receive/deposit inquiry with storytelling enhancements.
"""

import pytest


class TestGuestReceiveFlow:
    """Test receive inquiry flow."""

    @pytest.mark.asyncio
    async def test_receive_response_structure(self, client):
        """Test receive response has correct structure."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]
        assert "📥" in content or "Receive" in content
        assert data["registration_required"]["required"] is True

        # Verify enrichment data
        assert "enrichment" in data
        assert "addresses" in data["enrichment"]

    @pytest.mark.asyncio
    async def test_receive_shows_demo_addresses(self, client):
        """Test that receive shows demo addresses for guests."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should show demo mode indicator
        assert (
            "Demo" in content
            or "demo" in content.lower()
            or "example" in content.lower()
        )

        # Should show multiple network addresses
        networks = ["Ethereum", "Bitcoin", "Solana"]
        networks_found = sum(1 for network in networks if network in content)
        assert networks_found >= 3, "Should show at least 3 different networks"

        # Should show sample addresses
        assert "0x" in content  # Ethereum address format
        assert "bc1" in content or "..." in content  # Bitcoin address format

    @pytest.mark.asyncio
    async def test_receive_has_instructions(self, client):
        """Test that receive includes how-to instructions."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should have instructions
        instruction_keywords = [
            "how to",
            "share",
            "address",
            "sender",
            "wait",
            "confirm",
        ]
        instructions_found = sum(
            1 for keyword in instruction_keywords if keyword in content.lower()
        )
        assert instructions_found >= 3, "Should include clear instructions"

    @pytest.mark.asyncio
    async def test_receive_has_security_warning(self, client):
        """Test that receive includes security warnings."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should have security warning
        assert "⚠️" in content or "Important" in content or "WARNING" in content.upper()
        assert "verify" in content.lower() or "network" in content.lower()

    @pytest.mark.asyncio
    async def test_receive_has_signup_cta(self, client):
        """Test that receive includes signup CTA for guests."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should have signup CTA
        assert any(
            phrase in content.lower()
            for phrase in ["sign up", "signup", "get", "register"]
        )
        assert "/signup" in content

    @pytest.mark.asyncio
    async def test_receive_multilingual_spanish(self, client):
        """Test receive in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Spanish text or fallback
        assert any(
            word in content for word in ["Recibir", "Receive", "dirección", "address"]
        )

    @pytest.mark.asyncio
    async def test_receive_multilingual_portuguese(self, client):
        """Test receive in Portuguese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receber", "language": "pt"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert any(
            word in content for word in ["Receber", "Receive", "endereço", "address"]
        )

    @pytest.mark.asyncio
    async def test_receive_multilingual_french(self, client):
        """Test receive in French."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "recevoir", "language": "fr"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        assert any(
            word in content for word in ["Recevoir", "Receive", "adresse", "address"]
        )

    @pytest.mark.asyncio
    async def test_receive_multilingual_chinese(self, client):
        """Test receive in Chinese."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "接收", "language": "zh"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should contain Chinese characters or fallback
        assert "接收" in content or "Receive" in content


class TestGuestReceiveStorytellingQuality:
    """Test storytelling and UX quality of receive responses."""

    @pytest.mark.asyncio
    async def test_response_uses_emojis(self, client):
        """Test that response uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        emoji_indicators = ["📥", "🔷", "₿", "◎", "⚠️"]
        emojis_found = sum(1 for emoji in emoji_indicators if emoji in content)
        assert emojis_found >= 3, "Should use multiple emojis for visual appeal"

    @pytest.mark.asyncio
    async def test_response_has_clear_structure(self, client):
        """Test that response has clear visual structure."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have section dividers
        assert "━" in content or "---" in content or "\n\n" in content

        # Should have numbered steps or clear sections
        assert "1" in content or "2" in content or "**" in content

    @pytest.mark.asyncio
    async def test_response_is_helpful(self, client):
        """Test that response has helpful tone."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have helpful/instructive language
        helpful_phrases = ["Ready", "Here's how", "You", "your"]
        has_helpful = any(phrase in content for phrase in helpful_phrases)
        assert has_helpful, "Should have helpful tone"

    @pytest.mark.asyncio
    async def test_addresses_are_visually_formatted(self, client):
        """Test that addresses are clearly formatted."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "receive", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Addresses should be in code blocks or clearly marked
        assert "`" in content or "**" in content, (
            "Addresses should be visually distinct"
        )
