"""
Integration tests for guest Hunter AI portfolio optimization.

Tests the portfolio optimization suggestion feature for guest users with real data.
"""

import pytest


class TestGuestHunterPortfolioOptimization:
    """Test Hunter AI portfolio optimization for guests."""

    @pytest.mark.asyncio
    async def test_portfolio_optimization_basic(self, client):
        """Test basic portfolio optimization request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "How can I optimize my crypto portfolio?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show optimization suggestions
        assert any(word in content.lower() for word in ["optimize", "portfolio", "allocation", "diversif"])

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "recommendations" in enrichment or "allocation" in enrichment or "optimization" in enrichment

        # Guests can access without registration (but need signup for execution)
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_portfolio_allocation_recommendations(self, client):
        """Test that optimization shows allocation recommendations."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization recommendations", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have allocation suggestions
        assert "allocation" in enrichment or "recommendations" in enrichment

        # Should mention percentages or weights
        allocation_keywords = ["%", "percent", "weight", "allocation", "split", "ratio"]
        assert any(keyword in content.lower() for keyword in allocation_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_risk_tolerance_levels(self, client):
        """Test optimization for different risk tolerance levels."""

        risk_levels = ["conservative", "moderate", "aggressive"]

        for risk in risk_levels:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"{risk} portfolio optimization", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            content = data["agent_message"]["content"]

            # Should acknowledge risk level
            assert risk in content.lower() or "risk" in content.lower()

    @pytest.mark.asyncio
    async def test_portfolio_diversification_suggestions(self, client):
        """Test that optimization includes diversification advice."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio diversification strategy", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have diversification recommendations
        assert "diversification" in enrichment or "recommendations" in enrichment

        # Should mention diversification
        diversification_keywords = ["diversif", "spread", "distribute", "variety", "multiple"]
        assert any(keyword in content.lower() for keyword in diversification_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_asset_recommendations(self, client):
        """Test that optimization recommends specific assets."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "crypto portfolio recommendations", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have asset recommendations
        assert "assets" in enrichment or "tokens" in enrichment or "recommendations" in enrichment

        # Should mention specific tokens
        token_keywords = ["btc", "eth", "sol", "usdc", "bitcoin", "ethereum"]
        assert any(keyword in content.lower() for keyword in token_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_rebalancing_advice(self, client):
        """Test that optimization includes rebalancing recommendations."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio rebalancing strategy", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have rebalancing advice
        assert "rebalancing" in enrichment or "recommendations" in enrichment

        # Should mention rebalancing
        rebalancing_keywords = ["rebalanc", "adjust", "reallocat", "shift", "modify"]
        assert any(keyword in content.lower() for keyword in rebalancing_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_risk_metrics(self, client):
        """Test that optimization shows risk metrics."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "optimize portfolio risk", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have risk metrics
        assert "risk_metrics" in enrichment or "risk" in enrichment or "optimization" in enrichment

        # Should mention risk concepts
        risk_keywords = ["volatility", "risk", "sharpe", "drawdown", "correlation"]
        assert any(keyword in content.lower() for keyword in risk_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_expected_returns(self, client):
        """Test that optimization shows expected return projections."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization returns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have return projections
        assert "expected_returns" in enrichment or "returns" in enrichment or "optimization" in enrichment

        # Should mention returns
        return_keywords = ["return", "yield", "apy", "gain", "performance"]
        assert any(keyword in content.lower() for keyword in return_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_hunter_tool_tag(self, client):
        """Test that response includes hunter_tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "portfolio_optimizer"

    @pytest.mark.asyncio
    async def test_portfolio_uses_real_market_data(self, client):
        """Test that optimization uses real market data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "crypto portfolio recommendations", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real recommendations based on market data
        assert "recommendations" in enrichment or "allocation" in enrichment
        recommendations = enrichment.get("recommendations") or enrichment.get("allocation")
        assert isinstance(recommendations, (list, dict))

    @pytest.mark.asyncio
    async def test_portfolio_multilingual_spanish(self, client):
        """Test portfolio optimization in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "optimización de cartera cripto", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Cartera", "Portfolio", "Optimización", "Optimization"])


class TestGuestHunterPortfolioOptimizationStorytellingQuality:
    """Test storytelling and UX quality of portfolio optimization responses."""

    @pytest.mark.asyncio
    async def test_portfolio_uses_emojis(self, client):
        """Test that optimization uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["💼", "📊", "📈", "⚖️", "🎯", "💰"])

    @pytest.mark.asyncio
    async def test_portfolio_clear_formatting(self, client):
        """Test that optimization has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "crypto portfolio recommendations", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_portfolio_clear_percentages(self, client):
        """Test that allocation percentages are clearly shown."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio allocation strategy", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should show percentages
        assert "%" in content or "percent" in content.lower()

    @pytest.mark.asyncio
    async def test_portfolio_actionable_steps(self, client):
        """Test that optimization provides actionable steps."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how to optimize portfolio", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have action steps
        action_keywords = ["allocate", "invest", "consider", "include", "add", "reduce"]
        assert any(keyword in content.lower() for keyword in action_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_risk_education(self, client):
        """Test that optimization educates about risk."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization strategy", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should educate about risk
        educational_keywords = ["risk", "diversification", "volatility", "balance", "protect"]
        assert any(keyword in content.lower() for keyword in educational_keywords)

    @pytest.mark.asyncio
    async def test_portfolio_signup_cta(self, client):
        """Test that optimization includes signup CTA for execution."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio optimization", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should mention signing up for implementation
        signup_keywords = ["sign up", "register", "create account", "get started"]
        assert any(keyword in content.lower() for keyword in signup_keywords)
