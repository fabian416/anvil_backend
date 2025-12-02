"""
Tests for infrastructure repository structure.

Tests that repository implementations exist and have correct structure.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
class TestRepositoryStructure:
    """Test repository implementation structure."""
    
    def test_llm_conversation_repository_exists(self):
        """Test LLMConversationRepositorySqla exists."""
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        assert LLMConversationRepositorySqla is not None
        assert hasattr(LLMConversationRepositorySqla, '__init__')
    
    def test_notification_repository_exists(self):
        """Test NotificationRepositorySqla exists."""
        from app.infrastructure.adapters.notification_repository_sqla import NotificationRepositorySqla
        
        assert NotificationRepositorySqla is not None
        assert hasattr(NotificationRepositorySqla, '__init__')
    
    def test_user_metrics_repository_exists(self):
        """Test UserMetricsRepositorySqla exists."""
        from app.infrastructure.adapters.user_metrics_repository_sqla import UserMetricsRepositorySqla
        
        assert UserMetricsRepositorySqla is not None
        assert hasattr(UserMetricsRepositorySqla, '__init__')
    
    def test_subscription_repository_exists(self):
        """Test SubscriptionRepositorySqla exists."""
        from app.infrastructure.adapters.subscription_repository_sqla import SubscriptionRepositorySqla
        
        assert SubscriptionRepositorySqla is not None
    
    def test_payment_repository_exists(self):
        """Test PaymentRepositorySqla exists."""
        from app.infrastructure.adapters.payment_repository_sqla import PaymentRepositorySqla
        
        assert PaymentRepositorySqla is not None
    
    def test_password_reset_repository_exists(self):
        """Test PasswordResetRepositorySqla exists."""
        from app.infrastructure.adapters.password_reset_repository_sqla import PasswordResetRepositorySqla
        
        assert PasswordResetRepositorySqla is not None
    
    def test_email_verification_repository_exists(self):
        """Test EmailVerificationRepositorySqla exists."""
        from app.infrastructure.adapters.email_verification_repository_sqla import EmailVerificationRepositorySqla
        
        assert EmailVerificationRepositorySqla is not None
    
    def test_model_config_repository_exists(self):
        """Test ModelConfigRepositorySqla exists."""
        from app.infrastructure.adapters.ai.model_config_repository_sqla import ModelConfigRepositorySqla
        
        assert ModelConfigRepositorySqla is not None
    
    def test_agent_execution_repository_exists(self):
        """Test AgentExecutionRepositorySqla exists."""
        from app.infrastructure.adapters.ai.agent_execution_repository_sqla import AgentExecutionRepositorySqla
        
        assert AgentExecutionRepositorySqla is not None
    
    def test_conversation_context_repository_exists(self):
        """Test ConversationContextRepositorySqla exists."""
        from app.infrastructure.adapters.conversation_context_repository_sqla import ConversationContextRepositorySqla
        
        assert ConversationContextRepositorySqla is not None


@pytest.mark.unit
class TestRepositoryDependencies:
    """Test repository dependency injection."""
    
    def test_llm_conversation_repository_accepts_session(self):
        """Test LLMConversationRepositorySqla accepts session."""
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        mock_session = MagicMock()
        repo = LLMConversationRepositorySqla(session=mock_session)
        
        assert repo is not None
        assert repo.session is mock_session
    
    def test_notification_repository_accepts_session(self):
        """Test NotificationRepositorySqla accepts session."""
        from app.infrastructure.adapters.notification_repository_sqla import NotificationRepositorySqla
        
        mock_session = MagicMock()
        repo = NotificationRepositorySqla(session=mock_session)
        
        assert repo is not None
        assert repo.session is mock_session
    
    def test_user_metrics_repository_accepts_session(self):
        """Test UserMetricsRepositorySqla accepts session."""
        from app.infrastructure.adapters.user_metrics_repository_sqla import UserMetricsRepositorySqla
        
        mock_session = MagicMock()
        repo = UserMetricsRepositorySqla(session=mock_session)
        
        assert repo is not None
        assert repo.session is mock_session


@pytest.mark.unit
class TestRepositoryMethods:
    """Test repository methods exist."""
    
    def test_llm_conversation_repository_has_add_method(self):
        """Test LLMConversationRepositorySqla has add method."""
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        mock_session = MagicMock()
        repo = LLMConversationRepositorySqla(session=mock_session)
        
        assert hasattr(repo, 'add')
        assert callable(getattr(repo, 'add', None))
    
    def test_notification_repository_has_create_method(self):
        """Test NotificationRepositorySqla has create method."""
        from app.infrastructure.adapters.notification_repository_sqla import NotificationRepositorySqla
        
        mock_session = MagicMock()
        repo = NotificationRepositorySqla(session=mock_session)
        
        assert hasattr(repo, 'create')
        assert callable(getattr(repo, 'create', None))
    
    def test_user_metrics_repository_has_track_event_method(self):
        """Test UserMetricsRepositorySqla has track_event method."""
        from app.infrastructure.adapters.user_metrics_repository_sqla import UserMetricsRepositorySqla
        
        mock_session = MagicMock()
        repo = UserMetricsRepositorySqla(session=mock_session)
        
        assert hasattr(repo, 'track_event')
        assert callable(getattr(repo, 'track_event', None))
    
    def test_notification_repository_has_get_user_notifications_method(self):
        """Test NotificationRepositorySqla has get_user_notifications method."""
        from app.infrastructure.adapters.notification_repository_sqla import NotificationRepositorySqla
        
        mock_session = MagicMock()
        repo = NotificationRepositorySqla(session=mock_session)
        
        assert hasattr(repo, 'get_user_notifications')
        assert callable(getattr(repo, 'get_user_notifications', None))
    
    def test_user_metrics_repository_has_get_user_metrics_summary_method(self):
        """Test UserMetricsRepositorySqla has get_user_metrics_summary method."""
        from app.infrastructure.adapters.user_metrics_repository_sqla import UserMetricsRepositorySqla
        
        mock_session = MagicMock()
        repo = UserMetricsRepositorySqla(session=mock_session)
        
        assert hasattr(repo, 'get_user_metrics_summary')
        assert callable(getattr(repo, 'get_user_metrics_summary', None))
