"""
Integration tests for Agno agent feature flags.

Tests granular enable/disable controls for each Agno agent and fallback logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.setup.config.agno import (
    AgnoSettings,
    AgnoAgentSettings,
    AgnoConfig,
    AgentDisabledError,
)
from app.infrastructure.agno.agent_router import AgentRouter, AgentType


class TestAgnoMasterSwitch:
    """Test Agno master enable/disable switch."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_agno_disabled_globally(self, mock_mcp_manager_http):
        """Test that Agno system can be disabled globally."""
        settings = AgnoSettings(enabled=False)
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # No agents should be initialized
        assert len(router.agents) == 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_agno_enabled_by_default(self, mock_mcp_manager_http):
        """Test that Agno is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # All 5 agents should be initialized
        assert len(router.agents) == 5
        assert AgentType.TRADING in router.agents
        assert AgentType.LENDING in router.agents
        assert AgentType.PERPETUAL in router.agents
        assert AgentType.ANALYTICS in router.agents
        assert AgentType.PORTFOLIO in router.agents


class TestTradingAgentFlags:
    """Test Trading agent feature flags."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trading_agent_enabled_by_default(self, mock_mcp_manager_http):
        """Test Trading agent is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.TRADING in router.agents

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trading_agent_can_be_disabled(self, mock_mcp_manager_http):
        """Test Trading agent can be disabled."""
        settings = AgnoSettings(agents=AgnoAgentSettings(trading_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.TRADING not in router.agents
        assert len(router.agents) == 4  # Other 4 agents still enabled


class TestLendingAgentFlags:
    """Test Lending agent feature flags."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_agent_enabled_by_default(self, mock_mcp_manager_http):
        """Test Lending agent is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.LENDING in router.agents

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_agent_can_be_disabled(self, mock_mcp_manager_http):
        """Test Lending agent can be disabled."""
        settings = AgnoSettings(agents=AgnoAgentSettings(lending_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.LENDING not in router.agents
        assert len(router.agents) == 4


class TestAnalyticsAgentFlags:
    """Test Analytics agent feature flags."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analytics_agent_enabled_by_default(self, mock_mcp_manager_http):
        """Test Analytics agent is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.ANALYTICS in router.agents

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analytics_agent_can_be_disabled(self, mock_mcp_manager_http):
        """Test Analytics agent can be disabled."""
        settings = AgnoSettings(agents=AgnoAgentSettings(analytics_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.ANALYTICS not in router.agents
        assert len(router.agents) == 4


class TestPortfolioAgentFlags:
    """Test Portfolio agent feature flags."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_agent_enabled_by_default(self, mock_mcp_manager_http):
        """Test Portfolio agent is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.PORTFOLIO in router.agents

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_agent_can_be_disabled(self, mock_mcp_manager_http):
        """Test Portfolio agent can be disabled."""
        settings = AgnoSettings(agents=AgnoAgentSettings(portfolio_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.PORTFOLIO not in router.agents
        assert len(router.agents) == 4


class TestPerpetualAgentFlags:
    """Test Perpetual agent feature flags."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_perpetual_agent_enabled_by_default(self, mock_mcp_manager_http):
        """Test Perpetual agent is enabled by default."""
        settings = AgnoSettings()
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.PERPETUAL in router.agents

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_perpetual_agent_can_be_disabled(self, mock_mcp_manager_http):
        """Test Perpetual agent can be disabled."""
        settings = AgnoSettings(agents=AgnoAgentSettings(perpetual_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.PERPETUAL not in router.agents
        assert len(router.agents) == 4


class TestFallbackBehavior:
    """Test fallback behavior when agents are disabled."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_fallback_to_analytics_enabled(self, mock_mcp_manager_http):
        """Test fallback to analytics when requested agent is disabled."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(
                trading_enabled=False,  # Disable trading
                analytics_enabled=True,  # Keep analytics
            ),
            fallback_to_general=True,
        )
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # Mock classify_intent to return trading
        router.classify_intent = Mock(return_value=(AgentType.TRADING, 0.8))

        # Mock the analytics agent's run method
        analytics_agent = router.agents[AgentType.ANALYTICS]
        analytics_agent.run = AsyncMock(return_value={"content": "Fallback response"})

        # Should fallback to analytics without error
        result = await router.route("Swap ETH for USDC")
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_fallback_disabled_raises_error(self, mock_mcp_manager_http):
        """Test error when fallback is disabled and agent is not available."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(trading_enabled=False),
            fallback_to_general=False,  # Disable fallback
        )
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # Mock classify_intent to return trading
        router.classify_intent = Mock(return_value=(AgentType.TRADING, 0.8))

        # Should raise error
        with pytest.raises(AgentDisabledError) as exc_info:
            await router.route("Swap ETH for USDC")

        assert "trading agent is disabled" in str(exc_info.value)
        assert "trading_enabled=true" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_no_agents_enabled_raises_error(self, mock_mcp_manager_http):
        """Test error when all agents are disabled."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(
                trading_enabled=False,
                lending_enabled=False,
                perpetual_enabled=False,
                analytics_enabled=False,
                portfolio_enabled=False,
            ),
            fallback_to_general=True,
        )
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # Mock classify_intent
        router.classify_intent = Mock(return_value=(AgentType.TRADING, 0.8))

        # Should raise error even with fallback enabled
        with pytest.raises(AgentDisabledError) as exc_info:
            await router.route("Any query")

        assert "All agents are disabled" in str(exc_info.value)


