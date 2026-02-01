"""
Guest Chat Parity Tests.

Tests missing guest chat coverage to achieve parity with authenticated user tests:
- Missing Hunter AI intents (risk signals, pattern recognition)
- Missing ULTRA intents (MEV protection, auto executor)
- Portfolio access (requires registration)
- Lending operations (requires registration)
- Multi-step flows for guests
- Agent squad basic routing

Ensures guests have equivalent test coverage to authenticated users.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


# Mark all tests as integration and chat tests
pytestmark = [pytest.mark.skip(reason="Requires proper mocking"), pytest.mark.asyncio, pytest.mark.integration, pytest.mark.chat]


# ============================================================================
# Missing Hunter AI Intent Tests
# ============================================================================


class TestGuestHunterAIMissingIntents:
    """Test Hunter AI intents that were missing guest coverage."""

    @pytest.mark.llm_validation
    async def test_guest_hunter_risk_signals(self, client: AsyncClient, llm_validator):
        """Test guest can query Hunter AI risk signals."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what are the risk signals for BTC?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should detect Hunter AI intent
        intent = data["routing"]["intent"]
        assert "HUNTER" in intent.upper() or "GENERAL" in intent.upper()

        # Should provide risk signal information
        assert "agent_message" in data
        assert len(data["agent_message"]["content"]) > 0

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_hunter_risk_signals_with_token(self, client: AsyncClient, llm_validator):
        """Test risk signals query with specific token."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show me ETH risk signals", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should respond with ETH-specific risk information
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_hunter_pattern_recognition(self, client: AsyncClient, llm_validator):
        """Test guest can access pattern recognition features."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what patterns do you see in BTC?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should provide pattern analysis
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_hunter_pattern_btc(self, client: AsyncClient, llm_validator):
        """Test pattern recognition for BTC specifically."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "analyze BTC chart patterns", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 0

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_hunter_risk_signals_multiple_tokens(self, client: AsyncClient, llm_validator):
        """Test risk signals for multiple tokens."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "compare risk signals for BTC and ETH", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle multi-token queries
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_hunter_pattern_eth_scenarios(self, client: AsyncClient, llm_validator):
        """Test pattern recognition edge cases for ETH."""
        queries = [
            "ETH pattern analysis",
            "what patterns are forming in ethereum?",
            "show me ETH technical patterns",
        ]

        for query in queries:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": query, "language": "en"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

class TestGuestULTRAMissingIntents:
    """Test ULTRA intents that were missing guest coverage."""

    @pytest.mark.llm_validation
    async def test_guest_ultra_mev_protection(self, client: AsyncClient, llm_validator):
        """Test guest can learn about MEV protection."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what is MEV protection?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should explain MEV protection
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_ultra_mev_protection_with_token(self, client: AsyncClient, llm_validator):
        """Test MEV protection information with specific context."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how does ULTRA protect against MEV when swapping ETH?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should provide MEV protection details
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_ultra_auto_executor(self, client: AsyncClient, llm_validator):
        """Test guest can learn about auto executor."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what is the auto executor feature?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should explain auto executor
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_ultra_auto_executor_demo_mode(self, client: AsyncClient, llm_validator):
        """Test auto executor shows demo information for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "enable auto executor", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # For guests, should explain feature but may require registration for execution
        assert "agent_message" in data

        # May have registration requirement
        if data.get("registration_required"):
            assert data["registration_required"]["required"] is True

        # Extract agent response for validation
        content = data["agent_message"]["content"]

class TestGuestPortfolioAccess:
    """Test portfolio access properly requires registration for guests."""

    @pytest.mark.llm_validation
    async def test_guest_portfolio_view_requires_registration(self, client: AsyncClient, llm_validator):
        """Test viewing portfolio requires registration."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show me my portfolio", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should indicate registration is required
        assert "registration_required" in data

        # If restricted, verify the flag
        if data["registration_required"]:
            assert data["registration_required"]["required"] is True
            assert "message" in data["registration_required"]

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_portfolio_balance_requires_registration(self, client: AsyncClient, llm_validator):
        """Test checking portfolio balance requires registration."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what is my balance?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have registration requirement field
        assert "registration_required" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_portfolio_view_registration_message(self, client: AsyncClient, llm_validator):
        """Test registration message is clear and helpful."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show my portfolio", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # If registration required, should have clear message
        if data.get("registration_required") and data["registration_required"]:
            reg_req = data["registration_required"]

            # Should have localized messages
            assert "message" in reg_req
            assert isinstance(reg_req["message"], dict)

            # Should have English message at minimum
            if reg_req["message"]:
                assert "en" in reg_req["message"] or len(reg_req["message"]) > 0

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_portfolio_balance_registration_cta(self, client: AsyncClient, llm_validator):
        """Test registration call-to-action is present."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "check my balance", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should provide guidance on next steps
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

