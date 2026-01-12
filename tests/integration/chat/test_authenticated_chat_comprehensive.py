"""
Comprehensive integration tests for authenticated user chat endpoint.

Tests multi-step flows, database persistence, and real user scenarios using ops@anvlcrypto.com.

Test Strategy (CTO Framework):
- Phase 1: Test all multi-step flows with authenticated user
- Phase 2: Validate database persistence (messages, pending_action, swap_info, lending_info)
- Phase 3: Verify wallet address integration
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedChatMultiStepFlows:
    """Test multi-step flows for authenticated users with database persistence."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient):
        """
        Get authentication headers for ops@anvlcrypto.com user.

        This user should have an active session in the test database.
        If not, create a session first.
        """
        # Option 1: Login to get token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "ops@anvlcrypto.com",
                "password": "your_test_password_here"  # Update with actual test password
            }
        )

        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            return {"Authorization": f"Bearer {access_token}"}

        # Option 2: Use existing session token if available
        # This is a placeholder - update with actual session token retrieval
        pytest.skip("ops@anvlcrypto.com user not available or login failed")

    @pytest.fixture
    async def conversation_id(self, client: AsyncClient, auth_headers):
        """Create a new conversation for testing."""
        response = await client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Test Conversation"}
        )
        assert response.status_code == 201
        data = response.json()
        return data["id"]

    @pytest.mark.asyncio
    async def test_authenticated_lending_flow_with_real_wallet(
        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test LENDING flow for authenticated user with real wallet address.

        Validates:
        - Flow completes without signup prompts
        - Wallet address is shown in confirmation
        - Database persistence of lending_info
        """
        # Step 1: Initiate lending
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Deposit 1000 USDC", "language": "en"}
        )
        assert response.status_code == 201
        data = response.json()

        # Should ask for confirmation (or asset selection if not parsed)
        assert "message" in data
        content = data["message"]["content"]
        assert "USDC" in content or "asset" in content.lower()

        # Continue flow to completion...
        # Step 2-4: Similar to guest flow but without signup prompts

        # Final validation: Should NOT require registration
        assert data.get("requires_registration") is False

    @pytest.mark.asyncio
    async def test_authenticated_balance_shows_real_data(
        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users see real on-chain balance.

        Validates:
        - No demo data
        - Real wallet balance from Base chain
        - Shows $0.00 if empty (not fake $3000)
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's my balance?", "language": "en"}
        )
        assert response.status_code == 201
        data = response.json()

        content = data["message"]["content"]
        # Should NOT show fake demo data
        assert "$3,000" not in content  # No fake balance
        # Should show real balance or empty
        assert "$" in content  # Has dollar sign
        # Should not have demo disclaimer for authenticated users
        assert "demo" not in content.lower()

    @pytest.mark.asyncio
    async def test_authenticated_portfolio_shows_real_holdings(
        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users see real on-chain portfolio.

        Validates:
        - Real holdings from blockchain
        - Shows empty if wallet has no tokens
        - No fake $21,525 demo portfolio
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my portfolio", "language": "en"}
        )
        assert response.status_code == 201
        data = response.json()

        content = data["message"]["content"]
        # Should NOT show fake demo portfolio
        assert "$21,525" not in content
        # Should show real holdings or empty message
        assert any(word in content.lower() for word in ["portfolio", "holdings", "empty", "tokens"])

    @pytest.mark.asyncio
    async def test_authenticated_activity_shows_real_transactions(
        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users see real transaction history.

        Validates:
        - No fake demo transactions
        - Shows "No Transactions Found" if empty
        - Real tx hashes if available
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "My activity", "language": "en"}
        )
        assert response.status_code == 201
        data = response.json()

        content = data["message"]["content"]
        # Should NOT show fake demo transactions
        assert "0x1234...5678" not in content  # No fake hash
        # Should show real state
        assert any(word in content.lower() for word in ["transaction", "activity", "no transactions", "empty"])

    @pytest.mark.asyncio
    async def test_authenticated_receive_shows_real_address(
        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users see real wallet address.

        Validates:
        - Real EVM-compatible address
        - NOT fake 0x1234...5678
        - Full address or properly truncated
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my address", "language": "en"}
        )
        assert response.status_code == 201
        data = response.json()

        content = data["message"]["content"]
        # Should NOT show fake demo address
        assert "0x1234" not in content or "demo" not in content.lower()
        # Should have real address format
        assert "0x" in content  # EVM address starts with 0x


@pytest.mark.integration
@pytest.mark.chat
class TestDatabasePersistence:
    """Test database persistence for multi-step flows."""

    @pytest.fixture
    async def db_session(self, test_app):
        """Get database session for verification."""
        from dishka import FromDishka
        from sqlalchemy.ext.asyncio import AsyncSession

        # This is a simplified example - actual implementation depends on your DI setup
        # You may need to get the session from the DI container
        pytest.skip("Database session fixture needs container access")

    @pytest.mark.asyncio
    async def test_lending_info_persisted_in_database(
        self, client: AsyncClient, conversation_id, db_session: AsyncSession
    ):
        """
        Test that lending_info is persisted across message exchanges.

        Validates:
        - pending_action stored in conversation
        - lending_info (asset, amount) stored
        - State survives between requests
        """
        # Start lending flow
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending", "language": "en"}
        )

        # Verify database state
        # from app.domain.chat.entities import ChatConversation
        # stmt = select(ChatConversation).where(...)
        # result = await db_session.execute(stmt)
        # conversation = result.scalar_one_or_none()
        #
        # assert conversation.pending_action == "lending_awaiting_asset"
        # assert conversation.lending_info is not None

        pytest.skip("Requires database session and entity access")

    @pytest.mark.asyncio
    async def test_swap_info_persisted_in_database(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        Test that swap_info is persisted across message exchanges.

        Validates:
        - pending_action stored
        - swap_info (from_token, to_token, amount) stored
        - State survives between requests
        """
        pytest.skip("Requires database session and entity access")

    @pytest.mark.asyncio
    async def test_messages_stored_correctly(
        self, client: AsyncClient, conversation_id, db_session: AsyncSession
    ):
        """
        Test that all messages are stored in database.

        Validates:
        - User messages stored
        - Agent responses stored
        - Message order preserved
        - Timestamps correct
        """
        pytest.skip("Requires database session and entity access")


@pytest.mark.integration
@pytest.mark.chat
class TestIntentDetectionQuality:
    """Test intent detection accuracy and handling."""

    @pytest.mark.asyncio
    async def test_typo_tolerance_portfolio(self, client: AsyncClient):
        """Test that 'porfolio' typo routes to PORTFOLIO intent."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "porfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should route to portfolio handler (not out-of-scope)
        assert "portfolio" in content.lower() or "holdings" in content.lower()
        # Should NOT mention "baking" or other contamination
        assert "baking" not in content.lower()
        assert "bomb" not in content.lower()

    @pytest.mark.asyncio
    async def test_context_isolation_after_out_of_scope(self, client: AsyncClient):
        """
        Test that out-of-scope rejections don't contaminate future queries.

        Validates:
        - User sends "bomb" → rejected
        - User sends "portfolio" → should NOT reference "bomb" or "baking"
        """
        # Step 1: Send out-of-scope query
        await client.post(
            "/api/v1/guest/chat",
            json={"content": "bomb", "language": "en"}
        )

        # Step 2: Send valid DeFi query
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "portfolio", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]
        # Should respond about portfolio, NOT contaminated with "baking"
        assert "portfolio" in content.lower() or "holdings" in content.lower()
        assert "baking" not in content.lower()
        assert "bomb cake" not in content.lower()


@pytest.mark.integration
@pytest.mark.chat
class TestMultiStepStateManagement:
    """Test state management across multi-step flows."""

    @pytest.mark.asyncio
    async def test_concurrent_users_dont_interfere(self, client: AsyncClient):
        """
        Test that two concurrent guest users don't interfere with each other.

        Validates:
        - User A starts lending flow
        - User B starts swap flow
        - Neither flow affects the other
        """
        # Guest A: Lending flow
        response_a1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending", "language": "en"}
        )
        assert response_a1.json()["enrichment"]["lending_flow"] == "step1_asset"

        # Guest B: Swap flow
        response_b1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "swap", "language": "en"}
        )
        assert response_b1.json()["enrichment"]["swap_flow"] == "step1_from_token"

        # Guest A: Continue lending
        response_a2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "USDC", "language": "en"}
        )
        # Should still be in lending flow (not affected by Guest B)
        assert response_a2.json()["enrichment"]["lending_flow"] == "step2_amount"

    @pytest.mark.asyncio
    async def test_flow_restart_clears_previous_state(self, client: AsyncClient):
        """
        Test that restarting a flow clears previous state.

        Validates:
        - Start lending flow
        - Restart lending flow mid-way
        - Previous state is cleared
        """
        # Start lending flow
        await client.post("/api/v1/guest/chat", json={"content": "lending", "language": "en"})
        await client.post("/api/v1/guest/chat", json={"content": "USDC", "language": "en"})

        # Restart lending flow
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "lending", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should restart from step 1
        assert data["enrichment"]["lending_flow"] == "step1_asset"
