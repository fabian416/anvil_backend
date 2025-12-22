"""
Agent Library Registry.

Centralized registry for all pre-configured custom agents.
Provides discovery, filtering, and instantiation capabilities.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Callable, Optional
from uuid import UUID

from app.domain.value_objects.chat.orchestration import CustomAgentConfig

# Import all agent factory functions
from app.application.agents.library.curve_finance_expert import (
    create_curve_finance_expert,
    AGENT_METADATA as CURVE_METADATA,
)
from app.application.agents.library.aave_specialist import (
    create_aave_specialist,
    AGENT_METADATA as AAVE_METADATA,
)
from app.application.agents.library.uniswap_expert import (
    create_uniswap_expert,
    AGENT_METADATA as UNISWAP_METADATA,
)
from app.application.agents.library.yearn_strategist import (
    create_yearn_strategist,
    AGENT_METADATA as YEARN_METADATA,
)
from app.application.agents.library.compound_advisor import (
    create_compound_advisor,
    AGENT_METADATA as COMPOUND_METADATA,
)
from app.application.agents.library.smart_contract_auditor import (
    create_smart_contract_auditor,
    AGENT_METADATA as AUDITOR_METADATA,
)
from app.application.agents.library.gas_optimization_expert import (
    create_gas_optimization_expert,
    AGENT_METADATA as GAS_METADATA,
)
from app.application.agents.library.mev_protection_advisor import (
    create_mev_protection_advisor,
    AGENT_METADATA as MEV_METADATA,
)
from app.application.agents.library.bridge_specialist import (
    create_bridge_specialist,
    AGENT_METADATA as BRIDGE_METADATA,
)
from app.application.agents.library.wallet_security_expert import (
    create_wallet_security_expert,
    AGENT_METADATA as WALLET_METADATA,
)


class AgentCategory(Enum):
    """Agent categories for organization and discovery."""

    DEFI_SPECIALIST = "defi_specialist"
    TECHNICAL_EXPERT = "technical_expert"
    ALL = "all"


@dataclass
class AgentLibraryEntry:
    """
    Entry in the agent library registry.

    Combines agent factory function with metadata for discovery.
    """

    agent_id: str  # Unique identifier (e.g., "curve_finance_expert")
    factory_fn: Callable[[], CustomAgentConfig]
    metadata: Dict
    category: AgentCategory

    def create(self) -> CustomAgentConfig:
        """Create instance of the agent."""
        return self.factory_fn()

    @property
    def name(self) -> str:
        """Get agent display name."""
        return self.factory_fn().__dict__.get("name", self.agent_id)

    @property
    def description(self) -> str:
        """Get agent description."""
        return self.factory_fn().__dict__.get("description", "")

    @property
    def tags(self) -> List[str]:
        """Get agent tags for filtering."""
        return self.metadata.get("tags", [])

    @property
    def protocol(self) -> Optional[str]:
        """Get associated protocol (for DeFi specialists)."""
        return self.metadata.get("protocol")


class AgentLibraryRegistry:
    """
    Central registry for all pre-configured agents.

    Provides:
    - Agent discovery by category, tags, protocol
    - Agent instantiation
    - Metadata queries
    - Library statistics
    """

    def __init__(self):
        """Initialize registry with all available agents."""
        self._agents: Dict[str, AgentLibraryEntry] = {}
        self._register_all_agents()

    def _register_all_agents(self) -> None:
        """Register all available agents in the library."""
        # DeFi Specialists
        self._register(
            "curve_finance_expert",
            create_curve_finance_expert,
            CURVE_METADATA,
            AgentCategory.DEFI_SPECIALIST,
        )
        self._register(
            "aave_specialist",
            create_aave_specialist,
            AAVE_METADATA,
            AgentCategory.DEFI_SPECIALIST,
        )
        self._register(
            "uniswap_expert",
            create_uniswap_expert,
            UNISWAP_METADATA,
            AgentCategory.DEFI_SPECIALIST,
        )
        self._register(
            "yearn_strategist",
            create_yearn_strategist,
            YEARN_METADATA,
            AgentCategory.DEFI_SPECIALIST,
        )
        self._register(
            "compound_advisor",
            create_compound_advisor,
            COMPOUND_METADATA,
            AgentCategory.DEFI_SPECIALIST,
        )

        # Technical Experts
        self._register(
            "smart_contract_auditor",
            create_smart_contract_auditor,
            AUDITOR_METADATA,
            AgentCategory.TECHNICAL_EXPERT,
        )
        self._register(
            "gas_optimization_expert",
            create_gas_optimization_expert,
            GAS_METADATA,
            AgentCategory.TECHNICAL_EXPERT,
        )
        self._register(
            "mev_protection_advisor",
            create_mev_protection_advisor,
            MEV_METADATA,
            AgentCategory.TECHNICAL_EXPERT,
        )
        self._register(
            "bridge_specialist",
            create_bridge_specialist,
            BRIDGE_METADATA,
            AgentCategory.TECHNICAL_EXPERT,
        )
        self._register(
            "wallet_security_expert",
            create_wallet_security_expert,
            WALLET_METADATA,
            AgentCategory.TECHNICAL_EXPERT,
        )

    def _register(
        self,
        agent_id: str,
        factory_fn: Callable[[], CustomAgentConfig],
        metadata: Dict,
        category: AgentCategory,
    ) -> None:
        """Register an agent in the library."""
        entry = AgentLibraryEntry(
            agent_id=agent_id,
            factory_fn=factory_fn,
            metadata=metadata,
            category=category,
        )
        self._agents[agent_id] = entry

    def get_agent(self, agent_id: str) -> Optional[CustomAgentConfig]:
        """
        Get agent by ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Agent configuration or None if not found
        """
        entry = self._agents.get(agent_id)
        return entry.create() if entry else None

    def get_all_agents(self) -> List[CustomAgentConfig]:
        """Get all available agents."""
        return [entry.create() for entry in self._agents.values()]

    def get_agents_by_category(self, category: AgentCategory) -> List[CustomAgentConfig]:
        """
        Get all agents in a category.

        Args:
            category: Agent category to filter by

        Returns:
            List of agents in the category
        """
        if category == AgentCategory.ALL:
            return self.get_all_agents()

        return [
            entry.create()
            for entry in self._agents.values()
            if entry.category == category
        ]

    def get_agents_by_tag(self, tag: str) -> List[CustomAgentConfig]:
        """
        Get agents matching a tag.

        Args:
            tag: Tag to search for (e.g., "lending", "security")

        Returns:
            List of agents with matching tag
        """
        return [
            entry.create()
            for entry in self._agents.values()
            if tag.lower() in [t.lower() for t in entry.tags]
        ]

    def get_agents_by_protocol(self, protocol: str) -> List[CustomAgentConfig]:
        """
        Get agents specialized in a specific protocol.

        Args:
            protocol: Protocol name (e.g., "aave", "uniswap")

        Returns:
            List of agents for that protocol
        """
        return [
            entry.create()
            for entry in self._agents.values()
            if entry.protocol and entry.protocol.lower() == protocol.lower()
        ]

    def search_agents(
        self,
        query: str,
        category: Optional[AgentCategory] = None,
    ) -> List[CustomAgentConfig]:
        """
        Search agents by text query.

        Searches in:
        - Agent name
        - Description
        - Tags
        - Expertise areas

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List of matching agents
        """
        query_lower = query.lower()
        results = []

        for entry in self._agents.values():
            # Apply category filter
            if category and category != AgentCategory.ALL and entry.category != category:
                continue

            # Create agent to access full config
            agent = entry.create()

            # Search in multiple fields
            searchable_text = " ".join([
                agent.name.lower(),
                agent.description.lower(),
                " ".join(entry.tags).lower(),
                " ".join(agent.expertise_areas).lower(),
            ])

            if query_lower in searchable_text:
                results.append(agent)

        return results

    def get_library_stats(self) -> Dict:
        """
        Get statistics about the agent library.

        Returns:
            Dictionary with library statistics
        """
        defi_count = len([e for e in self._agents.values() if e.category == AgentCategory.DEFI_SPECIALIST])
        tech_count = len([e for e in self._agents.values() if e.category == AgentCategory.TECHNICAL_EXPERT])

        all_tags = set()
        for entry in self._agents.values():
            all_tags.update(entry.tags)

        return {
            "total_agents": len(self._agents),
            "defi_specialists": defi_count,
            "technical_experts": tech_count,
            "unique_tags": len(all_tags),
            "tags": sorted(list(all_tags)),
            "agent_ids": sorted(list(self._agents.keys())),
        }

    def list_agent_summaries(self) -> List[Dict]:
        """
        Get summary information for all agents.

        Useful for UI display, agent selection interfaces.

        Returns:
            List of agent summary dictionaries
        """
        summaries = []

        for agent_id, entry in self._agents.items():
            agent = entry.create()
            summaries.append({
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
                "category": entry.category.value,
                "tags": entry.tags,
                "protocol": entry.protocol,
                "expertise_areas": agent.expertise_areas,
                "response_style": agent.response_style,
                "temperature": agent.temperature,
            })

        return summaries


# Global singleton instance
_registry_instance: Optional[AgentLibraryRegistry] = None


def get_agent_registry() -> AgentLibraryRegistry:
    """
    Get the global agent registry instance.

    Returns:
        Singleton AgentLibraryRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentLibraryRegistry()
    return _registry_instance


# Convenience functions
def get_agent(agent_id: str) -> Optional[CustomAgentConfig]:
    """Get agent by ID."""
    return get_agent_registry().get_agent(agent_id)


def get_all_agents() -> List[CustomAgentConfig]:
    """Get all available agents."""
    return get_agent_registry().get_all_agents()


def get_defi_specialists() -> List[CustomAgentConfig]:
    """Get all DeFi specialist agents."""
    return get_agent_registry().get_agents_by_category(AgentCategory.DEFI_SPECIALIST)


def get_technical_experts() -> List[CustomAgentConfig]:
    """Get all technical expert agents."""
    return get_agent_registry().get_agents_by_category(AgentCategory.TECHNICAL_EXPERT)


def search_agents(query: str) -> List[CustomAgentConfig]:
    """Search agents by text query."""
    return get_agent_registry().search_agents(query)
