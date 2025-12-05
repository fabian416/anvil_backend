"""
Agent Squad Configuration value objects.
"""

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums.agent_type import AgentType


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration for a single agent.
    
    Controls:
    - enabled: Whether agent is available
    - model: LLM model to use (e.g., "gpt-4o", "gpt-4o-mini")
    - temperature: Model temperature (0.0-1.0)
    - max_tokens: Maximum response tokens
    - timeout_seconds: Agent execution timeout
    - custom_params: Agent-specific parameters
    """
    enabled: bool
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 60
    custom_params: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be 0.0-2.0, got {self.temperature}")
        
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        
        if self.timeout_seconds < 1:
            raise ValueError(f"timeout_seconds must be positive, got {self.timeout_seconds}")
    
    @property
    def is_enabled(self) -> bool:
        """Check if agent is enabled."""
        return self.enabled
    
    @classmethod
    def default(cls, enabled: bool = True) -> "AgentConfig":
        """Create default agent configuration."""
        return cls(
            enabled=enabled,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            timeout_seconds=60,
            custom_params={},
        )
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        """Create from dictionary (TOML config)."""
        return cls(
            enabled=data.get("enabled", True),
            model=data.get("model", "gpt-4o-mini"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1000),
            timeout_seconds=data.get("timeout_seconds", 60),
            custom_params=data.get("custom_params", {}),
        )


@dataclass(frozen=True)
class AgentSquadConfig:
    """
    Configuration for Agent Squad multi-agent system.
    
    Controls:
    - Master toggle (enable/disable entire system)
    - Intent classification settings
    - Supervisor settings
    - Per-agent configuration (18 agents)
    - Performance limits
    - Storage settings
    """
    # Master toggle
    enabled: bool
    
    # Intent classification
    intent_classification_model: str
    intent_confidence_threshold: float
    fallback_agent: AgentType
    
    # Supervisor
    enable_supervisor: bool
    supervisor_model: str
    supervisor_max_agents: int
    supervisor_timeout_seconds: int
    
    # Context preservation
    conversation_history_limit: int
    context_window_tokens: int
    
    # Performance
    max_concurrent_agents: int
    routing_timeout_seconds: int
    execution_timeout_seconds: int
    
    # Storage
    storage_backend: str  # "postgresql" or "redis"
    storage_ttl_seconds: int
    
    # Telemetry
    telemetry_enabled: bool
    telemetry_sample_rate: float
    
    # Per-agent configuration (18 agents)
    agents: dict[AgentType, AgentConfig]
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.intent_confidence_threshold <= 1.0:
            raise ValueError(
                f"intent_confidence_threshold must be 0.0-1.0, got {self.intent_confidence_threshold}"
            )
        
        if not 0.0 <= self.telemetry_sample_rate <= 1.0:
            raise ValueError(
                f"telemetry_sample_rate must be 0.0-1.0, got {self.telemetry_sample_rate}"
            )
        
        if self.supervisor_max_agents < 1 or self.supervisor_max_agents > 10:
            raise ValueError(
                f"supervisor_max_agents must be 1-10, got {self.supervisor_max_agents}"
            )
    
    def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for specific agent."""
        return self.agents.get(agent_type, AgentConfig.default(enabled=True))
    
    def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if specific agent is enabled."""
        if not self.enabled:
            return False
        
        agent_config = self.get_agent_config(agent_type)
        return agent_config.is_enabled
    
    @property
    def enabled_agents(self) -> list[AgentType]:
        """Get list of enabled agents."""
        if not self.enabled:
            return []
        
        return [
            agent_type
            for agent_type, config in self.agents.items()
            if config.is_enabled
        ]
    
    @property
    def enabled_core_agents(self) -> list[AgentType]:
        """Get list of enabled core user-facing agents."""
        core_agents = AgentType.get_core_agents()
        return [
            agent_type
            for agent_type in core_agents
            if self.is_agent_enabled(agent_type)
        ]
    
    @property
    def enabled_enterprise_agents(self) -> list[AgentType]:
        """Get list of enabled enterprise agents."""
        enterprise_agents = AgentType.get_enterprise_agents()
        return [
            agent_type
            for agent_type in enterprise_agents
            if self.is_agent_enabled(agent_type)
        ]
    
    @classmethod
    def default(cls) -> "AgentSquadConfig":
        """
        Create default configuration.
        
        All core agents enabled, enterprise agents disabled.
        """
        # Create default config for all agents
        agents = {}
        
        # Core agents: enabled by default
        for agent_type in AgentType.get_core_agents():
            agents[agent_type] = AgentConfig.default(enabled=True)
        
        # Enterprise agents: disabled by default
        for agent_type in AgentType.get_enterprise_agents():
            agents[agent_type] = AgentConfig.default(enabled=False)
        
        return cls(
            enabled=True,
            intent_classification_model="gpt-4o-mini",
            intent_confidence_threshold=0.85,
            fallback_agent=AgentType.CHAT,
            enable_supervisor=True,
            supervisor_model="gpt-4o",
            supervisor_max_agents=5,
            supervisor_timeout_seconds=120,
            conversation_history_limit=20,
            context_window_tokens=8000,
            max_concurrent_agents=3,
            routing_timeout_seconds=5,
            execution_timeout_seconds=60,
            storage_backend="postgresql",
            storage_ttl_seconds=86400,  # 24 hours
            telemetry_enabled=True,
            telemetry_sample_rate=1.0,
            agents=agents,
        )
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentSquadConfig":
        """
        Create from dictionary (loaded from TOML).
        
        Args:
            data: Configuration dictionary from TOML file
            
        Returns:
            AgentSquadConfig instance
        """
        # Parse fallback agent
        fallback_agent_str = data.get("fallback_agent", "chat")
        try:
            fallback_agent = AgentType[fallback_agent_str.upper()]
        except KeyError:
            fallback_agent = AgentType.CHAT
        
        # Parse per-agent configuration
        agents = {}
        agents_config = data.get("agents", {})
        
        # All agents (default: core enabled, enterprise disabled)
        for agent_type in AgentType.get_all_agents():
            agent_key = agent_type.value
            
            if agent_key in agents_config:
                # Use configured values
                agents[agent_type] = AgentConfig.from_dict(agents_config[agent_key])
            else:
                # Use defaults (core enabled, enterprise disabled)
                is_enterprise = AgentType.is_enterprise_agent(agent_type)
                agents[agent_type] = AgentConfig.default(enabled=not is_enterprise)
        
        return cls(
            enabled=data.get("enabled", True),
            intent_classification_model=data.get("intent_classification_model", "gpt-4o-mini"),
            intent_confidence_threshold=data.get("intent_confidence_threshold", 0.85),
            fallback_agent=fallback_agent,
            enable_supervisor=data.get("enable_supervisor", True),
            supervisor_model=data.get("supervisor_model", "gpt-4o"),
            supervisor_max_agents=data.get("supervisor_max_agents", 5),
            supervisor_timeout_seconds=data.get("supervisor_timeout_seconds", 120),
            conversation_history_limit=data.get("conversation_history_limit", 20),
            context_window_tokens=data.get("context_window_tokens", 8000),
            max_concurrent_agents=data.get("max_concurrent_agents", 3),
            routing_timeout_seconds=data.get("routing_timeout_seconds", 5),
            execution_timeout_seconds=data.get("execution_timeout_seconds", 60),
            storage_backend=data.get("storage_backend", "postgresql"),
            storage_ttl_seconds=data.get("storage_ttl_seconds", 86400),
            telemetry_enabled=data.get("telemetry_enabled", True),
            telemetry_sample_rate=data.get("telemetry_sample_rate", 1.0),
            agents=agents,
        )