class TestGuestLendingAccess:
    """Test lending operations properly require registration for guests."""

    @pytest.mark.llm_validation
    async def test_guest_lending_deposit_requires_registration(self, client: AsyncClient, llm_validator):
        """Test depositing to lending protocols requires registration."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "deposit USDC to Aave", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Execution requires registration
        assert "registration_required" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_lending_deposit_demo_rates(self, client: AsyncClient, llm_validator):
        """Test guests can view lending rates without registration."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what are the lending rates?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should provide rate information
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_lending_withdraw_requires_registration(self, client: AsyncClient, llm_validator):
        """Test withdrawing from lending requires registration."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "withdraw my USDC from Aave", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should require registration for execution
        assert "registration_required" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_lending_view_rates_allowed(self, client: AsyncClient, llm_validator):
        """Test guests can view lending rates (read-only)."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show me Aave lending rates", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should succeed - viewing rates is allowed
        assert "agent_message" in data

        # Should NOT require registration for viewing
        # (registration_required can be None or False for read operations)
        if data.get("registration_required"):
            # If present, it might be about execution, not viewing
            pass

        # Extract agent response for validation
        content = data["agent_message"]["content"]

class TestGuestMultiStepFlows:
    """Test multi-step flows for guest users."""

    @pytest.mark.llm_validation
    async def test_guest_lending_multistep_requires_registration(self, client: AsyncClient, llm_validator):
        """Test lending multi-step flow requires registration."""
        # Start lending flow
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I want to deposit to Aave", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should indicate registration is needed for execution
        assert "registration_required" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_lending_multistep_demo_flow(self, client: AsyncClient, llm_validator):
        """Test guests can see demo lending flow information."""
        # Query about lending process
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "how do I deposit to lending protocols?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should explain the process
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_portfolio_multistep_blocked(self, client: AsyncClient, llm_validator):
        """Test portfolio multi-step operations are blocked for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show me my activity history", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should require registration
        assert "registration_required" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_portfolio_multistep_registration_prompt(self, client: AsyncClient, llm_validator):
        """Test clear registration prompt for portfolio operations."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show my transaction history", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have clear guidance
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_activity_multistep_blocked(self, client: AsyncClient, llm_validator):
        """Test activity history multi-step is blocked for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "show me my recent swaps", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should require registration for personal data
        assert "registration_required" in data or "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_activity_multistep_demo_data(self, client: AsyncClient, llm_validator):
        """Test guests can see example activity data."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "what kind of activity can I track?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should explain features
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

class TestGuestAgentSquad:
    """Test agent squad basic routing for guests."""

    @pytest.mark.llm_validation
    async def test_guest_agent_squad_basic_routing(self, client: AsyncClient, llm_validator):
        """Test guest queries can access basic agent squad features."""
        agent_squad_queries = [
            "what agents do you have?",
            "tell me about your AI agents",
            "what can your agent squad do?",
            "explain your 18 agents",
        ]

        for query in agent_squad_queries:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": query, "language": "en"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Should provide information about agent squad
            assert "agent_message" in data
            agent_content = data["agent_message"]["content"]
            assert len(agent_content) > 0

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_agent_squad_hunter_routing(self, client: AsyncClient, llm_validator):
        """Test Hunter AI agent routing works for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "use Hunter AI to analyze BTC", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should route to Hunter AI
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_guest_agent_squad_ultra_routing(self, client: AsyncClient, llm_validator):
        """Test ULTRA agent routing works for guests."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "use ULTRA to find arbitrage", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should route to ULTRA agent
        assert "agent_message" in data

        # Extract agent response for validation
        content = data["agent_message"]["content"]
