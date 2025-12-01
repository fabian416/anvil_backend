"""
End-to-end tests for complete chat flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID

from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.queries.get_conversation import GetConversation
from app.application.chat.queries.list_conversations import ListConversations
from app.application.chat.queries.get_messages import GetMessages
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole


@pytest.fixture
def mock_repository():
    """Create mock conversation repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_agent_gateway():
    """Create mock agent gateway."""
    gateway = AsyncMock()
    gateway.process_message.return_value = "This is a mock agent response"
    return gateway


class TestChatE2E:
    """End-to-end tests for chat functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_chat_flow(self, mock_repository, mock_agent_gateway):
        """
        Test complete chat flow from start to finish.
        
        Flow:
        1. Create conversation
        2. Send message
        3. Get conversation
        4. List conversations
        5. Get messages
        """
        user_id = 123
        
        # Setup mock repository
        conversations = {}
        messages = []
        
        async def add_conversation(conv):
            # Store or update conversation by ID
            conversations[conv.id] = conv
        
        async def add_message(msg):
            messages.append(msg)
        
        async def get_conversation(conv_id):
            return conversations.get(conv_id)
        
        async def list_convs(user_id, limit, offset):
            return [c for c in conversations.values() if c.user_id == user_id]
        
        async def get_msgs(conv_id, limit):
            return [m for m in messages if m.conversation_id == conv_id]
        
        mock_repository.add_conversation.side_effect = add_conversation
        mock_repository.add_message.side_effect = add_message
        mock_repository.get_conversation.side_effect = get_conversation
        mock_repository.list_conversations.side_effect = list_convs
        mock_repository.get_messages.side_effect = get_msgs
        
        # 1. Create conversation
        create_conv = CreateConversation(mock_repository)
        conversation = await create_conv.execute(user_id=user_id, title="Test Chat")
        
        assert conversation is not None
        assert conversation.user_id == user_id
        assert conversation.title == "Test Chat"
        assert len(conversations) == 1
        
        # 2. Send message
        send_msg = SendMessage(mock_repository, mock_agent_gateway)
        user_message, agent_message = await send_msg.execute(
            user_id=user_id,
            conversation_id=conversation.id,
            content="swap 100 USDC to ETH"
        )
        
        assert user_message.role == MessageRole.USER
        assert user_message.content == "swap 100 USDC to ETH"
        assert agent_message.role == MessageRole.AGENT
        assert agent_message.content == "This is a mock agent response"
        assert len(messages) == 2
        
        # Verify agent gateway was called
        mock_agent_gateway.process_message.assert_called_once()
        
        # 3. Get conversation
        get_conv = GetConversation(mock_repository)
        retrieved_conv = await get_conv.execute(
            user_id=user_id,
            conversation_id=conversation.id
        )
        
        assert retrieved_conv is not None
        assert retrieved_conv.id == conversation.id
        
        # 4. List conversations
        list_convs = ListConversations(mock_repository)
        conv_list = await list_convs.execute(user_id=user_id)
        
        assert len(conv_list) == 1
        assert conv_list[0].id == conversation.id
        
        # 5. Get messages
        get_msgs = GetMessages(mock_repository)
        msg_list = await get_msgs.execute(
            user_id=user_id,
            conversation_id=conversation.id
        )
        
        assert len(msg_list) == 2
        assert msg_list[0].role == MessageRole.USER
        assert msg_list[1].role == MessageRole.AGENT
    
    @pytest.mark.asyncio
    async def test_multiple_messages_in_conversation(
        self,
        mock_repository,
        mock_agent_gateway
    ):
        """Test sending multiple messages in same conversation."""
        user_id = 123
        
        messages = []
        conversation = Conversation.create(user_id=user_id)
        
        mock_repository.get_conversation.return_value = conversation
        mock_repository.add_message.side_effect = lambda m: messages.append(m)
        mock_agent_gateway.process_message.side_effect = [
            "First response",
            "Second response",
            "Third response"
        ]
        
        send_msg = SendMessage(mock_repository, mock_agent_gateway)
        
        # Send 3 messages
        await send_msg.execute(user_id, conversation.id, "First message")
        await send_msg.execute(user_id, conversation.id, "Second message")
        await send_msg.execute(user_id, conversation.id, "Third message")
        
        # Should have 6 messages (3 user + 3 agent)
        assert len(messages) == 6
        
        # Verify agent was called 3 times
        assert mock_agent_gateway.process_message.call_count == 3
    
    @pytest.mark.asyncio
    async def test_conversation_isolation(self, mock_repository, mock_agent_gateway):
        """Test that conversations are properly isolated."""
        user1_id = 123
        user2_id = 456
        
        conversations = {}
        
        async def add_conv(c):
            conversations[c.id] = c
        
        async def list_convs(uid, limit, offset):
            return [c for c in conversations.values() if c.user_id == uid]
        
        mock_repository.add_conversation.side_effect = add_conv
        mock_repository.list_conversations.side_effect = list_convs
        
        # Create conversations for both users
        create_conv = CreateConversation(mock_repository)
        
        conv1 = await create_conv.execute(user_id=user1_id)
        conv2 = await create_conv.execute(user_id=user2_id)
        conv3 = await create_conv.execute(user_id=user1_id)
        
        # List conversations for user 1
        list_convs = ListConversations(mock_repository)
        user1_convs = await list_convs.execute(user_id=user1_id)
        
        assert len(user1_convs) == 2
        assert conv1.id in [c.id for c in user1_convs]
        assert conv3.id in [c.id for c in user1_convs]
        assert conv2.id not in [c.id for c in user1_convs]
        
        # List conversations for user 2
        user2_convs = await list_convs.execute(user_id=user2_id)
        
        assert len(user2_convs) == 1
        assert conv2.id in [c.id for c in user2_convs]
    
    @pytest.mark.asyncio
    async def test_conversation_ownership_check(self, mock_repository):
        """Test that users can only access their own conversations."""
        user1_id = 123
        user2_id = 456
        
        conversation = Conversation.create(user_id=user1_id)
        mock_repository.get_conversation.return_value = conversation
        
        get_conv = GetConversation(mock_repository)
        
        # User 1 can access their conversation
        result = await get_conv.execute(user1_id, conversation.id)
        assert result is not None
        
        # User 2 cannot access user 1's conversation
        with pytest.raises(ValueError, match="does not belong to user"):
            await get_conv.execute(user2_id, conversation.id)
    
    @pytest.mark.asyncio
    async def test_error_handling_conversation_not_found(
        self,
        mock_repository,
        mock_agent_gateway
    ):
        """Test error handling when conversation doesn't exist."""
        user_id = 123
        fake_conv_id = uuid4()
        
        mock_repository.get_conversation.return_value = None
        
        send_msg = SendMessage(mock_repository, mock_agent_gateway)
        
        with pytest.raises(ValueError, match="Conversation .* not found"):
            await send_msg.execute(
                user_id=user_id,
                conversation_id=fake_conv_id,
                content="test"
            )


