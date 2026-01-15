"""
Integration tests for authenticated chat system.

⚠️ DEPRECATED: These tests were written for the old AuthChatUser system
which has been replaced by the unified ChatUser system (2026-01-06).

Tests marked with @pytest.mark.skip are deprecated and need to be rewritten
for the new unified chat system. See:
- src/app/domain/chat/entities/chat_user.py (new)
- src/app/domain/chat/entities/authenticated_chat.py (deprecated)
- Migration: 2026_01_06_1500-chat_unified_v2.py

TODO: Rewrite these tests for the unified ChatUser system
Priority: P2 (working tests exist in comprehensive suite)

Tests the complete flow of authenticated user chat:
- Chat user creation/retrieval (bridge to legacy users)
- Chat conversation management
- Chat message creation with Hunter AI metadata
- UnifiedChatHandler with authenticated context
- End-to-end API flow

Day 4: Risk Assessment - Integration Testing
"""

import pytest
import pytest_asyncio
from uuid import UUID, uuid4
from datetime import datetime

from app.domain.chat.entities import ChatUser, ChatConversation, ChatMessage
from app.domain.chat.value_objects import (
    AuthenticatedContext,
    GuestContext,
    FeatureFlags,
)
from app.domain.ports.chat_repository import (
    ChatUserRepository,
    ChatConversationRepository,
    ChatMessageRepository,
)
from app.infrastructure.adapters.chat_repository_sqla import (
    ChatUserRepositorySqla,
    ChatConversationRepositorySqla,
    ChatMessageRepositorySqla,
)
from app.application.chat.commands.get_or_create_chat_user import (
    GetOrCreateChatUserCommand,
)
from app.application.chat.commands.get_or_create_chat_conversation import (
    GetOrCreateChatConversationCommand,
)
from app.application.chat.commands.create_chat_message import (
    CreateChatMessageCommand,
)

from tests.helpers.auth_helper import AuthHelper


@pytest_asyncio.fixture
async def chat_user_repo(async_db_session) -> ChatUserRepository:
    """Provide ChatUserRepository for testing."""
    return ChatUserRepositorySqla(async_db_session)


@pytest_asyncio.fixture
async def chat_conversation_repo(async_db_session) -> ChatConversationRepository:
    """Provide ChatConversationRepository for testing."""
    return ChatConversationRepositorySqla(async_db_session)


@pytest_asyncio.fixture
async def chat_message_repo(async_db_session) -> ChatMessageRepository:
    """Provide ChatMessageRepository for testing."""
    return ChatMessageRepositorySqla(async_db_session)


@pytest_asyncio.fixture
async def legacy_user(async_db_session):
    """Create a legacy user in the users table."""
    user, token = await AuthHelper.create_test_user_in_db(
        db_session=async_db_session,
        email="test@example.com",
        role="user",
    )
    return user


