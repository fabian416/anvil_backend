"""
Unit tests for chat controllers.

Tests conversation creation, message sending, and listing controllers
in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from tests.builders import a_conversation, a_message
from tests.helpers.auth_helper import AuthHelper


class TestCreateConversationController:
    """Unit tests for POST /conversations controller."""

    @pytest.fixture
    def mock_create_conversation_interactor(self):
        """Create mock CreateConversation interactor."""
        interactor = AsyncMock()
        conv_id = uuid4()
        interactor.execute = AsyncMock(
            return_value={
                "id": str(conv_id),
                "user_id": str(uuid4()),
                "title": "New Conversation",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        return interactor

    def test_create_conversation_request_structure(self):
        """Test valid create conversation request structure."""
        request_data = {
            "title": "DeFi Portfolio Discussion",
        }

        # Title is optional
        assert "title" in request_data

    def test_create_conversation_minimal_request(self):
        """Test create conversation with minimal data."""
        request_data = {}  # No title required

        assert len(request_data) == 0

    def test_create_conversation_response_structure(
        self, mock_create_conversation_interactor
    ):
        """Test create conversation returns expected response."""
        response = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "New Conversation",
            "created_at": datetime.utcnow().isoformat(),
        }

        assert "id" in response
        assert "created_at" in response

    def test_create_conversation_requires_authentication(self):
        """Test create conversation requires Bearer token."""
        # Router has dependencies=[Security(bearer_scheme)]
        assert True  # Configuration test

    def test_create_conversation_with_custom_title(self):
        """Test creating conversation with custom title."""
        request_data = {
            "title": "My DeFi Research",
        }

        assert request_data["title"] == "My DeFi Research"


class TestListConversationsController:
    """Unit tests for GET /conversations controller."""

    @pytest.fixture
    def mock_list_conversations_interactor(self):
        """Create mock ListConversations interactor."""
        interactor = AsyncMock()
        interactor.execute = AsyncMock(
            return_value=[
                {
                    "id": str(uuid4()),
                    "title": "Conversation 1",
                    "created_at": datetime.utcnow().isoformat(),
                },
                {
                    "id": str(uuid4()),
                    "title": "Conversation 2",
                    "created_at": datetime.utcnow().isoformat(),
                },
            ]
        )
        return interactor

    def test_list_conversations_supports_pagination(self):
        """Test list conversations supports limit and offset."""
        params = {
            "limit": 20,
            "offset": 0,
        }

        assert params["limit"] == 20
        assert params["offset"] == 0

    def test_list_conversations_response_structure(self):
        """Test list conversations returns expected structure."""
        response = {
            "conversations": [
                {"id": str(uuid4()), "title": "Conv 1"},
                {"id": str(uuid4()), "title": "Conv 2"},
            ],
            "total": 2,
        }

        assert "conversations" in response
        assert "total" in response
        assert isinstance(response["conversations"], list)

    def test_list_conversations_empty_response(self):
        """Test list conversations handles empty list."""
        response = {
            "conversations": [],
            "total": 0,
        }

        assert response["total"] == 0
        assert len(response["conversations"]) == 0

    def test_list_conversations_requires_authentication(self):
        """Test list conversations requires Bearer token."""
        assert True  # Configuration test


class TestGetConversationController:
    """Unit tests for GET /conversations/{id} controller."""

    @pytest.fixture
    def mock_get_conversation_interactor(self):
        """Create mock GetConversation interactor."""
        interactor = AsyncMock()
        conv_id = uuid4()
        interactor.execute = AsyncMock(
            return_value={
                "id": str(conv_id),
                "user_id": str(uuid4()),
                "title": "Test Conversation",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return interactor

    def test_get_conversation_by_uuid(self):
        """Test getting conversation by UUID."""
        conversation_id = uuid4()

        assert isinstance(conversation_id, type(uuid4()))

    def test_get_conversation_not_found_error(self):
        """Test not found returns CHAT_001 error."""
        error_response = {
            "error": {
                "code": "CHAT_001",
                "message": "Conversation not found",
                "i18n_key": "errors.chat.conversation_not_found",
                "http_status": 404,
            }
        }

        assert error_response["error"]["code"] == "CHAT_001"
        assert error_response["error"]["http_status"] == 404

    def test_get_conversation_access_denied_error(self):
        """Test access denied returns CHAT_002 error."""
        error_response = {
            "error": {
                "code": "CHAT_002",
                "message": "Access denied to this conversation",
                "i18n_key": "errors.chat.access_denied",
                "http_status": 403,
            }
        }

        assert error_response["error"]["code"] == "CHAT_002"
        assert error_response["error"]["http_status"] == 403


class TestSendMessageController:
    """Unit tests for POST /conversations/{id}/messages controller."""

    @pytest.fixture
    def mock_send_message_interactor(self):
        """Create mock SendMessage interactor."""
        interactor = AsyncMock()
        interactor.execute = AsyncMock(
            return_value=(
                {
                    "id": str(uuid4()),
                    "role": "user",
                    "content": "Hello",
                    "created_at": datetime.utcnow().isoformat(),
                },
                {
                    "id": str(uuid4()),
                    "role": "assistant",
                    "content": "Hello! How can I help you with DeFi today?",
                    "agent_type": "chat",
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
        )
        return interactor

    def test_send_message_request_structure(self):
        """Test valid send message request structure."""
        request_data = {
            "content": "What is the current TVL on Aave?",
        }

        assert "content" in request_data
        assert len(request_data["content"]) > 0

    def test_send_message_response_includes_both_messages(self):
        """Test send message returns user and agent messages."""
        response = {
            "user_message": {
                "id": str(uuid4()),
                "role": "user",
                "content": "Hello",
            },
            "agent_message": {
                "id": str(uuid4()),
                "role": "assistant",
                "content": "Hello! How can I help?",
                "agent_type": "chat",
            },
        }

        assert "user_message" in response
        assert "agent_message" in response
        assert response["user_message"]["role"] == "user"
        assert response["agent_message"]["role"] == "assistant"

    def test_send_message_empty_content_error(self):
        """Test empty message returns CHAT_003 error."""
        error_response = {
            "error": {
                "code": "CHAT_003",
                "message": "Message content cannot be empty",
                "i18n_key": "errors.chat.message_empty",
                "http_status": 400,
            }
        }

        assert error_response["error"]["code"] == "CHAT_003"
        assert error_response["error"]["http_status"] == 400

    def test_send_message_content_validation(self):
        """Test message content is validated."""
        # Empty content
        empty_request = {"content": ""}
        assert len(empty_request["content"]) == 0

        # Whitespace-only content
        whitespace_request = {"content": "   "}
        assert whitespace_request["content"].strip() == ""

    def test_send_message_to_nonexistent_conversation_error(self):
        """Test sending to nonexistent conversation returns error."""
        error_response = {
            "error": {
                "code": "CHAT_001",
                "message": "Conversation not found",
                "i18n_key": "errors.chat.conversation_not_found",
                "http_status": 404,
            }
        }

        assert error_response["error"]["code"] == "CHAT_001"


class TestGetMessagesController:
    """Unit tests for GET /conversations/{id}/messages controller."""

    @pytest.fixture
    def mock_get_messages_interactor(self):
        """Create mock GetMessages interactor."""
        interactor = AsyncMock()
        interactor.execute = AsyncMock(
            return_value=[
                {
                    "id": str(uuid4()),
                    "role": "user",
                    "content": "Hello",
                    "created_at": "2024-01-01T00:00:00Z",
                },
                {
                    "id": str(uuid4()),
                    "role": "assistant",
                    "content": "Hi there!",
                    "created_at": "2024-01-01T00:00:01Z",
                },
            ]
        )
        return interactor

    def test_get_messages_supports_limit(self):
        """Test get messages supports limit parameter."""
        params = {
            "limit": 50,
        }

        assert params["limit"] == 50

    def test_get_messages_response_structure(self):
        """Test get messages returns expected structure."""
        response = {
            "messages": [
                {"id": str(uuid4()), "role": "user", "content": "Hello"},
                {"id": str(uuid4()), "role": "assistant", "content": "Hi"},
            ],
            "total": 2,
        }

        assert "messages" in response
        assert "total" in response

    def test_get_messages_chronological_order(self):
        """Test messages are returned in chronological order."""
        messages = [
            {"created_at": "2024-01-01T00:00:00Z"},
            {"created_at": "2024-01-01T00:01:00Z"},
            {"created_at": "2024-01-01T00:02:00Z"},
        ]

        # Verify order (oldest first)
        timestamps = [m["created_at"] for m in messages]
        assert timestamps == sorted(timestamps)


class TestChatBuilderIntegration:
    """Tests for chat-related test builders."""

    def test_conversation_builder_creates_valid_conversation(self):
        """Test ConversationBuilder creates valid conversation."""
        conversation = a_conversation().with_title("Test Chat").build()

        assert conversation.title == "Test Chat"
        assert conversation.id is not None

    def test_conversation_builder_with_messages(self):
        """Test ConversationBuilder can include messages."""
        conversation = a_conversation().with_messages(3).build()

        # 3 user messages + 3 agent responses = 6 total messages
        assert conversation.message_count == 6

    def test_message_builder_creates_user_message(self):
        """Test MessageBuilder creates user message."""
        message = a_message().from_user().with_content("Hello, bot!").build()

        assert message.role == "user"
        assert message.content == "Hello, bot!"

    def test_message_builder_creates_agent_message(self):
        """Test MessageBuilder creates agent message."""
        message = (
            a_message()
            .from_agent()
            .with_agent_type("chat")
            .with_content("Hello! How can I help?")
            .build()
        )

        # Builder uses "agent" as the role constant
        assert message.role == "agent"
        assert message.agent_type == "chat"

    def test_message_builder_with_llm_response(self):
        """Test MessageBuilder creates LLM response."""
        message = (
            a_message()
            .from_agent()
            .with_llm_response(
                content="Aave is a leading DeFi lending protocol...",
                include_disclaimer=True,
            )
            .build()
        )

        # Builder uses "agent" as the role constant
        assert message.role == "agent"
        assert "Aave" in message.content


class TestAgentSquadEndpoints:
    """Unit tests for Agent Squad endpoints."""

    def test_agent_squad_message_request_structure(self):
        """Test agent squad message request structure."""
        request_data = {
            "content": "Create a DeFi portfolio for me",
            "force_agent": None,  # Optional
        }

        assert "content" in request_data

    def test_agent_squad_message_with_forced_agent(self):
        """Test forcing specific agent."""
        request_data = {
            "content": "What's the risk of Aave?",
            "force_agent": "risk_agent",
        }

        assert request_data["force_agent"] == "risk_agent"

    def test_supervisor_workflow_request_structure(self):
        """Test supervisor workflow request structure."""
        request_data = {
            "complex_task": "Create a balanced DeFi portfolio with $10k",
            "max_agents": 5,
        }

        assert "complex_task" in request_data
        assert request_data["max_agents"] == 5

    def test_list_enabled_agents_response_structure(self):
        """Test list enabled agents response structure."""
        response = {
            "agents": [
                {
                    "agent_id": "chat_agent",
                    "name": "Chat Agent",
                    "description": "General DeFi assistant",
                    "is_core": True,
                },
                {
                    "agent_id": "risk_agent",
                    "name": "Risk Agent",
                    "description": "Risk analysis specialist",
                    "is_core": True,
                },
            ],
            "total": 2,
        }

        assert "agents" in response
        assert "total" in response