class TestWebSocketIntegration:
    """Test WebSocket integration with chat."""
    
    @pytest.mark.asyncio
    async def test_message_broadcast_on_send(self, mock_repository, mock_agent_gateway):
        """Test that messages are broadcast via WebSocket."""
        user_id = 123
        conversation = Conversation.create(user_id=user_id)
        
        mock_repository.get_conversation.return_value = conversation
        mock_agent_gateway.process_message.return_value = "Agent response"
        
        send_msg = SendMessage(mock_repository, mock_agent_gateway)
        
        # Send message (WebSocket broadcast happens in background)
        user_message, agent_message = await send_msg.execute(
            user_id=user_id,
            conversation_id=conversation.id,
            content="Test message"
        )
        
        # Verify messages were created
        assert user_message is not None
        assert agent_message is not None
        
        # Note: WebSocket broadcast is fire-and-forget
        # Full WebSocket testing requires integration tests with actual connections


class TestAgentIntegration:
    """Test integration with agent gateway."""
    
    @pytest.mark.asyncio
    async def test_agent_receives_correct_context(
        self,
        mock_repository,
        mock_agent_gateway
    ):
        """Test that agent gateway receives correct context."""
        user_id = 123
        conversation = Conversation.create(user_id=user_id)
        
        mock_repository.get_conversation.return_value = conversation
        mock_agent_gateway.process_message.return_value = "Response"
        
        send_msg = SendMessage(mock_repository, mock_agent_gateway)
        
        await send_msg.execute(
            user_id=user_id,
            conversation_id=conversation.id,
            content="swap 100 USDC"
        )
        
        # Verify agent gateway was called with correct parameters
        call_args = mock_agent_gateway.process_message.call_args
        
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["session_id"] == str(conversation.id)
        assert call_args[1]["message"] == "swap 100 USDC"
