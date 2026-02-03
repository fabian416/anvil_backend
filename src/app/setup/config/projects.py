"""
Project Template configuration settings.

Provides granular enable/disable controls for each project template.
"""

from pydantic import BaseModel, Field


class ProjectTemplateSettings(BaseModel):
    """Settings for individual project templates."""

    defi_swing_trader_enabled: bool = Field(
        default=True,
        description="Enable DeFi Swing Trader template (Intermediate users)",
    )
    arbitrage_hunter_enabled: bool = Field(
        default=True,
        description="Enable Arbitrage Hunter template (Expert users)",
    )
    ai_portfolio_manager_enabled: bool = Field(
        default=True,
        description="Enable AI Portfolio Manager template (Long-term investors)",
    )
    conservative_investor_enabled: bool = Field(
        default=True,
        description="Enable Conservative Investor template (Beginners)",
    )
    day_trader_pro_enabled: bool = Field(
        default=True,
        description="Enable Day Trader Pro template (Expert traders)",
    )


class ProjectSettings(BaseModel):
    """Project system configuration settings."""

    enabled: bool = Field(
        default=True,
        description="Master switch for project system",
    )
    templates_enabled: bool = Field(
        default=True,
        description="Master switch for pre-built project templates",
    )
    templates: ProjectTemplateSettings = Field(
        default_factory=ProjectTemplateSettings,
        description="Individual template enable/disable flags",
    )


class TemplateDisabledError(Exception):
    """Raised when attempting to use a disabled template."""

    pass
