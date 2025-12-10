"""
Test-specific DI providers for isolated testing.

This module provides mock implementations of all infrastructure
dependencies for unit and integration testing.
"""

from collections.abc import Iterable
from typing import Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dishka import Provider, provide, Scope

# Domain Ports
from app.domain.ports.user_query_gateway import UserQueryGateway
from app.domain.ports.user_command_gateway import UserCommandGateway
from app.domain.ports.conversation_query_gateway import ConversationQueryGateway
from app.domain.ports.conversation_command_gateway import ConversationCommandGateway
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.ports.user_id_generator import UserIdGenerator

# Infrastructure interfaces
from app.infrastructure.cache.external_api_cache import ExternalAPICache

# Application services
from app.application.common.ports.unit_of_work import UnitOfWork
from app.application.common.ports.task_queue import TaskQueue


class TestDomainProvider(Provider):
    """Test provider for domain layer dependencies."""
    
    @provide(scope=Scope.REQUEST)
    def mock_password_hasher(self) -> PasswordHasher:
        """Mock password hasher."""
        hasher = MagicMock(spec=PasswordHasher)
        hasher.hash.return_value = b"hashed_password_for_testing"
        hasher.verify.return_value = True
        return hasher
    
    @provide(scope=Scope.REQUEST)
    def mock_user_id_generator(self) -> UserIdGenerator:
        """Mock user ID generator."""
        counter = [0]
        def generate():
            counter[0] += 1
            return counter[0]
        return generate


class TestInfrastructureProvider(Provider):
    """Test provider for infrastructure dependencies."""
    
    @provide(scope=Scope.REQUEST)
    def mock_user_query_gateway(self) -> UserQueryGateway:
        """Mock user query gateway."""
        gateway = AsyncMock(spec=UserQueryGateway)
        gateway.get_by_id.return_value = None
        gateway.get_by_email.return_value = None
        gateway.list_users.return_value = []
        gateway.count_users.return_value = 0
        return gateway
    
    @provide(scope=Scope.REQUEST)
    def mock_user_command_gateway(self) -> UserCommandGateway:
        """Mock user command gateway."""
        gateway = AsyncMock(spec=UserCommandGateway)
        gateway.save.return_value = None
        gateway.delete.return_value = None
        gateway.update.return_value = None
        return gateway
    
    @provide(scope=Scope.REQUEST)
    def mock_conversation_query_gateway(self) -> ConversationQueryGateway:
        """Mock conversation query gateway."""
        gateway = AsyncMock(spec=ConversationQueryGateway)
        gateway.get_by_id.return_value = None
        gateway.list_by_user.return_value = []
        gateway.get_messages.return_value = []
        return gateway
    
    @provide(scope=Scope.REQUEST)
    def mock_conversation_command_gateway(self) -> ConversationCommandGateway:
        """Mock conversation command gateway."""
        gateway = AsyncMock(spec=ConversationCommandGateway)
        gateway.save.return_value = None
        gateway.delete.return_value = None
        gateway.add_message.return_value = None
        return gateway
    
    @provide(scope=Scope.REQUEST)
    def mock_external_cache(self) -> ExternalAPICache:
        """Mock external API cache."""
        cache = AsyncMock(spec=ExternalAPICache)
        cache.get.return_value = None
        cache.set.return_value = None
        cache.delete.return_value = None
        cache.exists.return_value = False
        return cache
    
    @provide(scope=Scope.REQUEST)
    def mock_unit_of_work(self) -> UnitOfWork:
        """Mock unit of work."""
        uow = AsyncMock(spec=UnitOfWork)
        uow.commit.return_value = None
        uow.rollback.return_value = None
        return uow
    
    @provide(scope=Scope.REQUEST)
    def mock_task_queue(self) -> TaskQueue:
        """Mock task queue."""
        queue = AsyncMock(spec=TaskQueue)
        queue.enqueue.return_value = str(uuid4())
        queue.enqueue_message_processing.return_value = str(uuid4())
        return queue


class TestDeFiProvider(Provider):
    """Test provider for DeFi protocol dependencies."""
    
    @provide(scope=Scope.REQUEST)
    def mock_aave_gateway(self):
        """Mock Aave gateway."""
        from app.domain.ports.aave_gateway import AaveGateway
        gateway = AsyncMock(spec=AaveGateway)
        gateway.get_markets.return_value = []
        gateway.get_position.return_value = None
        gateway.get_stats.return_value = {"tvl": 0}
        return gateway
    
    @provide(scope=Scope.REQUEST)
    def mock_curve_gateway(self):
        """Mock Curve gateway."""
        from app.domain.ports.curve_gateway import CurveGateway
        gateway = AsyncMock(spec=CurveGateway)
        gateway.get_pools.return_value = []
        gateway.get_pool_apy.return_value = None
        gateway.get_tvl.return_value = {"total": 0}
        return gateway


class TestAgentProvider(Provider):
    """Test provider for agent dependencies."""
    
    @provide(scope=Scope.REQUEST)
    def mock_llm_client(self):
        """Mock LLM client."""
        from app.domain.ports.llm_gateway import LLMGateway
        client = AsyncMock(spec=LLMGateway)
        client.generate.return_value = {
            "content": "Mock LLM response for testing",
            "model": "gpt-4o-mini",
            "tokens_used": 100,
            "finish_reason": "stop",
        }
        client.chat.return_value = {
            "content": "Mock chat response",
            "model": "gpt-4o-mini",
        }
        return client
    
    @provide(scope=Scope.REQUEST)
    def mock_agent_gateway(self):
        """Mock agent gateway."""
        from app.domain.ports.agent_squad.agent_gateway import AgentGateway
        gateway = AsyncMock(spec=AgentGateway)
        gateway.process_message.return_value = {
            "response": "Mock agent response",
            "confidence": 0.95,
            "agent_type": "chat",
        }
        return gateway


def get_test_providers() -> Iterable[Provider]:
    """Get all test providers for isolated testing."""
    return (
        TestDomainProvider(),
        TestInfrastructureProvider(),
        TestDeFiProvider(),
        TestAgentProvider(),
    )


def create_test_container():
    """Create a test DI container with all mocks."""
    from dishka import make_async_container
    from app.setup.ioc.settings import SettingsProvider
    
    return make_async_container(
        SettingsProvider(),
        *get_test_providers(),
    )
