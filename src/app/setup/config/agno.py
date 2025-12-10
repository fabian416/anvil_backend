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


class AgnoRetryConfig(BaseModel):
    """Retry configuration for Agno agent MCP tool calls."""
    
    enabled: bool = Field(
        default=True,
        description="Enable retry for MCP tool calls",
    )
    
    max_attempts: int = Field(
        default=2,
        description="Maximum retry attempts (agents prioritize fast feedback)",
        ge=1,
        le=5,
    )
    
    initial_backoff_seconds: float = Field(
        default=1.0,
        description="Initial backoff delay in seconds",
        gt=0,
    )
    
    max_backoff_seconds: float = Field(
        default=5.0,
        description="Maximum backoff delay in seconds",
        gt=0,
    )
    
    exponential_base: float = Field(
        default=2.0,
        description="Exponential backoff base",
        gt=1.0,
    )
    
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker for agent tool calls",
    )
    
    telemetry_enabled: bool = Field(
        default=True,
        description="Enable telemetry for agent retry attempts",
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
    
    retry: AgnoRetryConfig = Field(
        default_factory=AgnoRetryConfig,
        description="Retry configuration for MCP tool calls",
    )
    
    # Legacy compatibility properties
    @property
    def retry_max_attempts(self) -> int:
        """Legacy property for backward compatibility."""
        return self.retry.max_attempts

    @property
    def model_id(self) -> str:
        """Return the default model ID for agent initialization."""
        return self.default_model

    @property
    def temperature(self) -> float:
        """Return default temperature for model."""
        return 0.7

    @property
    def max_tokens(self) -> int:
        """Return default max tokens for model."""
        return 4096

    @property
    def show_tool_calls(self) -> bool:
        """Return whether to show tool calls in debug mode."""
        return self.debug_mode


class AgentDisabledError(Exception):
    """Raised when attempting to use a disabled agent."""
    pass
