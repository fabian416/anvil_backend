"""
Feature Flags Config adapter - Loads configuration from TOML.
"""

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.agent_squad.agent_squad_config import (
    AgentSquadConfig,
    AgentConfig,
)
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway


class FeatureFlagsConfig:
    """
    Feature Flags Config adapter.

    Implements: FeatureFlagsGateway

    Loads agent configuration from AgentSquadConfig (TOML-based).
    Provides agent enable/disable checks and configuration access.
    """

    def __init__(self, config: AgentSquadConfig):
        """
        Initialize feature flags adapter.

        Args:
            config: AgentSquadConfig loaded from TOML
        """
        self._config = config

    async def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if agent is enabled."""
        return self._config.is_agent_enabled(agent_type)

    async def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for specific agent."""
        return self._config.get_agent_config(agent_type)

    async def get_enabled_agents(self) -> list[AgentType]:
        """Get list of all enabled agents."""
        return self._config.enabled_agents

    @property
    def config(self) -> AgentSquadConfig:
        """Get full configuration."""
        return self._config
