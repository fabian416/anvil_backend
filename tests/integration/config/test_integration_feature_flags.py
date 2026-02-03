"""
Integration tests for integration feature flags.

Tests that feature flags correctly enable/disable chat and project integration features.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.setup.config.integrations import (
    IntegrationSettings,
    ChatIntegrationSettings,
    ProjectIntegrationSettings,
)
from app.application.chat.commands.send_message import SendMessage
from app.application.projects.services.project_tool_executor import (
    ProjectToolExecutor,
    ToolExecutionError,
)
from app.application.projects.templates.project_templates import (
    create_project_from_template,
    ARBITRAGE_HUNTER_TEMPLATE,
)


class TestChatIntegrationFlags:
    """Test chat integration feature flags."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock conversation repository."""
        repo = AsyncMock()

        # Mock conversation
        conversation = AsyncMock()
        conversation.id = uuid4()
        conversation.user_id = 1
        conversation.project_id = None
        conversation.is_project_scoped = False
        repo.get_conversation.return_value = conversation
        repo.add_message.return_value = None

        return repo

    @pytest.fixture
    def mock_agent_gateway(self):
        """Create mock agent gateway."""
        gateway = AsyncMock()
        gateway.process_message.return_value = "Agent response"
        return gateway

    @pytest.fixture
    def mock_hunter_executor(self):
        """Create mock Hunter AI executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "Hunter AI result"
        return executor

    @pytest.fixture
    def mock_ultra_executor(self):
        """Create mock ULTRA executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "ULTRA result"
        return executor

    @pytest.mark.asyncio
    async def test_chat_integration_disabled(
        self,
        mock_repository,
        mock_agent_gateway,
        mock_hunter_executor,
        mock_ultra_executor,
    ):
        """Test that chat integration is disabled when flag is false."""
        # Disable chat integration
        settings = IntegrationSettings(chat=ChatIntegrationSettings(enabled=False))

        send_message = SendMessage(
            repository=mock_repository,
            agent_gateway=mock_agent_gateway,
            hunter_executor=mock_hunter_executor,
            ultra_executor=mock_ultra_executor,
            integration_settings=settings,
        )

        # Send message with tool keywords
        user_msg, agent_msg = await send_message.execute(
            user_id=1,
            conversation_id=uuid4(),
            content="Analyze ETH sentiment",
        )

        # Tools should not be executed
        mock_hunter_executor.execute_tool.assert_not_called()
        mock_ultra_executor.execute_tool.assert_not_called()

        # Only agent response
        assert agent_msg.content == "Agent response"

    @pytest.mark.asyncio
    async def test_hunter_tools_disabled(
        self,
        mock_repository,
        mock_agent_gateway,
        mock_hunter_executor,
        mock_ultra_executor,
    ):
        """Test that Hunter AI tools are disabled when flag is false."""
        # Disable Hunter AI tools only
        settings = IntegrationSettings(
            chat=ChatIntegrationSettings(
                enabled=True,
                hunter_tools_enabled=False,
                ultra_tools_enabled=True,
            )
        )

        send_message = SendMessage(
            repository=mock_repository,
            agent_gateway=mock_agent_gateway,
            hunter_executor=mock_hunter_executor,
            ultra_executor=mock_ultra_executor,
            integration_settings=settings,
        )

        # Send message with Hunter AI keywords
        user_msg, agent_msg = await send_message.execute(
            user_id=1,
            conversation_id=uuid4(),
            content="Analyze ETH sentiment",
        )

        # Hunter AI should not be called
        mock_hunter_executor.execute_tool.assert_not_called()

        # Only agent response
        assert agent_msg.content == "Agent response"

    @pytest.mark.asyncio
    async def test_ultra_tools_disabled(
        self,
        mock_repository,
        mock_agent_gateway,
        mock_hunter_executor,
        mock_ultra_executor,
    ):
        """Test that ULTRA tools are disabled when flag is false."""
        # Disable ULTRA tools only
        settings = IntegrationSettings(
            chat=ChatIntegrationSettings(
                enabled=True,
                hunter_tools_enabled=True,
                ultra_tools_enabled=False,
            )
        )

        send_message = SendMessage(
            repository=mock_repository,
            agent_gateway=mock_agent_gateway,
            hunter_executor=mock_hunter_executor,
            ultra_executor=mock_ultra_executor,
            integration_settings=settings,
        )

        # Send message with ULTRA keywords
        user_msg, agent_msg = await send_message.execute(
            user_id=1,
            conversation_id=uuid4(),
            content="Find arbitrage for ETH",
        )

        # ULTRA should not be called
        mock_ultra_executor.execute_tool.assert_not_called()

        # Only agent response
        assert agent_msg.content == "Agent response"

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_disabled(
        self,
        mock_repository,
        mock_agent_gateway,
        mock_hunter_executor,
        mock_ultra_executor,
    ):
        """Test that comprehensive analysis is disabled when flag is false."""
        # Disable comprehensive analysis
        settings = IntegrationSettings(
            chat=ChatIntegrationSettings(
                enabled=True,
                hunter_tools_enabled=True,
                comprehensive_analysis_enabled=False,
            )
        )

        send_message = SendMessage(
            repository=mock_repository,
            agent_gateway=mock_agent_gateway,
            hunter_executor=mock_hunter_executor,
            ultra_executor=mock_ultra_executor,
            integration_settings=settings,
        )

        # Send message with comprehensive keywords
        user_msg, agent_msg = await send_message.execute(
            user_id=1,
            conversation_id=uuid4(),
            content="Analyze ETH completely",
        )

        # Tools should not be called (comprehensive disabled)
        # Note: Individual tools might still work with other keywords
        assert agent_msg.content == "Agent response"


