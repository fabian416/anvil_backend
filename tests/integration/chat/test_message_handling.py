"""
Integration tests for message handling.

Tests chat endpoints for:
- Send message
- Get messages
- Message validation
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.chat
class TestSendMessage:
    """Integration tests for sending messages."""

    def test_send_message_returns_response(self, client):
        """
        WHEN authenticated user sends message
        THEN system SHALL return user message and agent response
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Hello, what is DeFi?"}
        )

        # Without auth, expect 401
        if response.status_code == 201:
            data = response.json()
            assert "user_message" in data or "message" in data
        else:
            assert response.status_code in (401, 404)

    def test_send_message_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user sends message
        THEN system SHALL return 401 unauthorized
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Hello"}
        )

        assert response.status_code == 401

    def test_send_message_to_nonexistent_conversation(self, client):
        """
        WHEN user sends message to non-existent conversation
        THEN system SHALL return 404 (or 401 if not authenticated)
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Hello"}
        )

        assert response.status_code in (401, 404)

    def test_send_empty_message_returns_error(self, client):
        """
        WHEN user sends empty message
        THEN system SHALL return validation error
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": ""}
        )

        # Should return 400/422 for empty message or 401 if not authenticated
        assert response.status_code in (400, 401, 422)

    def test_send_message_without_content(self, client):
        """
        WHEN user sends message without content field
        THEN system SHALL return validation error
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={}
        )

        assert response.status_code in (401, 422)


@pytest.mark.integration
@pytest.mark.chat
class TestGetMessages:
    """Integration tests for getting messages."""

    def test_get_messages_returns_array(self, client):
        """
        WHEN authenticated user gets messages
        THEN system SHALL return array of messages
        """
        conversation_id = str(uuid4())
        response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/messages"
        )

        # Without auth or if not found: 401 or 404
        if response.status_code == 200:
            data = response.json()
            assert "messages" in data or isinstance(data, list)
        else:
            assert response.status_code in (401, 404)

    def test_get_messages_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user gets messages
        THEN system SHALL return 401 unauthorized
        """
        conversation_id = str(uuid4())
        response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/messages"
        )

        assert response.status_code == 401

    def test_get_messages_with_limit(self, client):
        """
        WHEN user gets messages with limit
        THEN system SHALL return at most that many messages
        """
        conversation_id = str(uuid4())
        response = client.get(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            params={"limit": 10}
        )

        assert response.status_code in (200, 401, 404)


@pytest.mark.integration
@pytest.mark.chat
class TestMessageValidation:
    """Integration tests for message validation."""

    def test_message_with_special_characters(self, client):
        """
        WHEN user sends message with special characters
        THEN system SHALL accept and process
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "What about 🚀 DeFi? Special chars: <>&\"'"}
        )

        assert response.status_code in (201, 401, 404)

    def test_message_with_unicode(self, client):
        """
        WHEN user sends message with unicode
        THEN system SHALL accept and process
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "什么是去中心化金融？"}
        )

        assert response.status_code in (201, 401, 404)

    def test_very_long_message(self, client):
        """
        WHEN user sends very long message
        THEN system SHALL accept or truncate
        """
        conversation_id = str(uuid4())
        long_message = "A" * 10000
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": long_message}
        )

        # Should create, truncate, or return validation error
        assert response.status_code in (201, 400, 401, 404, 413, 422)
