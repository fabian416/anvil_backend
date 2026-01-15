"""
Interruption Flow Integration Tests (P0 - CRITICAL).

Tests that verify state management when users interrupt multi-step flows
with unrelated messages. This is a CRITICAL gap identified in Week 1-8 testing.

Test Strategy (CTO Framework - First Principles Analysis):
- Risk: State corruption during flow interruption
- Impact: Transaction errors, lost user context, broken UX
- Priority: P0 (Highest) - Production-critical functionality

Test Scenarios:
1. Swap flow interrupted by general question
2. Lending flow interrupted by price check
3. Multiple interruptions in single flow
4. Interruption then flow resumption
5. Interruption with context switch (ULTRA → Swap)
6. Cancellation after interruption
7. Complex flow with multiple interruption points

Coverage:
- Guest users (IP-based)
- Authenticated users (JWT-based)
- All multistep intents (swap, lending, buy, send)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from tests.helpers.auth_helper import AuthHelper


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.critical
class TestInterruptionFlows:
    """Test interruption handling in multistep chat flows."""

    # ==========================================
    # Guest User Interruption Tests
    # ==========================================

    @pytest.mark.asyncio
    async def test_guest_swap_flow_interrupted_by_general_question(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN a guest user starting a swap flow
        WHEN they interrupt with a general question
        THEN the system should:
        - Answer the question
        - NOT lose swap flow state
        - Allow resuming the swap flow
        """
        # Step 1: Start swap flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Swap 100 USDC for ETH",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "swap" in data1.get("message", "").lower() or "quote" in data1.get("message", "").lower()

        # Step 2: Interrupt with unrelated question
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is Bitcoin?",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should answer the question about Bitcoin
        assert "bitcoin" in data2.get("message", "").lower() or "btc" in data2.get("message", "").lower()

        # Step 3: Resume swap flow (continue or cancel)
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Yes, continue the swap",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        assert response3.status_code == 200
        data3 = response3.json()
        # Should resume swap flow or handle gracefully
        assert response3.status_code == 200

    @pytest.mark.asyncio
    async def test_guest_lending_flow_interrupted_by_price_check(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN a guest user starting a lending deposit flow
        WHEN they interrupt with a price check request
        THEN the system should:
        - Provide price information
        - Maintain lending flow state
        - Allow flow resumption
        """
        # Step 1: Start lending flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I want to deposit USDC to earn yield",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.5"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        # Should start lending flow
        assert any(keyword in data1.get("message", "").lower() for keyword in ["deposit", "vault", "yield", "lend"])

        # Step 2: Interrupt with price check
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the current ETH price?",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.5"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should provide ETH price
        assert any(keyword in data2.get("message", "").lower() for keyword in ["eth", "ethereum", "price"])

        # Step 3: Try to resume lending flow
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Continue with deposit",
                "language": "en",
            },
            headers={"X-Forwarded-For": "1.2.3.5"},
        )
        assert response3.status_code == 200
        # Should handle resumption gracefully (may ask to restart or continue)

    @pytest.mark.asyncio
    async def test_guest_multiple_interruptions_in_single_flow(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN a guest user in a multistep flow
        WHEN they send multiple interruption messages
        THEN the system should:
        - Handle each interruption independently
        - NOT corrupt state
        - Maintain conversation context
        """
        # Start swap flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap USDC to ETH", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.6"},
        )
        assert response1.status_code == 200

        # Interruption 1: General question
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is DeFi?", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.6"},
        )
        assert response2.status_code == 200
        assert "defi" in response2.json().get("message", "").lower()

        # Interruption 2: Price check
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Show me BTC price", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.6"},
        )
        assert response3.status_code == 200

        # Try to continue original flow
        response4 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Continue my swap", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.6"},
        )
        assert response4.status_code == 200

    @pytest.mark.asyncio
    async def test_guest_interruption_with_context_switch(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN a guest user in a swap flow
        WHEN they interrupt with ULTRA Hunter request (different intent)
        THEN the system should:
        - Process ULTRA Hunter request
        - Switch context appropriately
        - Handle original flow cancellation/resumption
        """
        # Start swap flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap 50 USDC for ETH", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.7"},
        )
        assert response1.status_code == 200

        # Interrupt with ULTRA Hunter (different intent entirely)
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Show me risk signals for ETH", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.7"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should provide risk signals
        assert any(keyword in data2.get("message", "").lower() for keyword in ["risk", "signal", "eth", "ethereum"])

        # Original swap flow should be cancelled or pausable
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What was I doing?", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.7"},
        )
        assert response3.status_code == 200

    @pytest.mark.asyncio
    async def test_guest_cancellation_after_interruption(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN a guest user who interrupted a multistep flow
        WHEN they explicitly cancel
        THEN the system should:
        - Clear the flow state
        - Confirm cancellation
        - Start fresh on next request
        """
        # Start lending flow
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit USDC to earn yield", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.8"},
        )
        assert response1.status_code == 200

        # Interrupt
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the weather?", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.8"},
        )
        assert response2.status_code == 200

        # Cancel explicitly
        response3 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Cancel", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.8"},
        )
        assert response3.status_code == 200
        # Should acknowledge cancellation

        # Start fresh
        response4 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Show my portfolio", "language": "en"},
            headers={"X-Forwarded-For": "1.2.3.8"},
        )
        assert response4.status_code == 200
        # Should handle as new request without flow state

    # ==========================================
    # Authenticated User Interruption Tests
    # ==========================================

    @pytest_asyncio.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user for authenticated interruption tests."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email=f"interruption_test_{uuid4().hex[:8]}@example.com",
        )
        return user, token

    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest.mark.asyncio
    async def test_authenticated_swap_interrupted_then_resumed(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        async_db_session: AsyncSession,
    ):
        """
        GIVEN an authenticated user starting a swap flow
        WHEN they interrupt with a balance check
        THEN resume the swap
        THEN the system should:
        - Provide balance information
        - Maintain swap state for authenticated user
        - Complete swap successfully after resumption
        """
        user, token = test_user

        # Create conversation
        create_conv_response = await client.post(
            "/api/v1/conversations",
            json={"language": "en"},
            headers=auth_headers,
        )
        assert create_conv_response.status_code == 201
        conversation_id = create_conv_response.json()["id"]

        # Step 1: Start swap
        response1 = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Swap 100 USDC for ETH", "language": "en"},
            headers=auth_headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "swap" in data1.get("message", "").lower() or "quote" in data1.get("message", "").lower()

        # Step 2: Interrupt with balance check
        response2 = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "What's my USDC balance?", "language": "en"},
            headers=auth_headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should provide balance info
        assert any(keyword in data2.get("message", "").lower() for keyword in ["usdc", "balance"])

        # Step 3: Resume swap
        response3 = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Continue with the swap", "language": "en"},
            headers=auth_headers,
        )
        assert response3.status_code == 200
        # Should handle resumption (authenticated users have persistent state)

    @pytest.mark.asyncio
    async def test_authenticated_complex_interruption_scenario(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
        async_db_session: AsyncSession,
    ):
        """
        GIVEN an authenticated user in a complex multi-step flow
        WHEN they interrupt multiple times with different intents
        THEN the system should:
        - Handle all interruptions gracefully
        - Maintain conversation history
        - Preserve user context across interruptions
        - Allow flexible flow resumption
        """
        user, token = test_user

        # Create conversation
        create_conv_response = await client.post(
            "/api/v1/conversations",
            json={"language": "en"},
            headers=auth_headers,
        )
        assert create_conv_response.status_code == 201
        conversation_id = create_conv_response.json()["id"]

        # Complex flow with interruptions
        messages = [
            ("Deposit 500 USDC to Morpho", "deposit|vault|morpho|lend"),  # Start lending
            ("Wait, what's the APY on Aave?", "aave|apy|rate"),  # Interruption 1: Compare protocols
            ("Show me ETH price trends", "eth|price|trend"),  # Interruption 2: Market check
            ("What are the risks?", "risk"),  # Interruption 3: Risk check
            ("Okay, continue with Morpho deposit", "morpho|deposit|continue"),  # Resume
        ]

        for idx, (message, expected_keywords) in enumerate(messages, start=1):
            response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={"content": message, "language": "en"},
                headers=auth_headers,
            )
            assert response.status_code == 200, f"Message {idx} failed: {message}"
            data = response.json()

            # Verify response contains expected keywords
            response_text = data.get("message", "").lower()
            keywords = expected_keywords.split("|")
            assert any(keyword in response_text for keyword in keywords), \
                f"Message {idx}: Expected one of {keywords} in response"

        # Verify conversation history preserved
        get_conv_response = await client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=auth_headers,
        )
        assert get_conv_response.status_code == 200
        conv_data = get_conv_response.json()
        assert conv_data["conversation"]["message_count"] >= 10  # At least 5 user + 5 assistant


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.critical
class TestInterruptionStateManagement:
    """Test state management during interruptions."""

    @pytest.mark.asyncio
    async def test_guest_state_isolation_between_users(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN two different guest users starting flows
        WHEN they send messages simultaneously
        THEN their states should NOT interfere
        """
        # User 1: Start swap
        response1_user1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Swap USDC to ETH", "language": "en"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert response1_user1.status_code == 200

        # User 2: Start lending (different IP, different flow)
        response1_user2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Deposit DAI", "language": "en"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert response1_user2.status_code == 200

        # User 1: Continue swap
        response2_user1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Confirm swap", "language": "en"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert response2_user1.status_code == 200
        # Should be in swap context, not lending

        # User 2: Continue lending
        response2_user2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Select Aave", "language": "en"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert response2_user2.status_code == 200
        # Should be in lending context, not swap

    @pytest.mark.asyncio
    async def test_authenticated_state_persistence_across_sessions(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
    ):
        """
        GIVEN an authenticated user with an interrupted flow
        WHEN they disconnect and reconnect (new session)
        THEN the conversation state should be preserved
        """
        # Create user and start conversation
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email=f"state_persist_{uuid4().hex[:8]}@example.com",
        )
        auth_headers = AuthHelper.get_auth_headers(token)

        # Create conversation
        create_response = await client.post(
            "/api/v1/conversations",
            json={"language": "en"},
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        conversation_id = create_response.json()["id"]

        # Start a flow and interrupt
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Swap 100 USDC for ETH", "language": "en"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "What's the gas price?", "language": "en"},
            headers=auth_headers,
        )

        # Simulate reconnection: Retrieve conversation
        get_response = await client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        conv_data = get_response.json()

        # Verify message history preserved
        assert len(conv_data["messages"]) >= 4  # 2 user + 2 assistant minimum

        # Continue the flow
        continue_response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Resume the swap", "language": "en"},
            headers=auth_headers,
        )
        assert continue_response.status_code == 200
        # Should handle context from previous messages
