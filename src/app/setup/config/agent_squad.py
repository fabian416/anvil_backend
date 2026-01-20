"""Agent Squad configuration from TOML."""

from pydantic import BaseModel, Field

# Default model for agents (Vertex AI - Gemini)
DEFAULT_AGENT_MODEL = "gemini-2.0-flash"


class AgentConfigModel(BaseModel):
    """Individual agent configuration."""
    enabled: bool = True
    model: str = DEFAULT_AGENT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1000


class AgentSquadAgentsConfig(BaseModel):
    """All 18 agent configurations."""
    # Core user-facing agents
    chat: AgentConfigModel = Field(default_factory=AgentConfigModel)
    hunter_ai: AgentConfigModel = Field(default_factory=AgentConfigModel)
    research: AgentConfigModel = Field(default_factory=AgentConfigModel)
    execution: AgentConfigModel = Field(default_factory=AgentConfigModel)
    risk_analyzer: AgentConfigModel = Field(default_factory=AgentConfigModel)
    portfolio: AgentConfigModel = Field(default_factory=AgentConfigModel)
    tax_optimizer: AgentConfigModel = Field(default_factory=AgentConfigModel)
    defi_yield: AgentConfigModel = Field(default_factory=AgentConfigModel)
    security_auditor: AgentConfigModel = Field(default_factory=AgentConfigModel)
    gas_optimizer: AgentConfigModel = Field(default_factory=AgentConfigModel)

    # Enterprise agents
    compliance_monitor: AgentConfigModel = Field(default_factory=AgentConfigModel)
    multisig_coordinator: AgentConfigModel = Field(default_factory=AgentConfigModel)
    alert_monitoring: AgentConfigModel = Field(default_factory=AgentConfigModel)
    crisis_manager: AgentConfigModel = Field(default_factory=AgentConfigModel)

    # Advanced agents
    bridge_crosschain: AgentConfigModel = Field(default_factory=AgentConfigModel)
    lending_borrowing: AgentConfigModel = Field(default_factory=AgentConfigModel)
    nft_asset_manager: AgentConfigModel = Field(default_factory=AgentConfigModel)
    dao_governance: AgentConfigModel = Field(default_factory=AgentConfigModel)


class ExternalAPIsConfig(BaseModel):
    """External API feature flags configuration."""
    # DeFi Data APIs (Week 1)
    enable_1inch: bool = True
    enable_defillama: bool = True
    enable_coingecko: bool = True
    enable_hyperliquid: bool = True
    enable_uniswap: bool = True
    enable_curve: bool = True
    enable_aave: bool = True
    
    # API Keys (loaded from environment/secrets)
    oneinch_api_key: str = ""  # Optional - loaded from ONEINCH_API_KEY env var

    # Enterprise APIs (Week 2)
    enable_chainalysis: bool = False  # Requires paid license
    enable_trm_labs: bool = False     # Requires paid license
    enable_gnosis_safe: bool = True
    enable_forta: bool = True
    enable_twilio: bool = False       # Requires paid account

    # Advanced APIs (Week 3)
    enable_privy: bool = False        # Requires app ID
    enable_axelar: bool = True
    enable_layerzero: bool = True
    enable_opensea: bool = False      # Requires API key
    enable_snapshot: bool = True


class AgentSquadSettings(BaseModel):
    """Agent Squad configuration from TOML."""
    # Master toggle
    enabled: bool = True

    # Intent classification
    enable_intent_classification: bool = True
    log_intent_classification: bool = False
    log_agent_selection: bool = False  # Log agent selection decisions
    intent_classification_model: str = DEFAULT_AGENT_MODEL  # gemini-2.0-flash (Vertex AI)
    intent_confidence_threshold: float = 0.85
    fallback_agent: str = "chat"
    max_context_messages: int = 10

    # Supervisor coordination
    enable_supervisor: bool = True
    supervisor_model: str = DEFAULT_AGENT_MODEL  # gemini-2.0-flash (Vertex AI)
    supervisor_max_agents: int = 5
    supervisor_timeout_seconds: int = 120

    # Context preservation
    conversation_history_limit: int = 20
    context_window_tokens: int = 8000

    # Performance
    max_concurrent_agents: int = 3
    routing_timeout_seconds: int = 5
    execution_timeout_seconds: int = 60

    # Storage
    storage_backend: str = "postgresql"
    storage_ttl_seconds: int = 86400  # 24 hours

    # Telemetry
    telemetry_enabled: bool = True
    telemetry_sample_rate: float = 1.0

    # External API feature flags
    external_apis: ExternalAPIsConfig = Field(default_factory=ExternalAPIsConfig)

    # Per-agent configuration
    agents: AgentSquadAgentsConfig = Field(default_factory=AgentSquadAgentsConfig)
    
    # Flag to use agent-squad library vs hand-rolled implementation
    use_agent_squad: bool = False

    # Default model for agents (Vertex AI native name)
    default_model: str = DEFAULT_AGENT_MODEL  # gemini-2.0-flash (Vertex AI)

    # DEMO MODE: Use pre-built demo handlers instead of real LLM calls
    # When enabled, authenticated users get the same responses as /guest/chat
    # This is useful for demos and testing without requiring LLM API costs
    use_demo_mode: bool = False  # Changed to False to enable real LLM for authenticated users

    # Debug settings
    debug_agent_timing: bool = False  # Include agent execution timing in responses (for performance analysis)


# Alias for backward compatibility
AgentSquadConfig = AgentSquadSettings


def load_agent_squad_config(use_agent_squad: bool = False) -> AgentSquadConfig:
    """
    Load Agent Squad configuration.
    
    Args:
        use_agent_squad: Whether to use agent-squad library implementation
    
    Returns:
        AgentSquadConfig instance with default settings
    """
    import os
    config = AgentSquadSettings()
    
    # Load API keys from environment
    oneinch_api_key = os.getenv("ONEINCH_API_KEY", "")
    if oneinch_api_key:
        config.external_apis.oneinch_api_key = oneinch_api_key
    
    # Override use_agent_squad if specified
    if use_agent_squad:
        config = config.model_copy(update={"use_agent_squad": True})
    return config