class TestProjectIntegrationFlags:
    """Test project integration feature flags."""

    @pytest.fixture
    def mock_hunter_executor(self):
        """Create mock Hunter AI executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "Hunter AI result"
        return executor

    @pytest.fixture
    def mock_ultra_executor(self):
        """Create mock ULTRA executor."""
        executor = AsyncMock()
        executor.execute_tool.return_value = "ULTRA result"
        return executor

    @pytest.fixture
    def arbitrage_project(self):
        """Create Arbitrage Hunter project."""
        return create_project_from_template(
            ARBITRAGE_HUNTER_TEMPLATE, created_by=uuid4()
        )

    @pytest.mark.asyncio
    async def test_project_integration_disabled(
        self, arbitrage_project, mock_hunter_executor, mock_ultra_executor
    ):
        """Test that project integration is disabled when flag is false."""
        # Disable project integration
        settings = IntegrationSettings(
            projects=ProjectIntegrationSettings(enabled=False)
        )

        executor = ProjectToolExecutor(
            arbitrage_project,
            mock_hunter_executor,
            mock_ultra_executor,
            integration_settings=settings,
        )

        # Try to execute tool
        with pytest.raises(ToolExecutionError) as exc_info:
            await executor.execute_tool(
                tool_name="hunter_risk_analysis", parameters={"token_symbol": "ETH"}
            )

        assert "Project integration is disabled" in str(exc_info.value)
        assert "integrations.projects.enabled=true" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_permissions_disabled(
        self, arbitrage_project, mock_hunter_executor, mock_ultra_executor
    ):
        """Test that tool permissions are bypassed when flag is false."""
        # Disable tool permissions (but keep project integration on)
        settings = IntegrationSettings(
            projects=ProjectIntegrationSettings(
                enabled=True,
                tool_permissions_enabled=False,
            )
        )

        executor = ProjectToolExecutor(
            arbitrage_project,
            mock_hunter_executor,
            mock_ultra_executor,
            integration_settings=settings,
        )

        # Try to execute tool NOT enabled in project
        # (Arbitrage Hunter doesn't have sentiment, but permissions disabled)
        result = await executor.execute_tool(
            tool_name="hunter_sentiment_analysis", parameters={"token_symbol": "ETH"}
        )

        # Should succeed (permissions bypassed)
        assert result == "Hunter AI result"
        mock_hunter_executor.execute_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_risk_validation_disabled(
        self, arbitrage_project, mock_hunter_executor, mock_ultra_executor
    ):
        """Test that risk validation is bypassed when flag is false."""
        # Disable risk validation (but keep project integration on)
        settings = IntegrationSettings(
            projects=ProjectIntegrationSettings(
                enabled=True,
                risk_validation_enabled=False,
            )
        )

        executor = ProjectToolExecutor(
            arbitrage_project,
            mock_hunter_executor,
            mock_ultra_executor,
            integration_settings=settings,
        )

        # Try to execute ULTRA tool with HIGH capital (should exceed limit)
        # But validation is disabled, so it should pass
        result = await executor.execute_tool(
            tool_name="ultra_arbitrage_discovery",
            parameters={
                "token_symbol": "ETH",
                "capital": 10000000,
            },  # $10M (way over limit)
        )

        # Should succeed (validation bypassed)
        assert result == "ULTRA result"
        mock_ultra_executor.execute_tool.assert_called_once()


class TestIntegrationSettingsDefaults:
    """Test integration settings default values."""

    def test_default_settings(self):
        """Test that all flags default to true."""
        settings = IntegrationSettings()

        # Chat defaults
        assert settings.chat.enabled is True
        assert settings.chat.hunter_tools_enabled is True
        assert settings.chat.ultra_tools_enabled is True
        assert settings.chat.comprehensive_analysis_enabled is True
        assert settings.chat.max_parallel_tools == 10

        # Project defaults
        assert settings.projects.enabled is True
        assert settings.projects.templates_enabled is True
        assert settings.projects.risk_validation_enabled is True
        assert settings.projects.tool_permissions_enabled is True

    def test_partial_settings(self):
        """Test that partial settings work with defaults."""
        settings = IntegrationSettings(
            chat=ChatIntegrationSettings(hunter_tools_enabled=False)
        )

        # Explicitly set
        assert settings.chat.hunter_tools_enabled is False

        # Should use defaults for others
        assert settings.chat.enabled is True
        assert settings.chat.ultra_tools_enabled is True
        assert settings.projects.enabled is True
