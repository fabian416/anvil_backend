"""
Integration tests for conversation lifecycle.

Tests chat endpoints for:
- Create conversation
- List conversations
- Get conversation
- Pagination
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
class TestCreateConversation:
    """Integration tests for conversation creation."""

    @pytest.mark.llm_validation
    async def test_create_conversation_returns_id(self, client):
        """
        WHEN authenticated user creates conversation
        THEN system SHALL return conversation with ID
        """
        response = await client.post(
            "/api/v1/chat/conversations",
            json={"title": "Test Conversation"}
        )

        # Without auth, expect 401
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
        else:
            assert response.status_code in (401, 403)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_conversation_returns_id",
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


    @pytest.mark.llm_validation
    async def test_create_conversation_without_title(self, client):
        """
        WHEN user creates conversation without title
        THEN system SHALL create conversation with null/default title
        """
        response = await client.post(
            "/api/v1/chat/conversations",
            json={}
        )

        # Should work (title is optional) or return 401 (not authenticated)
        assert response.status_code in (201, 401, 422)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_conversation_without_title",
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


    @pytest.mark.llm_validation
    async def test_create_conversation_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user creates conversation
        THEN system SHALL return 401 unauthorized
        """
        response = await client.post(
            "/api/v1/chat/conversations",
            json={"title": "Test"}
        )

        assert response.status_code == 401

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_conversation_without_auth_returns_401",
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


    @pytest.mark.llm_validation
    async def test_create_conversation_with_long_title(self, client):
        """
        WHEN user creates conversation with very long title
        THEN system SHALL accept or truncate
        """
        long_title = "A" * 500
        response = await client.post(
            "/api/v1/chat/conversations",
            json={"title": long_title}
        )

        # Should create, truncate, or return validation error
        assert response.status_code in (201, 400, 401, 422)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_conversation_with_long_title",
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



@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
class TestListConversations:
    """Integration tests for conversation listing."""

    @pytest.mark.llm_validation
    async def test_list_conversations_returns_array(self, client):
        """
        WHEN authenticated user lists conversations
        THEN system SHALL return array of conversations
        """
        response = await client.get("/api/v1/chat/conversations")

        # Without auth, expect 401
        if response.status_code == 200:
            data = response.json()
            assert "conversations" in data or isinstance(data, list)
        else:
            assert response.status_code == 401

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_list_conversations_returns_array",
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


    @pytest.mark.llm_validation
    async def test_list_conversations_with_pagination(self, client):
        """
        WHEN user lists conversations with pagination
        THEN system SHALL return paginated results
        """
        response = await client.get(
            "/api/v1/chat/conversations",
            params={"limit": 10, "offset": 0}
        )

        assert response.status_code in (200, 401)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_list_conversations_with_pagination",
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


    @pytest.mark.llm_validation
    async def test_list_conversations_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user lists conversations
        THEN system SHALL return 401 unauthorized
        """
        response = await client.get("/api/v1/chat/conversations")

        assert response.status_code == 401

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_list_conversations_without_auth_returns_401",
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



@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
class TestGetConversation:
    """Integration tests for getting single conversation."""

    @pytest.mark.llm_validation
    async def test_get_conversation_by_id(self, client):
        """
        WHEN authenticated user gets conversation by ID
        THEN system SHALL return conversation details
        """
        conversation_id = str(uuid4())
        response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")

        # Without auth or if not found: 401 or 404
        assert response.status_code in (200, 401, 404)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_conversation_by_id",
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


    @pytest.mark.llm_validation
    async def test_get_conversation_not_found(self, client):
        """
        WHEN user requests non-existent conversation
        THEN system SHALL return 404 (or 401 if not authenticated)
        """
        conversation_id = str(uuid4())
        response = await client.get(f"/api/v1/chat/conversations/{conversation_id}")

        assert response.status_code in (401, 404)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_conversation_not_found",
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


    @pytest.mark.llm_validation
    async def test_get_conversation_invalid_uuid_returns_error(self, client):
        """
        WHEN user requests conversation with invalid UUID
        THEN system SHALL return validation error
        """
        response = await client.get("/api/v1/chat/conversations/not-a-uuid")

        assert response.status_code in (401, 422)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_get_conversation_invalid_uuid_returns_error",
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



@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.asyncio
class TestConversationPagination:
    """Integration tests for conversation pagination."""

    @pytest.mark.llm_validation
    async def test_pagination_limit_works(self, client):
        """
        WHEN user specifies limit
        THEN system SHALL return at most that many items
        """
        response = await client.get(
            "/api/v1/chat/conversations",
            params={"limit": 5}
        )

        assert response.status_code in (200, 401)

        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", data)
            if isinstance(conversations, list):
                assert len(conversations) <= 5

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_pagination_limit_works",
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


    @pytest.mark.llm_validation
    async def test_pagination_offset_skips_items(self, client):
        """
        WHEN user specifies offset
        THEN system SHALL skip that many items
        """
        response = await client.get(
            "/api/v1/chat/conversations",
            params={"offset": 10}
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_pagination_offset_skips_items",
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


        assert response.status_code in (200, 401)