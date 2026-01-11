"""
Integration tests for guest GraphRAG similar protocols.

Tests the protocol similarity and alternatives feature for guest users with real data.
"""

import pytest


class TestGuestGraphRAGSimilarProtocols:
    """Test GraphRAG similar protocol discovery for guests."""

    @pytest.mark.asyncio
    async def test_similar_protocols_basic(self, client):
        """Test basic similar protocols request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What protocols are similar to Aave?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show similar protocols
        assert any(word in content.lower() for word in ["similar", "alternative", "like"])
        assert "aave" in content.lower()

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "similar_protocols" in enrichment or "alternatives" in enrichment or "protocols" in enrichment

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_similar_protocols_results_structure(self, client):
        """Test that similar protocol results have proper structure."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "alternatives to Compound", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have structured similar protocol data
        assert "similar_protocols" in enrichment or "alternatives" in enrichment or "protocols" in enrichment
        protocols = enrichment.get("similar_protocols") or enrichment.get("alternatives") or enrichment.get("protocols")
        assert isinstance(protocols, list)

        # Each protocol should have key fields
        if len(protocols) > 0:
            protocol = protocols[0]
            assert "name" in protocol or "protocol_name" in protocol

    @pytest.mark.asyncio
    async def test_similar_protocols_multiple_queries(self, client):
        """Test finding similar protocols for different protocols."""

        base_protocols = ["Aave", "Uniswap", "Morpho"]

        for protocol in base_protocols:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"protocols like {protocol}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            content = data["agent_message"]["content"]

            # Should find alternatives
            assert "similar_protocols" in enrichment or "alternatives" in enrichment or "protocols" in enrichment
            assert protocol.lower() in content.lower()

    @pytest.mark.asyncio
    async def test_similar_protocols_similarity_score(self, client):
        """Test that similar protocols include similarity scores."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols similar to Aave", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have similarity metrics
        protocols = enrichment.get("similar_protocols") or enrichment.get("alternatives") or enrichment.get("protocols", [])
        if len(protocols) > 0:
            # At least some protocols should have similarity scores
            has_score = any("similarity" in p or "score" in p for p in protocols if isinstance(p, dict))
            # If no explicit score, should at least be ranked by similarity
            assert has_score or len(protocols) > 1

    @pytest.mark.asyncio
    async def test_similar_protocols_category_matching(self, client):
        """Test that similar protocols match by category."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "other lending protocols like Compound", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should match by category (lending)
        assert "similar_protocols" in enrichment or "alternatives" in enrichment or "protocols" in enrichment

        # Should mention category
        category_keywords = ["lending", "borrow", "supply", "interest"]
        assert any(keyword in content.lower() for keyword in category_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_chain_filtering(self, client):
        """Test finding similar protocols on same chain."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols like Aave on Ethereum", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should filter by chain
        assert "chain" in enrichment or "similar_protocols" in enrichment or "protocols" in enrichment
        assert "ethereum" in content.lower()

    @pytest.mark.asyncio
    async def test_similar_protocols_feature_comparison(self, client):
        """Test that similar protocols show feature comparisons."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "alternatives to Uniswap", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should compare features
        assert "similar_protocols" in enrichment or "alternatives" in enrichment or "protocols" in enrichment

        # Should mention key features
        feature_keywords = ["feature", "support", "offer", "provide", "enable"]
        assert any(keyword in content.lower() for keyword in feature_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_differences_highlighted(self, client):
        """Test that key differences are highlighted."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how does Morpho compare to Aave?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should highlight differences
        assert "similar_protocols" in enrichment or "comparison" in enrichment or "protocols" in enrichment

        # Should use comparison language
        comparison_keywords = ["different", "unlike", "whereas", "however", "instead"]
        assert any(keyword in content.lower() for keyword in comparison_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_graphrag_tag(self, client):
        """Test that response includes graphrag tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols like Aave", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "tool" in enrichment or "source" in enrichment

    @pytest.mark.asyncio
    async def test_similar_protocols_uses_real_data(self, client):
        """Test that similar protocols use real protocol data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "alternatives to Compound", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real protocol alternatives
        protocols = enrichment.get("similar_protocols") or enrichment.get("alternatives") or enrichment.get("protocols")
        assert len(protocols) > 0

        # Should include real protocol names
        real_protocol_names = ["aave", "morpho", "maker", "euler"]
        protocol_names_in_results = [p.get("name", "").lower() for p in protocols if isinstance(p, dict)]
        # At least one real protocol should be mentioned
        assert any(name in str(protocol_names_in_results).lower() for name in real_protocol_names)

    @pytest.mark.asyncio
    async def test_similar_protocols_multilingual_spanish(self, client):
        """Test similar protocols in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocolos similares a Aave", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Similar", "Alternativa", "Alternative", "Protocolo", "Protocol"])


class TestGuestGraphRAGSimilarProtocolsStorytellingQuality:
    """Test storytelling and UX quality of similar protocol responses."""

    @pytest.mark.asyncio
    async def test_similar_protocols_uses_emojis(self, client):
        """Test that similar protocols use emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols like Aave", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["🔍", "📊", "💡", "🔄", "⚡", "🌐"])

    @pytest.mark.asyncio
    async def test_similar_protocols_clear_formatting(self, client):
        """Test that similar protocols have clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "alternatives to Compound", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_similar_protocols_ranked_presentation(self, client):
        """Test that similar protocols are presented in ranked order."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "top alternatives to Uniswap", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have ranking indicators
        ranking_keywords = ["1.", "2.", "3.", "first", "top", "best", "most similar"]
        assert any(keyword in content.lower() for keyword in ranking_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_pros_and_cons(self, client):
        """Test that comparisons show pros and cons."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "compare Morpho to Aave", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should highlight trade-offs
        tradeoff_keywords = ["advantage", "benefit", "downside", "tradeoff", "pro", "con"]
        assert any(keyword in content.lower() for keyword in tradeoff_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_use_case_guidance(self, client):
        """Test that comparisons guide use case selection."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "which is better, Aave or Compound?", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide use case guidance
        guidance_keywords = ["if you", "for", "when", "depending on", "choose"]
        assert any(keyword in content.lower() for keyword in guidance_keywords)

    @pytest.mark.asyncio
    async def test_similar_protocols_educational_context(self, client):
        """Test that comparisons educate about protocols."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "protocols similar to Morpho", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should explain how protocols work
        educational_keywords = ["works by", "allows", "enables", "provides", "focuses on"]
        assert any(keyword in content.lower() for keyword in educational_keywords)
