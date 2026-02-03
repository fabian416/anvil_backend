"""
Integration tests for guest GraphRAG protocol risk assessment.

Tests the protocol security and risk analysis feature for guest users with real data.
"""

import pytest


class TestGuestGraphRAGRiskAssessment:
    """Test GraphRAG protocol risk assessment for guests."""

    @pytest.mark.asyncio
    async def test_risk_assessment_basic(self, client):
        """Test basic protocol risk assessment request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What are the risks of using Aave?", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show risk analysis
        assert any(word in content.lower() for word in ["risk", "security", "safe"])
        assert "aave" in content.lower()

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert (
            "risk_score" in enrichment
            or "risks" in enrichment
            or "assessment" in enrichment
        )

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_risk_assessment_score(self, client):
        """Test that risk assessment includes risk score."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "assess risk for Compound protocol", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have risk score
        assert "risk_score" in enrichment or "score" in enrichment

        # Should mention risk level
        risk_levels = ["low", "medium", "high", "safe", "risky"]
        assert any(level in content.lower() for level in risk_levels)

    @pytest.mark.asyncio
    async def test_risk_assessment_categories(self, client):
        """Test that risk assessment covers multiple categories."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "security analysis of Morpho", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have risk categories
        assert (
            "risks" in enrichment
            or "categories" in enrichment
            or "assessment" in enrichment
        )

        # Should mention risk types
        risk_types = [
            "smart contract",
            "audit",
            "centralization",
            "liquidity",
            "oracle",
        ]
        assert any(risk_type in content.lower() for risk_type in risk_types)

    @pytest.mark.asyncio
    async def test_risk_assessment_multiple_protocols(self, client):
        """Test risk assessment for different protocols."""

        protocols = ["Aave", "Compound", "Uniswap"]

        for protocol in protocols:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"risk assessment for {protocol}", "language": "en"},
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            content = data["agent_message"]["content"]

            # Should assess the specific protocol
            assert protocol.lower() in content.lower()
            assert "risk" in enrichment or "assessment" in enrichment

    @pytest.mark.asyncio
    async def test_risk_assessment_audit_history(self, client):
        """Test that assessment includes audit information."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "is Aave audited and safe?", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have audit information
        assert (
            "audits" in enrichment
            or "audit_history" in enrichment
            or "assessment" in enrichment
        )

        # Should mention audits
        audit_keywords = ["audit", "audited", "security review", "verified"]
        assert any(keyword in content.lower() for keyword in audit_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_exploit_history(self, client):
        """Test that assessment includes exploit/incident history."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "has Compound been hacked?", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have incident history
        assert (
            "exploits" in enrichment
            or "incidents" in enrichment
            or "assessment" in enrichment
        )

        # Should mention security history
        security_keywords = ["hack", "exploit", "incident", "vulnerability", "security"]
        assert any(keyword in content.lower() for keyword in security_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_tvl_correlation(self, client):
        """Test that assessment considers TVL as risk indicator."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "risk analysis for Morpho protocol", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should consider TVL
        assert "tvl" in enrichment or "assessment" in enrichment

        # Should mention market adoption
        adoption_keywords = ["tvl", "adoption", "users", "market", "established"]
        assert any(keyword in content.lower() for keyword in adoption_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_recommendations(self, client):
        """Test that assessment provides risk mitigation recommendations."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how safe is Uniswap?", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have recommendations
        assert (
            "recommendations" in enrichment
            or "suggestions" in enrichment
            or "assessment" in enrichment
        )

        # Should suggest risk management
        recommendation_keywords = [
            "consider",
            "recommend",
            "suggest",
            "diversify",
            "limit",
        ]
        assert any(keyword in content.lower() for keyword in recommendation_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_graphrag_tag(self, client):
        """Test that response includes graphrag tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "risk analysis for Aave", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "tool" in enrichment or "source" in enrichment

    @pytest.mark.asyncio
    async def test_risk_assessment_uses_real_data(self, client):
        """Test that assessment uses real protocol data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "security assessment for Compound", "language": "en"},
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real assessment data
        assert (
            "risks" in enrichment
            or "assessment" in enrichment
            or "risk_score" in enrichment
        )

        # Data should be structured
        assessment_data = enrichment.get("risks") or enrichment.get("assessment")
        if assessment_data:
            assert isinstance(assessment_data, (list, dict, str))

    @pytest.mark.asyncio
    async def test_risk_assessment_multilingual_spanish(self, client):
        """Test risk assessment in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "evaluación de riesgo para Aave", "language": "es"},
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(
            word in content for word in ["Riesgo", "Risk", "Seguridad", "Security"]
        )


class TestGuestGraphRAGRiskAssessmentStorytellingQuality:
    """Test storytelling and UX quality of risk assessment responses."""

    @pytest.mark.asyncio
    async def test_risk_assessment_uses_emojis(self, client):
        """Test that risk assessment uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "risk analysis for Aave", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["🔒", "⚠️", "✅", "🛡️", "🔍", "📊"])

    @pytest.mark.asyncio
    async def test_risk_assessment_clear_formatting(self, client):
        """Test that risk assessment has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "security analysis for Compound", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_risk_assessment_balanced_perspective(self, client):
        """Test that assessment provides balanced view."""

        response = await client.post(
            "/api/v1/guest/chat", json={"content": "is Morpho safe?", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide balanced analysis
        balance_keywords = ["however", "although", "while", "but", "also"]
        assert any(keyword in content.lower() for keyword in balance_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_educational_context(self, client):
        """Test that assessment educates about risks."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what are the risks of Uniswap?", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should explain risk concepts
        educational_keywords = [
            "means",
            "refers to",
            "involves",
            "can lead to",
            "because",
        ]
        assert any(keyword in content.lower() for keyword in educational_keywords)

    @pytest.mark.asyncio
    async def test_risk_assessment_disclaimers(self, client):
        """Test that assessment includes appropriate disclaimers."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "risk assessment for Aave", "language": "en"},
        )
        content = response.json()["agent_message"]["content"]

        # Should have disclaimer language
        disclaimer_keywords = ["dyor", "not financial advice", "own research", "risk"]
        assert any(keyword in content.lower() for keyword in disclaimer_keywords)
