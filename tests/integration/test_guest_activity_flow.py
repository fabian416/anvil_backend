"""
Integration tests for guest activity/transaction history flow.

Tests the transaction history display showing demo transactions for guests.
"""

import pytest


class TestGuestActivityFlow:
    """Test activity/transaction history display flow for guests."""

    @pytest.mark.asyncio
    async def test_activity_displays_demo_transactions(self, client):
        """Test that activity shows demo transaction history for guests."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show activity title
        assert "📜" in content or "Transaction" in content or "Activity" in content

        # Should show demo notice
        assert "Demo" in content or "demo" in content.lower()

        # Should show transaction types
        assert any(tx_type in content.upper() for tx_type in ["SWAP", "SEND", "RECEIVE", "BUY"])

        # Should show transaction statuses
        assert "✅" in content or "Completed" in content or "completed" in content

        # Should show signup CTA
        assert "sign up" in content.lower() or "signup" in content.lower()

        # Verify enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "transactions" in enrichment
        assert "transaction_count" in enrichment

        # Verify registration required
        assert data["registration_required"]["required"] is True

    @pytest.mark.asyncio
    async def test_activity_shows_transaction_count(self, client):
        """Test that activity shows transaction count."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show my activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show transaction count
        assert "transaction_count" in enrichment
        assert enrichment["transaction_count"] > 0

        # Should mention transactions in content
        assert "transaction" in content.lower()

    @pytest.mark.asyncio
    async def test_activity_shows_transaction_types(self, client):
        """Test that activity displays different transaction types."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show multiple transaction types
        tx_types_found = sum([
            "SWAP" in content,
            "SEND" in content or "SENT" in content,
            "RECEIVE" in content or "RECEIVED" in content,
            "BUY" in content or "BOUGHT" in content,
        ])
        assert tx_types_found >= 2, "Should show at least 2 different transaction types"

        # Should have types in enrichment
        assert "types" in enrichment
        assert len(enrichment["types"]) > 0

    @pytest.mark.asyncio
    async def test_activity_shows_transaction_details(self, client):
        """Test that activity shows detailed transaction information."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "transactions", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show transaction hashes
        assert "0x" in content or "TX" in content

        # Should show timestamps/time info
        assert any(word in content.lower() for word in ["time", "ago", "hour", "day", "minute"])

        # Should have detailed transaction data in enrichment
        assert "transactions" in enrichment
        assert len(enrichment["transactions"]) > 0

        # Each transaction should have required fields
        for tx in enrichment["transactions"]:
            assert "type" in tx
            assert "status" in tx
            assert "timestamp" in tx
            assert "tx_hash" in tx

    @pytest.mark.asyncio
    async def test_activity_shows_swap_transactions(self, client):
        """Test that activity shows swap transaction details."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show swap emojis
        assert "🔄" in content

        # Should have swap transactions in enrichment
        swaps = [tx for tx in enrichment["transactions"] if tx["type"] == "swap"]
        assert len(swaps) > 0

        # Swap transactions should have required fields
        for swap in swaps:
            assert "from_token" in swap
            assert "to_token" in swap
            assert "from_amount" in swap
            assert "to_amount" in swap

    @pytest.mark.asyncio
    async def test_activity_shows_send_receive_transactions(self, client):
        """Test that activity shows send/receive transaction details."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        enrichment = data["enrichment"]

        # Should show send/receive emojis
        assert any(emoji in content for emoji in ["📤", "📥"])

        # Should have send or receive transactions
        send_receive = [
            tx for tx in enrichment["transactions"]
            if tx["type"] in ["send", "receive"]
        ]
        assert len(send_receive) > 0

        # Send/receive transactions should have required fields
        for tx in send_receive:
            assert "token" in tx
            assert "amount" in tx

    @pytest.mark.asyncio
    async def test_activity_shows_time_formatted(self, client):
        """Test that activity shows time in relative format."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should show relative time
        assert any(phrase in content.lower() for phrase in [
            "ago", "hour", "day", "minute", "time"
        ])

    @pytest.mark.asyncio
    async def test_activity_multilingual_spanish(self, client):
        """Test activity in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "actividad", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content.lower() for word in [
            "transacc", "historial", "activity", "transaction"
        ])

    @pytest.mark.asyncio
    async def test_activity_multilingual_portuguese(self, client):
        """Test activity in Portuguese."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "atividade", "language": "pt"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Portuguese or English text (fallback)
        assert any(word in content.lower() for word in [
            "transaç", "histórico", "activity", "transaction"
        ])

    @pytest.mark.asyncio
    async def test_activity_multilingual_chinese(self, client):
        """Test activity in Chinese."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "交易历史", "language": "zh"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Chinese or English text (fallback)
        assert any(word in content for word in [
            "交易", "历史", "Activity", "Transaction"
        ])


class TestGuestActivityStorytellingQuality:
    """Test storytelling and UX quality of activity responses."""

    @pytest.mark.asyncio
    async def test_activity_uses_emojis_for_visual_appeal(self, client):
        """Test that activity uses emojis to enhance communication."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators for transaction types
        assert any(emoji in content for emoji in ["🔄", "📤", "📥", "💳"])

        # Should have status emojis
        assert "✅" in content or "⏳" in content or "❌" in content

    @pytest.mark.asyncio
    async def test_activity_has_clear_signup_cta(self, client):
        """Test that activity has clear signup call-to-action."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have clear signup CTA
        assert "sign up" in content.lower() or "signup" in content.lower()
        assert any(phrase in content.lower() for phrase in [
            "real transactions", "your real", "actual"
        ])

    @pytest.mark.asyncio
    async def test_activity_shows_clear_formatting(self, client):
        """Test that activity has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text
        assert "━" in content or "---" in content  # Dividers

        # Should show structured sections
        assert "\n\n" in content  # Paragraph breaks

    @pytest.mark.asyncio
    async def test_activity_shows_transaction_progression(self, client):
        """Test that activity shows transactions in logical order."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        data = response.json()

        enrichment = data["enrichment"]

        # Should have multiple transactions
        assert "transactions" in enrichment
        assert len(enrichment["transactions"]) > 1

        # Each transaction should have a timestamp
        for tx in enrichment["transactions"]:
            assert "timestamp" in tx

    @pytest.mark.asyncio
    async def test_activity_groups_information_clearly(self, client):
        """Test that activity groups transaction information clearly."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "activity", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should show numbered or bulleted lists
        assert any(marker in content for marker in ["**1.**", "**2.**", "•", "1.", "2."])

        # Should have section headers
        assert "Recent" in content or "History" in content or "Activity" in content
