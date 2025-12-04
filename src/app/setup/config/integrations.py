"""
Integration feature flags configuration.

Controls which integration features are enabled/disabled via environment variables.
"""

from pydantic import BaseModel, Field


class ChatIntegrationSettings(BaseModel):
    """
    Chat integration feature flags.
    
    Controls whether chat messages can trigger Hunter AI and ULTRA tools.
    """
    
    enabled: bool = Field(
        default=True,
        description="Master switch for all chat integration features",
    )
    
    hunter_tools_enabled: bool = Field(
        default=True,
        description="Enable Hunter AI tools in chat (sentiment, prediction, risk, signals, portfolio, patterns)",
    )
    
    ultra_tools_enabled: bool = Field(
        default=True,
        description="Enable ULTRA Arbitrage tools in chat (flash loans, arbitrage, MEV, auto-executor)",
    )
    
    comprehensive_analysis_enabled: bool = Field(
        default=True,
        description="Enable comprehensive analysis (parallel execution of multiple tools)",
    )
    
    max_parallel_tools: int = Field(
        default=10,
        description="Maximum number of tools to execute in parallel",
        ge=1,
        le=20,
    )


class ProjectIntegrationSettings(BaseModel):
    """
    Project integration feature flags.
    
    Controls whether projects can scope conversations and enforce tool permissions.
    """
    
    enabled: bool = Field(
        default=True,
        description="Master switch for project integration features",
    )
    
    templates_enabled: bool = Field(
        default=True,
        description="Enable pre-built project templates",
    )
    
    risk_validation_enabled: bool = Field(
        default=True,
        description="Enable risk limit validation (max_risk_tolerance, max_capital, etc.)",
    )
    
    tool_permissions_enabled: bool = Field(
        default=True,
        description="Enable tool permission enforcement (enabled_tools filtering)",
    )


class IntegrationSettings(BaseModel):
    """
    Master integration settings.
    
    Controls all chat and project integration features via environment variables.
    """
    
    chat: ChatIntegrationSettings = Field(
        default_factory=ChatIntegrationSettings,
        description="Chat integration settings",
    )
    
    projects: ProjectIntegrationSettings = Field(
        default_factory=ProjectIntegrationSettings,
        description="Project integration settings",
    )
