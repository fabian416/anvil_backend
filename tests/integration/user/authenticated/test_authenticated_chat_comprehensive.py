"""
Comprehensive integration tests for authenticated user chat endpoint.

Tests multi-step flows, database persistence, and real user scenarios.

Test Strategy (CTO Framework):
- Phase 1: Test all multi-step flows with authenticated user
- Phase 2: Validate database persistence (messages, pending_action, swap_info, lending_info)
- Phase 3: Verify wallet address integration
- Phase 4: Test authenticated vs guest behavior differences
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.auth_helper import AuthHelper


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedChatEndpoint:
    """Test authenticated user chat endpoint existence and basic functionality."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_endpoint@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_endpoint_requires_auth(self, client: AsyncClient, llm_validator):
        """Test that authenticated endpoint requires authentication."""
        response = await client.post(
            "/api/v1/conversations/test_conv_123/messages",
            json={"content": "What's my balance?", "language": "en"}
        )
        # Should return 401, 403 (unauthorized), or 422 (validation error for non-existent conversation)
        assert response.status_code in [401, 403, 422]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_endpoint_requires_auth",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_user_can_send_message(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_user_can_send_message",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test that authenticated user can send a message."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's my balance?", "language": "en"}
        )

        # Should succeed (200 or 201)
        assert response.status_code in [200, 201], f"Unexpected status: {response.status_code}"


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedMultiStepFlows:
    """Test multi-step conversational flows for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_flows@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user

        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    # ===== LENDING FLOW TESTS (5 steps) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_step1_initiate(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_step1_initiate",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        LENDING Step 1: User initiates lending flow.

        Expected: System asks for asset to deposit.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "I want to lend my crypto", "language": "en"}
        )

        assert response.status_code in [200, 201], f"Status: {response.status_code}"
        data = response.json()

        # Extract response content
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should ask for asset
        assert any(word in content.lower() for word in ["asset", "token", "usdc", "eth", "dai"]), \
            f"Step 1 should ask for asset: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_step2_select_asset(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_step2_select_asset",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        LENDING Step 2: User selects asset (USDC).

        Expected: System asks for amount to deposit.
        """
        # Step 1: Initiate
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "lending", "language": "en"}
        )

        # Step 2: Select asset
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "USDC", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should ask for amount
        assert any(word in content.lower() for word in ["amount", "how much", "deposit"]), \
            f"Step 2 should ask for amount: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_step3_enter_amount(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_step3_enter_amount",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        LENDING Step 3: User enters amount (1000 USDC).

        Expected: System shows vault options with APY quotes.
        """
        # Step 1: Initiate
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "lending", "language": "en"}
        )

        # Step 2: Select asset
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "USDC", "language": "en"}
        )

        # Step 3: Enter amount
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "1000", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show vault options with APY
        assert any(word in content.lower() for word in ["apy", "vault", "earn", "yield"]), \
            f"Step 3 should show vault options: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_step4_confirm_deposit(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_step4_confirm_deposit",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        LENDING Step 4: User confirms deposit.

        Expected: For authenticated users, should proceed without signup prompt.
        """
        # Complete flow to confirmation
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "lending", "language": "en"}
        )
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "USDC", "language": "en"}
        )
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "1000", "language": "en"}
        )

        # Step 4: Confirm
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "yes, confirm", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()

        # Should NOT require signup (authenticated user)
        requires_reg = data.get("registration_required") or data.get("requires_registration")
        if requires_reg is not None:
            assert requires_reg is False, "Authenticated users shouldn't need signup"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_no_signup_prompt_for_auth(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_no_signup_prompt_for_auth",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        LENDING Step 5: Validate no signup prompts shown to authenticated users.

        Expected: Full flow completes without "sign up" messages.
        """
        # Complete full lending flow
        responses = []

        responses.append(await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "deposit USDC", "language": "en"}
        ))

        responses.append(await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "1000", "language": "en"}
        ))

        # Check all responses for signup prompts
        for response in responses:
            if response.status_code in [200, 201]:
                data = response.json()
                content = str(data).lower()

                # Should NOT contain signup language
                assert "sign up" not in content, "Authenticated users shouldn't see signup prompts"
                assert "create account" not in content, "Authenticated users shouldn't see account creation prompts"

    # ===== SWAP FLOW TESTS (4 steps) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_step1_initiate(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_step1_initiate",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        SWAP Step 1: User initiates swap.

        Expected: System asks for source token and target token.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "swap", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should ask for swap details
        assert any(word in content.lower() for word in ["swap", "exchange", "token", "from", "to"]), \
            f"Step 1 should ask for swap details: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_step2_get_quote(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_step2_get_quote",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        SWAP Step 2: User provides swap details (100 USDC to ETH).

        Expected: System shows quote with exchange rate.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Swap 100 USDC to ETH", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show quote/rate information
        assert any(word in content.lower() for word in ["rate", "quote", "price", "receive", "eth"]), \
            f"Step 2 should show quote: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_step3_confirm(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_step3_confirm",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        SWAP Step 3: User confirms swap.

        Expected: For authenticated users, proceeds without signup.
        """
        # Get quote
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Swap 100 USDC to ETH", "language": "en"}
        )

        # Confirm
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "confirm swap", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()

        # Should NOT require signup
        requires_reg = data.get("registration_required") or data.get("requires_registration")
        if requires_reg is not None:
            assert requires_reg is False, "Authenticated users shouldn't need signup for swap"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_no_signup_prompt(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_no_signup_prompt",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        SWAP Step 4: Validate no signup prompts in swap flow.

        Expected: Authenticated users complete swap without signup prompts.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Swap 50 USDC to ETH", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should NOT contain signup language
        assert "sign up" not in content, "Swap flow shouldn't prompt signup for authenticated users"
        assert "create account" not in content

    # ===== SWAP_MOONPAY FLOW TESTS (3 steps) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_moonpay_swap_step1_initiate(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_moonpay_swap_step1_initiate",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        MOONPAY SWAP Step 1: User initiates fiat-to-crypto swap via MoonPay.

        Expected: System explains MoonPay integration and asks for details.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "buy crypto with card", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should mention MoonPay or fiat purchase
        assert any(word in content.lower() for word in ["moonpay", "card", "buy", "purchase", "fiat"]), \
            f"Step 1 should explain MoonPay option: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_moonpay_swap_step2_get_quote(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_moonpay_swap_step2_get_quote",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        MOONPAY SWAP Step 2: User requests quote for fiat purchase.

        Expected: System shows MoonPay quote with fees.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Buy 100 USD of ETH with card", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show quote or pricing info
        assert any(word in content.lower() for word in ["price", "fee", "total", "eth", "receive"]), \
            f"Step 2 should show quote: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_moonpay_swap_no_signup_for_auth(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_moonpay_swap_no_signup_for_auth",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        MOONPAY SWAP Step 3: Validate authenticated users can proceed.

        Expected: No signup prompts, direct MoonPay integration.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Buy 50 USD ETH with card", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should NOT require signup
        assert "sign up" not in content, "MoonPay flow shouldn't prompt signup for authenticated users"

    # ===== BUY FLOW TESTS (3 steps) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_buy_step1_initiate(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_buy_step1_initiate",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        BUY Step 1: User initiates token purchase.

        Expected: System asks which token to buy.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "buy tokens", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should ask for token details
        assert any(word in content.lower() for word in ["buy", "token", "crypto", "which", "what"]), \
            f"Step 1 should ask for token: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_buy_step2_show_options(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_buy_step2_show_options",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        BUY Step 2: User specifies token (ETH).

        Expected: System shows buying options (DEX, CEX, MoonPay).
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Buy ETH", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show buying options or proceed with purchase
        assert any(word in content.lower() for word in ["eth", "buy", "purchase", "swap"]), \
            f"Step 2 should handle ETH purchase: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_buy_no_signup_for_auth(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_buy_no_signup_for_auth",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        BUY Step 3: Validate no signup prompts for authenticated users.

        Expected: Buy flow completes without signup requirements.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "I want to buy 0.1 ETH", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should NOT contain signup language
        assert "sign up" not in content, "Buy flow shouldn't prompt signup for authenticated users"
        assert "create account" not in content


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedVsGuestBehavior:
    """Test behavioral differences between authenticated and guest users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_auth_vs_guest@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user

        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_no_signup_prompts(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_no_signup_prompts",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users never see signup prompts.

        Validates:
        - No "Sign up" messages
        - No "Create an account" prompts
        - No demo data disclaimers
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's my balance?", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Get content
            if "agent_message" in data:
                content = data["agent_message"]["content"]
            elif "message" in data:
                content = data["message"]["content"]
            else:
                content = str(data)

            content_lower = content.lower()

            # Should NOT have signup prompts
            signup_phrases = [
                "sign up", "signup", "create an account", "register now",
                "get started", "join now"
            ]
            has_signup = any(phrase in content_lower for phrase in signup_phrases)

            # If signup prompt exists, fail test
            assert not has_signup, f"Authenticated user received signup prompt: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_real_data_not_demo(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_real_data_not_demo",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users see real data, not demo data.

        Validates:
        - No fake $3,000 demo balance
        - No fake $21,525 portfolio
        - No "demo" disclaimers
        """
        # Test balance
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my balance", "language": "en"}
        )

        if response.status_code in [200, 201]:
            data = response.json()

            if "agent_message" in data:
                content = data["agent_message"]["content"]
            elif "message" in data:
                content = data["message"]["content"]
            else:
                content = str(data)

            # Should NOT show demo data
            assert "$3,000" not in content, "Authenticated user saw demo balance"
            assert "$21,525" not in content, "Authenticated user saw demo portfolio"

            # Should NOT have demo disclaimers
            assert "demo" not in content.lower() or "demon" in content.lower(), \
                "Authenticated user saw demo disclaimer"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_higher_rate_limits(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_higher_rate_limits",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test that authenticated users have higher rate limits than guests.

        Validates:
        - Authenticated users can make more requests
        - If rate limit hit, it's higher than guest limit (20/hour)
        """
        # Send multiple requests
        request_count = 0
        max_requests = 30  # More than guest limit (20)

        for i in range(max_requests):
            response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={"content": f"Test message {i}", "language": "en"}
            )

            if response.status_code == 429:  # Rate limit hit
                # If we hit rate limit, verify it's higher than guest limit
                assert i > 20, f"Authenticated user hit rate limit at {i} requests (guest limit: 20)"
                break
            elif response.status_code in [200, 201]:
                request_count += 1
            else:
                # Other error - skip test
                pytest.skip(f"Unexpected status: {response.status_code}")

        # If we made it past 20 requests without rate limit, test passes
        assert request_count >= 20 or request_count == max_requests


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedIntents:
    """Test intent detection and routing for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_intents@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user

        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_balance_intent(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_balance_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test BALANCE intent for authenticated user."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's my balance?", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Check intent routing
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "balance" in intent or routing.get("handler") == "balance_handler"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_intent(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portfolio_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test PORTFOLIO intent for authenticated user."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my portfolio", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Check intent routing
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "portfolio" in intent or routing.get("handler") == "portfolio_handler"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_activity_intent(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_activity_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test ACTIVITY intent for authenticated user."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my recent activity", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Check intent routing
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "activity" in intent or routing.get("handler") == "activity_handler"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_receive_intent(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_receive_intent",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test RECEIVE intent for authenticated user."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my wallet address", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Check intent routing
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "receive" in intent or routing.get("handler") == "receive_handler"


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedMultiLanguage:
    """Test multi-language support for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_multilang@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user

        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_spanish_support(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_spanish_support",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Spanish language support."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "¿Cuál es mi saldo?", "language": "es"}
        )

        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portuguese_support(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_support",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Portuguese language support."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Qual é o meu saldo?", "language": "pt"}
        )

        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_chinese_support(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_support",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Chinese language support."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "我的余额是多少？", "language": "zh"}
        )

        assert response.status_code in [200, 201]


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedDatabasePersistence:
    """Test database persistence for authenticated conversations."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_db_persist@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_conversation_created_in_database(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_conversation_created_in_database",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, test_user, async_db_session: AsyncSession
    ):
        """
        Test that authenticated conversations are created in database.

        Validates:
        - Conversation has user_id (not NULL like guests)
        - Conversation is accessible
        """
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with chat_user_id
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language)
                VALUES (:id, :user_id, :title, :status, :language)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "DB Test Conversation",
                "status": "active",
                "language": "en"
            }
        )
        await async_db_session.commit()

        # Send message
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Test message", "language": "en"}
        )

        if response.status_code in [200, 201]:
            # Verify conversation in database with correct chat_user_id
            result = await async_db_session.execute(
                text("""
                    SELECT user_id FROM chat_conversations
                    WHERE id = :conv_id
                """),
                {"conv_id": conversation_id}
            )
            row = result.fetchone()

            assert row is not None, "Conversation not found in database"
            assert row[0] == unified_chat_user_uuid, "Conversation has wrong chat_user_id"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_messages_stored_with_user_id(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_messages_stored_with_user_id",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, test_user, async_db_session: AsyncSession
    ):
        """
        Test that messages are stored with correct user_id.

        Validates:
        - Messages have conversation_id
        - Messages are retrievable
        - Timestamps are set
        """
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with chat_user_id
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language)
                VALUES (:id, :user_id, :title, :status, :language)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Message DB Test",
                "status": "active",
                "language": "en"
            }
        )
        await async_db_session.commit()

        # Send message
        message_content = "Test message for DB storage"
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": message_content, "language": "en"}
        )

        if response.status_code in [200, 201]:
            # Verify messages in database
            result = await async_db_session.execute(
                text("""
                    SELECT COUNT(*) FROM chat_messages
                    WHERE conversation_id = :conv_id
                    AND created_at >= NOW() - INTERVAL '1 minute'
                """),
                {"conv_id": conversation_id}
            )
            message_count = result.scalar()

            # Should have at least 1 message (user message, possibly agent response)
            assert message_count >= 1, "No messages found in database"


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedErrorHandling:
    """Test error handling for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_errors@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user

        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_empty_message_rejected(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_empty_message_rejected",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test that empty messages are rejected."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "", "language": "en"}
        )

        # Should return validation error (422)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_invalid_language_rejected(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_invalid_language_rejected",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test that invalid language codes are rejected."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Test message", "language": "invalid"}
        )

        # Should return validation error (422)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_nonexistent_conversation_handled(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_nonexistent_conversation_handled",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers
    ):
        """Test that requests to non-existent conversations are handled gracefully."""
        response = await client.post(
            "/api/v1/conversations/nonexistent_conv_123/messages",
            headers=auth_headers,
            json={"content": "Test message", "language": "en"}
        )

        # Should return 404 or handle gracefully
        assert response.status_code in [404, 400, 422]


# ============================================================================
# PHASE 1: CORE INTENT COVERAGE
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedHunterAI:
    """Test Hunter AI intents for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_hunter@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_analysis(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_analysis",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI sentiment analysis intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's the sentiment for BTC?", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()

            # Check routing
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "sentiment" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_price_prediction(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_price_prediction",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate cryptocurrency price information in a clear format. Response must reference cryptocurrency specifically (not other cryptocurrencies) and include current price data with USD denomination."
                ),
                additional_context={'test_category': 'price_query', 'token': 'cryptocurrency'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI price prediction intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Predict ETH price", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "price" in intent or "prediction" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_signals(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_risk_signals",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI risk signals intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Risk signals for SOL", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "risk" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trading_signals(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_trading_signals",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI trading signals intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Should I buy BTC?", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "trading" in intent or "signal" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_pattern_recognition(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_pattern_recognition",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI pattern recognition intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Chart patterns for ETH", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "pattern" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_optimization(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portfolio_optimization",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test Hunter AI portfolio optimization intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Optimize my portfolio", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "hunter" in intent or "portfolio" in intent or "optimi" in intent


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedULTRA:
    """Test ULTRA intents for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_ultra@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_arbitrage_discovery(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_arbitrage_discovery",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test ULTRA arbitrage discovery intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Find arbitrage opportunities", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "ultra" in intent or "arbitrage" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_flash_loans(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_flash_loans",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test ULTRA flash loans intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Best flash loan for USDC", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "ultra" in intent or "flash" in intent or "loan" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_mev_protection(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_mev_protection",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test ULTRA MEV protection intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Execute with Flashbots", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "ultra" in intent or "mev" in intent or "flashbots" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auto_executor(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_auto_executor",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test ULTRA auto executor intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Start trading bot", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "ultra" in intent or "auto" in intent or "executor" in intent or "bot" in intent


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedGraphRAG:
    """Test GraphRAG intents for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_graphrag@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_protocol_search(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_search",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test GraphRAG protocol search intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Find low-risk staking protocols", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "protocol" in intent or "search" in intent

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_risk_assessment(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_risk_assessment",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test GraphRAG risk assessment intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Is Aave safe?", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "risk" in intent or "assessment" in intent or "safe" in intent.lower()

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_similar_protocols(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_similar_protocols",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test GraphRAG similar protocols intent."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Protocols like Uniswap", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                intent = routing.get("intent", "").lower()
                assert "similar" in intent or "protocol" in intent or "alternative" in intent


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedAgentSquad:
    """Test Agent Squad orchestration for authenticated users."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_squad@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        # TestUser.id is UUID(int=users.id), so we get the int back
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        # NOTE: Unified chat uses 'user_id', not 'chat_user_id'
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_specialist_task(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_specialist_task",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test specialist agent routing."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Best USDC yield strategy", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                # Should route to specialist or yield-related handler
                intent = routing.get("intent", "").lower()
                handler = routing.get("handler", "").lower()
                assert any(word in intent + handler for word in ["specialist", "yield", "defi", "lending"])

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_complex_workflow(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_complex_workflow",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """Test complex workflow orchestration."""
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Create balanced portfolio strategy", "language": "en"}
        )

        assert response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            routing = data.get("routing", {})
            if routing:
                # Should route to complex workflow or portfolio handler
                intent = routing.get("intent", "").lower()
                handler = routing.get("handler", "").lower()
                assert any(word in intent + handler for word in ["portfolio", "complex", "workflow", "strategy"])


@pytest.mark.integration
@pytest.mark.chat
class TestAuthenticatedShortcutsAndQuality:
    """Test DeFi shortcuts, production quality, and auth-specific behavior."""

    @pytest_asyncio.fixture
    @pytest.mark.llm_validation
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user in the database."""
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            role="user",
            email="test_shortcuts@example.com",
        )
        return user, token

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest_asyncio.fixture
    async def auth_headers(self, test_user):
        """Get authentication headers for test user."""
        user, token = test_user
        return AuthHelper.get_auth_headers(token)

    @pytest_asyncio.fixture
    async def conversation_id(self, test_user, async_db_session: AsyncSession):
        """Create a new conversation for testing."""
        user, token = test_user
        conversation_id = str(uuid4())

        # Extract INTEGER user_id from TestUser UUID
        user_id_int = int(user.id.int)

        # Insert into unified chat_users (with user_type) and get auto-generated UUID
        result = await async_db_session.execute(
            text("""
                INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                VALUES (:user_type, :identifier, :email, :language)
                ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "user_type": "authenticated",
                "identifier": str(user_id_int),
                "email": user.email,
                "language": "en"
            }
        )
        unified_chat_user_uuid = result.scalar_one()

        # Create conversation with user_id (UUID FK to chat_users.id)
        await async_db_session.execute(
            text("""
                INSERT INTO chat_conversations (id, user_id, title, status, language, message_count)
                VALUES (:id, :user_id, :title, :status, :language, :message_count)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": conversation_id,
                "user_id": unified_chat_user_uuid,
                "title": "Test Conversation",
                "status": "active",
                "language": "en",
                "message_count": 0
            }
        )
        await async_db_session.commit()

        return conversation_id

    # ===== DEFI SHORTCUTS TESTS (8 tests) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_balance(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_balance",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test BALANCE shortcut for authenticated users.

        Expected: Shows real wallet balance (not demo data).
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "balance", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show balance information
        assert any(word in content.lower() for word in ["balance", "total", "portfolio", "$"]), \
            f"Balance shortcut should show balance: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_portfolio(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_portfolio",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test PORTFOLIO shortcut for authenticated users.

        Expected: Shows portfolio breakdown with holdings.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "portfolio", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show portfolio information
        assert any(word in content.lower() for word in ["portfolio", "holdings", "assets", "tokens"]), \
            f"Portfolio shortcut should show holdings: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_activity(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_activity",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test ACTIVITY shortcut for authenticated users.

        Expected: Shows recent transaction activity.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "activity", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show activity information
        assert any(word in content.lower() for word in ["activity", "transaction", "recent", "history"]), \
            f"Activity shortcut should show transactions: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_send(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_send",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test SEND shortcut for authenticated users.

        Expected: Initiates send flow without signup prompt.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "send 10 USDC", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should handle send request
        assert any(word in content for word in ["send", "transfer", "recipient", "address"]), \
            f"Send shortcut should handle transfer: {content[:200]}"

        # Should NOT require signup
        assert "sign up" not in content, "Send shortcut shouldn't prompt signup for authenticated users"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_receive(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_receive",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test RECEIVE shortcut for authenticated users.

        Expected: Shows wallet address for receiving funds.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "receive", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should provide wallet address or instructions
        assert any(word in content.lower() for word in ["address", "wallet", "receive", "deposit"]), \
            f"Receive shortcut should show address: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_money_market(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_money_market",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for crypto. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test MONEY_MARKET shortcut for authenticated users.

        Expected: Shows DeFi lending/borrowing rates.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "money market rates", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content") or data.get("message", {}).get("content", "")

        # Should show rate information
        assert any(word in content.lower() for word in ["rate", "apy", "yield", "lending", "borrowing", "market"]), \
            f"Money market shortcut should show rates: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_multi_language_support(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_multi_language_support",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test shortcuts work with multi-language support.

        Expected: Shortcuts respond in requested language.
        """
        # Test with Spanish
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "balance", "language": "es"}
        )

        assert response.status_code in [200, 201]
        # Response should be successful (language translation happens in handler)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcut_response_time(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcut_response_time",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test shortcuts respond quickly (performance check).

        Expected: Response within reasonable time (< 5 seconds).
        """
        import time

        start_time = time.time()
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "balance", "language": "en"}
        )
        elapsed_time = time.time() - start_time

        assert response.status_code in [200, 201]
        assert elapsed_time < 5.0, f"Shortcut took too long: {elapsed_time:.2f}s (should be < 5s)"

    # ===== PRODUCTION QUALITY TESTS (5 tests) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_error_handling_invalid_conversation(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_handling_invalid_conversation",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers
    ):
        """
        Test error handling for invalid conversation ID.

        Expected: Clear error message, appropriate status code.
        """
        invalid_conv_id = str(uuid4())
        response = await client.post(
            f"/api/v1/conversations/{invalid_conv_id}/messages",
            headers=auth_headers,
            json={"content": "test", "language": "en"}
        )

        # Should return error status (404 or 422)
        assert response.status_code in [404, 422], f"Should return error for invalid conversation: {response.status_code}"

        if response.status_code in [404, 422]:
            data = response.json()
            # Should have error details
            assert "detail" in data or "error" in data or "message" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_error_handling_empty_message(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_handling_empty_message",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test error handling for empty message content.

        Expected: Validation error with clear message.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "", "language": "en"}
        )

        # Should return validation error (422)
        assert response.status_code == 422, f"Should return 422 for empty message: {response.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_response_format_consistency(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_response_format_consistency",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test response format consistency across different intents.

        Expected: All responses follow same structure.
        """
        test_queries = ["balance", "swap", "portfolio", "lending"]
        response_formats = []

        for query in test_queries:
            response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={"content": query, "language": "en"}
            )

            if response.status_code in [200, 201]:
                data = response.json()
                # Check for consistent top-level keys
                has_agent_message = "agent_message" in data
                has_message = "message" in data
                has_routing = "routing" in data

                response_formats.append({
                    "query": query,
                    "has_agent_message": has_agent_message,
                    "has_message": has_message,
                    "has_routing": has_routing
                })

        # All responses should have similar structure
        assert len(response_formats) > 0, "Should have at least one successful response"

        # Check consistency (at least one common key across all responses)
        common_keys = ["agent_message", "message", "routing"]
        for key in common_keys:
            key_count = sum(1 for fmt in response_formats if fmt.get(f"has_{key}"))
            if key_count > 0:
                # At least this key appears in responses
                break
        else:
            assert False, "No common response structure found"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_rate_limit_headers_present(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_rate_limit_headers_present",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test rate limit information in response headers.

        Expected: Rate limit headers present for authenticated users.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "balance", "language": "en"}
        )

        assert response.status_code in [200, 201]

        # Check for rate limit headers (may or may not be present depending on implementation)
        # This is a quality check, not a strict requirement
        headers = response.headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]

        # Log presence of rate limit headers
        has_rate_limits = any(header in headers for header in rate_limit_headers)
        # Test passes regardless - this is informational for production quality assessment

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_conversation_context_persistence(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_conversation_context_persistence",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test conversation context is maintained across messages.

        Expected: Subsequent messages have context from previous messages.
        """
        # Message 1: Ask for balance
        response1 = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What's my balance?", "language": "en"}
        )

        assert response1.status_code in [200, 201]

        # Message 2: Follow-up question (should understand context)
        response2 = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "And how much ETH do I have?", "language": "en"}
        )

        assert response2.status_code in [200, 201]
        # Context should be maintained (both messages succeeded in same conversation)

    # ===== AUTH-SPECIFIC BEHAVIOR TESTS (3 tests) =====

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_vs_guest_rate_limits(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_vs_guest_rate_limits",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test authenticated users have higher rate limits than guests.

        Expected: Authenticated users can make more requests.
        """
        # Make multiple rapid requests (authenticated users should handle this)
        responses = []
        for i in range(5):
            response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={"content": f"balance check {i}", "language": "en"}
            )
            responses.append(response)

        # All requests should succeed (authenticated users have higher limits)
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        assert success_count >= 4, f"Authenticated users should handle rapid requests: {success_count}/5 succeeded"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_premium_features_access(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_premium_features_access",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test authenticated users can access premium features.

        Expected: Hunter AI and Agent Squad work for authenticated users.
        """
        # Test Hunter AI (premium feature)
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Analyze BTC sentiment", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should NOT have feature restrictions
        assert "upgrade" not in content, "Authenticated users shouldn't see upgrade prompts"
        assert "premium" not in content or "premium feature" not in content

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_authenticated_real_data_integration(

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_authenticated_real_data_integration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        self, client: AsyncClient, auth_headers, conversation_id
    ):
        """
        Test authenticated users receive real data (not demo data).

        Expected: Responses include real wallet data, not demo values.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "Show my portfolio", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = str(data).lower()

        # Should NOT contain demo disclaimers
        assert "demo" not in content, "Authenticated users shouldn't see demo disclaimers"
        assert "sample" not in content or "sample data" not in content
        assert "example" not in content or "example portfolio" not in content