@pytest.mark.skip(reason="DEPRECATED: Tests old AuthChatUser system - needs rewrite for unified ChatUser (P2)")
@pytest.mark.asyncio
class TestChatUserRepository:
    """Test ChatUserRepository operations."""

    async def test_create_chat_user(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN a legacy user in the users table
        WHEN creating a new chat user
        THEN chat user should be created with correct data
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,  # Legacy INTEGER user_id
            email=legacy_user.email,
            subscription_tier="free",
        )

        # Act
        created = await chat_user_repo.create(chat_user)

        # Assert
        assert created.id_ == chat_user.id_
        assert created.user_id == legacy_user.id
        assert created.email == legacy_user.email
        assert created.subscription_tier == "free"
        assert created.total_messages == 0
        assert isinstance(created.created_at, datetime)

    async def test_get_by_user_id(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN an existing chat user
        WHEN retrieving by legacy user_id
        THEN correct chat user should be returned
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
            subscription_tier="premium",
        )
        await chat_user_repo.create(chat_user)

        # Act
        retrieved = await chat_user_repo.get_by_user_id(legacy_user.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id_ == chat_user.id_
        assert retrieved.user_id == legacy_user.id
        assert retrieved.subscription_tier == "premium"

    async def test_update_last_seen(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN an existing chat user
        WHEN updating last_seen_at
        THEN timestamp should be updated
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        created = await chat_user_repo.create(chat_user)
        original_time = created.last_seen_at

        # Act
        await chat_user_repo.update_last_seen(created.id_)

        # Assert
        updated = await chat_user_repo.get_by_id(created.id_)
        assert updated.last_seen_at > original_time

    async def test_get_statistics(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
        async_db_session,
    ):
        """
        GIVEN multiple chat users with different tiers
        WHEN getting statistics
        THEN correct aggregated data should be returned
        """
        # Arrange - Create users with different tiers
        users_data = [
            {"tier": "free", "messages": 10},
            {"tier": "free", "messages": 20},
            {"tier": "premium", "messages": 50},
            {"tier": "enterprise", "messages": 100},
        ]

        for i, data in enumerate(users_data):
            # Create a unique legacy user for each chat user
            user, _ = await AuthHelper.create_test_user_in_db(
                db_session=async_db_session,
                email=f"test{i}@example.com",
                role="user",
            )
            chat_user = ChatUser(
                id_=uuid4(),
                user_id=user.id,
                email=user.email,
                subscription_tier=data["tier"],
                total_messages=data["messages"],
            )
            await chat_user_repo.create(chat_user)

        # Act
        stats = await chat_user_repo.get_statistics()

        # Assert
        assert stats["total_users"] >= 4
        assert stats["total_messages"] >= 180
        assert "free" in stats["users_by_tier"]
        assert "premium" in stats["users_by_tier"]
        assert "enterprise" in stats["users_by_tier"]


@pytest.mark.skip(reason="DEPRECATED: Tests old AuthChatUser system - needs rewrite for unified ChatUser (P2)")
@pytest.mark.asyncio
class TestChatConversationRepository:
    """Test ChatConversationRepository operations."""

    async def test_create_conversation(
        self,
        chat_conversation_repo: ChatConversationRepository,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN a chat user
        WHEN creating a conversation
        THEN conversation should be created with correct data
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
            title="Test Conversation",
        )

        # Act
        created = await chat_conversation_repo.create(conversation)

        # Assert
        assert created.id_ == conversation.id_
        assert created.chat_user_id == chat_user.id_
        assert created.language == "en"
        assert created.title == "Test Conversation"
        assert created.status == "active"
        assert created.message_count == 0

    async def test_get_active_conversation(
        self,
        chat_conversation_repo: ChatConversationRepository,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN multiple conversations (some active, some archived)
        WHEN getting active conversation
        THEN only active conversation for language should be returned
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        # Create archived conversation
        archived = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
            status="archived",
        )
        await chat_conversation_repo.create(archived)

        # Create active conversation
        active = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
            status="active",
        )
        await chat_conversation_repo.create(active)

        # Act
        retrieved = await chat_conversation_repo.get_active_conversation(
            chat_user.id_, "en"
        )

        # Assert
        assert retrieved is not None
        assert retrieved.id_ == active.id_
        assert retrieved.status == "active"

    async def test_increment_message_count(
        self,
        chat_conversation_repo: ChatConversationRepository,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN an existing conversation
        WHEN incrementing message count
        THEN count should increase
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
        )
        created = await chat_conversation_repo.create(conversation)

        # Act
        await chat_conversation_repo.increment_message_count(created.id_)

        # Assert
        updated = await chat_conversation_repo.get_by_id(created.id_)
        assert updated.message_count == 1


@pytest.mark.asyncio
class TestChatMessageRepository:
    """Test ChatMessageRepository operations."""

    async def test_create_message(
        self,
        chat_message_repo: ChatMessageRepository,
        chat_conversation_repo: ChatConversationRepository,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN a conversation
        WHEN creating a message
        THEN message should be created with metadata
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
        )
        conversation = await chat_conversation_repo.create(conversation)

        message = ChatMessage(
            id_=uuid4(),
            conversation_id=conversation.id_,
            role="user",
            content="What's the sentiment for BTC?",
            intent="hunter_sentiment",
            language="en",
            metadata={
                "token": "BTC",
                "price": 45000.0,
                "sentiment_score": 0.75,
            },
        )

        # Act
        created = await chat_message_repo.create(message)

        # Assert
        assert created.id_ == message.id_
        assert created.conversation_id == conversation.id_
        assert created.role == "user"
        assert created.content == "What's the sentiment for BTC?"
        assert created.intent == "hunter_sentiment"
        assert created.metadata["token"] == "BTC"
        assert created.metadata["sentiment_score"] == 0.75

    async def test_list_by_conversation(
        self,
        chat_message_repo: ChatMessageRepository,
        chat_conversation_repo: ChatConversationRepository,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN multiple messages in a conversation
        WHEN listing by conversation
        THEN all messages should be returned in order
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
        )
        conversation = await chat_conversation_repo.create(conversation)

        # Create user message
        msg1 = ChatMessage(
            id_=uuid4(),
            conversation_id=conversation.id_,
            role="user",
            content="Hello",
        )
        await chat_message_repo.create(msg1)

        # Create assistant message
        msg2 = ChatMessage(
            id_=uuid4(),
            conversation_id=conversation.id_,
            role="assistant",
            content="Hi! How can I help?",
        )
        await chat_message_repo.create(msg2)

        # Act
        messages = await chat_message_repo.list_by_conversation(conversation.id_)

        # Assert
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"


@pytest.mark.asyncio
class TestCommandHandlers:
    """Test command handler integration."""

    async def test_get_or_create_chat_user_command(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN a legacy user
        WHEN executing GetOrCreateChatUser command
        THEN chat user should be created or retrieved
        """
        # Arrange
        command = GetOrCreateChatUserCommand(chat_user_repository=chat_user_repo)

        # Act - First call creates
        chat_user1 = await command.execute(
            user_id=legacy_user.id,
            email=legacy_user.email,
            subscription_tier="free",
        )

        # Act - Second call retrieves
        chat_user2 = await command.execute(
            user_id=legacy_user.id,
            email=legacy_user.email,
            subscription_tier="free",
        )

        # Assert
        assert chat_user1.id_ == chat_user2.id_
        assert chat_user1.user_id == legacy_user.id

    async def test_get_or_create_chat_user_updates_tier(
        self,
        chat_user_repo: ChatUserRepository,
        legacy_user,
    ):
        """
        GIVEN an existing chat user with free tier
        WHEN executing command with premium tier
        THEN subscription tier should be updated
        """
        # Arrange
        command = GetOrCreateChatUserCommand(chat_user_repository=chat_user_repo)

        # Act - Create with free tier
        chat_user1 = await command.execute(
            user_id=legacy_user.id,
            email=legacy_user.email,
            subscription_tier="free",
        )

        # Act - Update to premium tier
        chat_user2 = await command.execute(
            user_id=legacy_user.id,
            email=legacy_user.email,
            subscription_tier="premium",
        )

        # Assert
        assert chat_user1.id_ == chat_user2.id_
        assert chat_user2.subscription_tier == "premium"

    async def test_get_or_create_conversation_command(
        self,
        chat_user_repo: ChatUserRepository,
        chat_conversation_repo: ChatConversationRepository,
        legacy_user,
    ):
        """
        GIVEN a chat user
        WHEN executing GetOrCreateChatConversation command
        THEN active conversation should be returned
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        command = GetOrCreateChatConversationCommand(
            chat_conversation_repository=chat_conversation_repo
        )

        # Act - First call creates
        conv1 = await command.execute(chat_user.id_, "en")

        # Act - Second call retrieves same
        conv2 = await command.execute(chat_user.id_, "en")

        # Assert
        assert conv1.id_ == conv2.id_
        assert conv1.language == "en"

    async def test_create_message_command(
        self,
        chat_user_repo: ChatUserRepository,
        chat_conversation_repo: ChatConversationRepository,
        chat_message_repo: ChatMessageRepository,
        legacy_user,
    ):
        """
        GIVEN a conversation
        WHEN executing CreateChatMessage command
        THEN message should be created and count incremented
        """
        # Arrange
        chat_user = ChatUser(
            id_=uuid4(),
            user_id=legacy_user.id,
            email=legacy_user.email,
        )
        chat_user = await chat_user_repo.create(chat_user)

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user.id_,
            language="en",
        )
        conversation = await chat_conversation_repo.create(conversation)

        command = CreateChatMessageCommand(
            chat_message_repository=chat_message_repo,
            chat_conversation_repository=chat_conversation_repo,
        )

        # Act
        message = await command.execute(
            conversation_id=conversation.id_,
            role="user",
            content="Test message",
            intent="hunter_sentiment",
            enrichment={"token": "BTC"},
        )

        # Assert
        assert message.content == "Test message"
        assert message.intent == "hunter_sentiment"
        assert message.metadata["token"] == "BTC"

        # Verify count incremented
        updated_conv = await chat_conversation_repo.get_by_id(conversation.id_)
        assert updated_conv.message_count == 1


@pytest.mark.asyncio
class TestAuthenticatedContext:
    """Test AuthenticatedContext value object."""

    def test_authenticated_context_creation(self):
        """
        GIVEN user data
        WHEN creating AuthenticatedContext
        THEN correct values should be set
        """
        # Act
        context = AuthenticatedContext(
            user_id=123,
            email="test@example.com",
            subscription_tier="premium",
        )

        # Assert
        assert context.user_id == 123
        assert context.email == "test@example.com"
        assert context.subscription_tier == "premium"
        assert context.is_authenticated() is True
        assert context.get_user_id() == "auth:123"

    def test_rate_limits_by_tier(self):
        """
        GIVEN different subscription tiers
        WHEN getting rate limits
        THEN correct limits should be returned
        """
        # Free tier
        free_context = AuthenticatedContext(
            user_id=1,
            email="free@example.com",
            subscription_tier="free",
        )
        assert free_context.get_rate_limit() == (1000, 3600)

        # Premium tier
        premium_context = AuthenticatedContext(
            user_id=2,
            email="premium@example.com",
            subscription_tier="premium",
        )
        assert premium_context.get_rate_limit() == (10000, 3600)

        # Enterprise tier
        enterprise_context = AuthenticatedContext(
            user_id=3,
            email="enterprise@example.com",
            subscription_tier="enterprise",
        )
        assert enterprise_context.get_rate_limit() == (10000, 3600)


@pytest.mark.asyncio
class TestFeatureFlags:
    """Test FeatureFlags for authenticated users."""

    def test_guest_features(self):
        """
        GIVEN a guest context
        WHEN creating feature flags
        THEN only basic features should be enabled
        """
        # Arrange
        context = GuestContext(ip_address="1.2.3.4")

        # Act
        features = FeatureFlags.from_context(context)

        # Assert
        assert features.hunter_sentiment is True
        assert features.hunter_trading_signals is True
        assert features.hunter_price_prediction is True
        assert features.hunter_patterns is False
        assert features.hunter_portfolio is False
        assert features.hunter_risk_signals is False

    def test_free_tier_features(self):
        """
        GIVEN a free tier authenticated user
        WHEN creating feature flags
        THEN basic + premium features should be enabled
        """
        # Arrange
        context = AuthenticatedContext(
            user_id=1,
            email="free@example.com",
            subscription_tier="free",
        )

        # Act
        features = FeatureFlags.from_context(context)

        # Assert
        # Basic features
        assert features.hunter_sentiment is True
        assert features.hunter_trading_signals is True
        assert features.hunter_price_prediction is True
        # Premium features
        assert features.hunter_patterns is True
        assert features.hunter_portfolio is True
        assert features.hunter_risk_signals is True
        # Advanced features (disabled)
        assert features.export_conversations is False
        assert features.api_access is False

    def test_premium_tier_features(self):
        """
        GIVEN a premium tier user
        WHEN creating feature flags
        THEN basic + premium + advanced features should be enabled
        """
        # Arrange
        context = AuthenticatedContext(
            user_id=1,
            email="premium@example.com",
            subscription_tier="premium",
        )

        # Act
        features = FeatureFlags.from_context(context)

        # Assert
        # Advanced features enabled
        assert features.export_conversations is True
        assert features.unlimited_history is True
        assert features.advanced_analytics is True
        assert features.api_access is True
        # Enterprise features disabled
        assert features.team_collaboration is False
        assert features.sso_integration is False

    def test_intent_allowed(self):
        """
        GIVEN different feature flags
        WHEN checking intent allowed
        THEN correct result should be returned
        """
        # Guest - only basic intents
        guest_context = GuestContext(ip_address="1.2.3.4")
        guest_features = FeatureFlags.from_context(guest_context)

        assert guest_features.is_intent_allowed("hunter_sentiment") is True
        assert guest_features.is_intent_allowed("hunter_patterns") is False

        # Premium - all intents
        premium_context = AuthenticatedContext(
            user_id=1,
            email="premium@example.com",
            subscription_tier="premium",
        )
        premium_features = FeatureFlags.from_context(premium_context)

        assert premium_features.is_intent_allowed("hunter_sentiment") is True
        assert premium_features.is_intent_allowed("hunter_patterns") is True
