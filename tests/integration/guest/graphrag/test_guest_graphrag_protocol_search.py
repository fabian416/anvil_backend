"""
Integration tests for guest GraphRAG protocol search.

Tests the protocol search and comparison feature for guest users with real data.
"""

import pytest


class TestGuestGraphRAGProtocolSearch:
    """Test GraphRAG protocol search for guests."""

    @pytest.mark.asyncio
    async def test_protocol_search_basic(self, client):
        """Test basic protocol search request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Find me DeFi lending protocols", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show protocol results
        assert any(word in content.lower() for word in ["protocol", "lending", "defi"])

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "protocols" in enrichment or "results" in enrichment

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_protocol_search_by_category(self, client):
        """Test protocol search by category."""

        categories = ["lending", "dex", "yield", "derivatives"]

        for category in categories:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"find {category} protocols", "language": "en"},
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            content = data["agent_message"]["content"]

            # Should have protocol results
            assert "protocols" in enrichment or "results" in enrichment

            # Should mention the category
            assert category in content.lower()

    @pytest.mark.asyncio
    async def test_protocol_search_by_chain(self, client):
        """Test protocol search filtered by blockchain."""

        chains = ["ethereum", "polygon", "arbitrum"]

        for chain in chains:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"lending protocols on {chain}", "language": "en"},
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            content = data["agent_message"]["content"]

            # Should filter by chain
            assert "chain" in enrichment or "protocols" in enrichment
            assert chain.lower() in content.lower()

    @pytest.mark.asyncio
    async def test_protocol_search_results_structure(self, client):
        """Test that protocol results have proper structure."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "top DeFi protocols", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have structured protocol data
        assert "protocols" in enrichment
        protocols = enrichment["protocols"]
        assert isinstance(protocols, list)

        # Each protocol should have key fields
        if len(protocols) > 0:
            protocol = protocols[0]
            assert "name" in protocol or "protocol_name" in protocol
            assert "tvl" in protocol or "category" in protocol

    @pytest.mark.asyncio
    async def test_protocol_search_comparison(self, client):
        """Test comparing multiple protocols."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "compare Aave and Compound", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have comparison data
        assert "protocols" in enrichment or "comparison" in enrichment

        # Should mention both protocols
        assert "aave" in content.lower()
        assert "compound" in content.lower()

    @pytest.mark.asyncio
    async def test_protocol_search_tvl_data(self, client):
        """Test that protocol results include TVL data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols with highest TVL", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have TVL information
        assert "protocols" in enrichment

        # Should mention TVL in content
        tvl_keywords = ["tvl", "total value locked", "liquidity", "billion", "million"]
        assert any(keyword in content.lower() for keyword in tvl_keywords)

    @pytest.mark.asyncio
    async def test_protocol_search_features(self, client):
        """Test that protocol results include feature information."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending protocols with flash loans", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have feature data
        assert "protocols" in enrichment or "features" in enrichment

        # Should mention features
        assert "flash loan" in content.lower() or "feature" in content.lower()

    @pytest.mark.asyncio
    async def test_protocol_search_graphrag_tag(self, client):
        """Test that response includes graphrag tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "find DeFi protocols", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "tool" in enrichment or "source" in enrichment

    @pytest.mark.asyncio
    async def test_protocol_search_uses_real_data(self, client):
        """Test that protocol search uses real protocol data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "top lending protocols", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real protocol data
        assert "protocols" in enrichment
        protocols = enrichment["protocols"]
        assert len(protocols) > 0

        # Should have real protocol names
        real_protocol_names = ["aave", "compound", "morpho", "maker", "uniswap"]
        protocol_names_in_results = [
            p.get("name", "").lower() for p in protocols if isinstance(p, dict)
        ]
        assert any(
            name in str(protocol_names_in_results).lower()
            for name in real_protocol_names
        )

    @pytest.mark.asyncio
    async def test_protocol_search_multilingual_spanish(self, client):
        """Test protocol search in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "buscar protocolos DeFi", "language": "es"},
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Protocolo", "Protocol", "DeFi"])


class TestGuestGraphRAGProtocolSearchStorytellingQuality:
    """Test storytelling and UX quality of protocol search responses."""

    @pytest.mark.asyncio
    async def test_protocol_search_uses_emojis(self, client):
        """Test that protocol search uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "find lending protocols", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["🏦", "💰", "📊", "🔍", "⚡", "🌐"])

    @pytest.mark.asyncio
    async def test_protocol_search_clear_formatting(self, client):
        """Test that protocol results have clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "top DeFi protocols", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_protocol_search_clear_comparisons(self, client):
        """Test that protocol comparisons are clearly presented."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "compare lending protocols", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should have comparison language
        comparison_keywords = [
            "vs",
            "versus",
            "compared to",
            "while",
            "whereas",
            "difference",
        ]
        assert any(keyword in content.lower() for keyword in comparison_keywords)

    @pytest.mark.asyncio
    async def test_protocol_search_educational_context(self, client):
        """Test that protocol results include educational context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what are the best DeFi protocols", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should explain protocols
        educational_keywords = [
            "allows",
            "enables",
            "provides",
            "offers",
            "specializes",
        ]
        assert any(keyword in content.lower() for keyword in educational_keywords)

    @pytest.mark.asyncio
    async def test_protocol_search_actionable_next_steps(self, client):
        """Test that search results suggest next steps."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "find yield farming protocols", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should suggest actions
        action_keywords = ["explore", "check out", "consider", "learn more", "try"]
        assert any(keyword in content.lower() for keyword in action_keywords)
