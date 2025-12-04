"""
Agno Agent configuration settings.

Provides granular enable/disable controls for each Agno agent
and routing behavior configuration.
"""

from pydantic import BaseModel, Field


class AgnoAgentSettings(BaseModel):
    """Settings for individual Agno agents."""
    
    trading_enabled: bool = Field(
        default=True,
        description="Enable Trading agent for trade execution & strategy",
    )
    lending_enabled: bool = Field(
        default=True,
        description="Enable Lending agent for lending/borrowing recommendations",
    )
    portfolio_enabled: bool = Field(
        default=True,
        description="Enable Portfolio agent for portfolio optimization",
    )
    analytics_enabled: bool = Field(
        default=True,
        description="Enable Analytics agent for data analysis & insights",
    )


class AgnoSettings(BaseModel):
    """Agno agent system configuration settings."""
    
    enabled: bool = Field(
        default=True,
        description="Master switch for all Agno agents",
    )
    intent_classification_enabled: bool = Field(
        default=True,
        description="Enable automatic intent classification and agent routing",
    )
    fallback_to_general: bool = Field(
        default=True,
        description="Fallback to general agent if specific agent is disabled",
    )
    agents: AgnoAgentSettings = Field(
        default_factory=AgnoAgentSettings,
        description="Individual agent enable/disable flags",
    )


class AgnoConfig(BaseModel):
    """Agno configuration (existing model extended with settings)."""
    
    default_model: str = "gpt-4-turbo"
    fallback_model: str = "gpt-3.5-turbo"
    intent_threshold: float = 0.75
    session_timeout: int = 3600
    max_context_messages: int = 20
    enable_intent_classification: bool = True
    enable_context_memory: bool = True
    enable_multi_agent_routing: bool = True
    debug_mode: bool = False
    log_intent_classification: bool = True
    log_agent_selection: bool = True


class AgentDisabledError(Exception):
    """Raised when attempting to use a disabled agent."""
    pass