class TestSelectiveAgentEnablement:
    """Test selective enablement scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_read_only_mode(self, mock_mcp_manager_http):
        """Test enabling only read-only agents (analytics, portfolio)."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(
                trading_enabled=False,  # Disable execution
                lending_enabled=False,  # Disable execution
                perpetual_enabled=False,  # Disable execution
                analytics_enabled=True,  # Read-only
                portfolio_enabled=True,  # Read-only
            )
        )
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert AgentType.TRADING not in router.agents
        assert AgentType.LENDING not in router.agents
        assert AgentType.PERPETUAL not in router.agents
        assert AgentType.ANALYTICS in router.agents
        assert AgentType.PORTFOLIO in router.agents
        assert len(router.agents) == 2

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analytics_only_mode(self, mock_mcp_manager_http):
        """Test enabling only analytics agent (market data)."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(
                trading_enabled=False,
                lending_enabled=False,
                perpetual_enabled=False,
                analytics_enabled=True,  # Only market data
                portfolio_enabled=False,
            )
        )
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        assert len(router.agents) == 1
        assert AgentType.ANALYTICS in router.agents


class TestConfigurationDefaults:
    """Test configuration default values."""

    def test_all_defaults_enabled(self):
        """Test that all agents are enabled by default."""
        settings = AgnoSettings()

        assert settings.enabled is True
        assert settings.intent_classification_enabled is True
        assert settings.fallback_to_general is True
        assert settings.agents.trading_enabled is True
        assert settings.agents.lending_enabled is True
        assert settings.agents.perpetual_enabled is True
        assert settings.agents.analytics_enabled is True
        assert settings.agents.portfolio_enabled is True

    def test_partial_configuration(self):
        """Test partial configuration with defaults."""
        settings = AgnoSettings(
            agents=AgnoAgentSettings(
                trading_enabled=False,
                # Others default to True
            )
        )

        assert settings.agents.trading_enabled is False
        assert settings.agents.lending_enabled is True  # Default
        assert settings.agents.analytics_enabled is True  # Default
        assert settings.agents.portfolio_enabled is True  # Default


class TestIntentClassification:
    """Test intent classification with disabled agents."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_intent_classification_still_works(self, mock_mcp_manager_http):
        """Test that intent classification works even with disabled agents."""
        settings = AgnoSettings(agents=AgnoAgentSettings(trading_enabled=False))
        config = AgnoConfig()

        router = AgentRouter(config, settings=settings)
        await router.initialize()

        # Classify trading intent (even though agent is disabled)
        agent_type, confidence = router.classify_intent("Swap ETH for USDC")

        # Should still classify as trading
        assert agent_type == AgentType.TRADING
        assert confidence > 0
