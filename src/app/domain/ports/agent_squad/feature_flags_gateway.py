"""
Feature Flags Gateway port.
"""

from typing import Protocol

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.agent_squad.agent_squad_config import AgentConfig


class FeatureFlagsGateway(Protocol):
    """
    Feature Flags Gateway port.

    Implementing adapter: FeatureFlagsConfig (loads from TOML)
    """

    async def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """
        Check if agent is enabled.

        Args:
            agent_type: Agent to check

        Returns:
            True if enabled, False otherwise
        """
        ...

    async def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """
        Get configuration for specific agent.

        Args:
            agent_type: Agent to get config for

        Returns:
            AgentConfig with model, temperature, etc.
        """
        ...

    async def get_enabled_agents(self) -> list[AgentType]:
        """
        Get list of all enabled agents.

        Returns:
            List of enabled agent types
        """
        ...
