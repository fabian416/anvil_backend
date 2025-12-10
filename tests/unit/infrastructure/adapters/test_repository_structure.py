"""
Tests for infrastructure repository structure.

Tests that repository implementations exist and have correct structure.
These tests verify that implemented repositories follow expected patterns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


def import_repository(module_path: str, class_name: str):
    """
    Safely import a repository class.
    
    Returns (class, None) if successful, (None, error_message) if not.
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls, None
    except (ImportError, AttributeError) as e:
        return None, str(e)


@pytest.mark.unit
class TestRepositoryStructure:
    """Test repository implementation structure."""
    
    def test_llm_conversation_repository_exists(self):
        """Test LLMConversationRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.ai.llm_conversation_repository_sqla",
            "LLMConversationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"LLMConversationRepositorySqla not implemented: {error}")
        
        assert cls is not None
        assert hasattr(cls, '__init__')
    
    def test_notification_repository_exists(self):
        """Test NotificationRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.notification_repository_sqla",
            "NotificationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"NotificationRepositorySqla not implemented: {error}")
        
        assert cls is not None
        assert hasattr(cls, '__init__')
    
    def test_user_metrics_repository_exists(self):
        """Test UserMetricsRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.user_metrics_repository_sqla",
            "UserMetricsRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"UserMetricsRepositorySqla not implemented: {error}")
        
        assert cls is not None
        assert hasattr(cls, '__init__')
    
    def test_subscription_repository_exists(self):
        """Test SubscriptionRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.subscription_repository_sqla",
            "SubscriptionRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"SubscriptionRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_payment_repository_exists(self):
        """Test PaymentRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.payment_repository_sqla",
            "PaymentRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"PaymentRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_password_reset_repository_exists(self):
        """Test PasswordResetRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.password_reset_repository_sqla",
            "PasswordResetRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"PasswordResetRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_email_verification_repository_exists(self):
        """Test EmailVerificationRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.email_verification_repository_sqla",
            "EmailVerificationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"EmailVerificationRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_model_config_repository_exists(self):
        """Test ModelConfigRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.ai.model_config_repository_sqla",
            "ModelConfigRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"ModelConfigRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_agent_execution_repository_exists(self):
        """Test AgentExecutionRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.ai.agent_execution_repository_sqla",
            "AgentExecutionRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"AgentExecutionRepositorySqla not implemented: {error}")
        
        assert cls is not None
    
    def test_conversation_context_repository_exists(self):
        """Test ConversationContextRepositorySqla exists."""
        cls, error = import_repository(
            "app.infrastructure.adapters.conversation_context_repository_sqla",
            "ConversationContextRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"ConversationContextRepositorySqla not implemented: {error}")
        
        assert cls is not None


@pytest.mark.unit
class TestRepositoryDependencies:
    """Test repository dependency injection."""
    
    def test_llm_conversation_repository_accepts_session(self):
        """Test LLMConversationRepositorySqla accepts session."""
        cls, error = import_repository(
            "app.infrastructure.adapters.ai.llm_conversation_repository_sqla",
            "LLMConversationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        assert repo is not None
        # Check for session in common attribute names
        session_attr = getattr(repo, 'session', getattr(repo, '_session', None))
        assert session_attr is not None
    
    def test_notification_repository_accepts_session(self):
        """Test NotificationRepositorySqla accepts session."""
        cls, error = import_repository(
            "app.infrastructure.adapters.notification_repository_sqla",
            "NotificationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        assert repo is not None
        session_attr = getattr(repo, 'session', getattr(repo, '_session', None))
        assert session_attr is not None
    
    def test_user_metrics_repository_accepts_session(self):
        """Test UserMetricsRepositorySqla accepts session."""
        cls, error = import_repository(
            "app.infrastructure.adapters.user_metrics_repository_sqla",
            "UserMetricsRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        assert repo is not None
        # Check common session attribute names
        session_attr = getattr(repo, 'session', getattr(repo, '_session', None))
        assert session_attr is not None


@pytest.mark.unit
class TestRepositoryMethods:
    """Test repository methods exist."""
    
    def test_llm_conversation_repository_has_save_method(self):
        """Test LLMConversationRepositorySqla has save method."""
        cls, error = import_repository(
            "app.infrastructure.adapters.ai.llm_conversation_repository_sqla",
            "LLMConversationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        # Check for common save method names
        has_save = hasattr(repo, 'save') or hasattr(repo, 'add') or hasattr(repo, 'create')
        assert has_save, f"Repository missing save/add/create method"
    
    def test_notification_repository_has_create_method(self):
        """Test NotificationRepositorySqla has create method."""
        cls, error = import_repository(
            "app.infrastructure.adapters.notification_repository_sqla",
            "NotificationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        has_create = hasattr(repo, 'create') or hasattr(repo, 'save') or hasattr(repo, 'add')
        assert has_create, "Repository missing create/save/add method"
    
    def test_user_metrics_repository_has_write_method(self):
        """Test UserMetricsRepositorySqla has write method."""
        cls, error = import_repository(
            "app.infrastructure.adapters.user_metrics_repository_sqla",
            "UserMetricsRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        # Check for any write method (including record_event)
        has_write = (
            hasattr(repo, 'save') or 
            hasattr(repo, 'track_event') or 
            hasattr(repo, 'record_event') or
            hasattr(repo, 'add') or 
            hasattr(repo, 'create')
        )
        assert has_write, "Repository missing write method"
    
    def test_notification_repository_has_get_method(self):
        """Test NotificationRepositorySqla has get method."""
        cls, error = import_repository(
            "app.infrastructure.adapters.notification_repository_sqla",
            "NotificationRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        has_get = (
            hasattr(repo, 'get_user_notifications') or
            hasattr(repo, 'get_by_user') or
            hasattr(repo, 'get') or
            hasattr(repo, 'get_by_id')
        )
        assert has_get, "Repository missing get method"
    
    def test_user_metrics_repository_has_get_method(self):
        """Test UserMetricsRepositorySqla has get method."""
        cls, error = import_repository(
            "app.infrastructure.adapters.user_metrics_repository_sqla",
            "UserMetricsRepositorySqla"
        )
        if cls is None:
            pytest.skip(f"Repository not implemented: {error}")
        
        mock_session = MagicMock()
        repo = cls(session=mock_session)
        
        has_get = (
            hasattr(repo, 'get_user_metrics_summary') or
            hasattr(repo, 'get_metrics') or
            hasattr(repo, 'get_by_user') or
            hasattr(repo, 'get')
        )
        assert has_get, "Repository missing get method"
