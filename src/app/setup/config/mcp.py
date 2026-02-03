"""
MCP Server configuration settings.

Provides granular enable/disable controls for each MCP server.
"""

from pydantic import BaseModel, Field


class MCPServerSettings(BaseModel):
    """Settings for individual MCP servers."""

    # Analytics & Data
    defillama_enabled: bool = Field(
        default=True,
        description="Enable DeFiLlama MCP server for TVL & protocol data",
    )
    coingecko_enabled: bool = Field(
        default=True,
        description="Enable CoinGecko MCP server for market data",
    )
    thegraph_enabled: bool = Field(
        default=True,
        description="Enable The Graph MCP server for blockchain indexing",
    )
    perplexity_enabled: bool = Field(
        default=True,
        description="Enable Perplexity MCP server for AI-powered search & research",
    )

    # Trading & DEX
    oneinch_enabled: bool = Field(
        default=True,
        description="Enable 1inch MCP server for DEX aggregation",
    )
    curve_enabled: bool = Field(
        default=True,
        description="Enable Curve Finance MCP server for stable swaps & liquidity pools",
    )

    # Lending
    aave_enabled: bool = Field(
        default=True,
        description="Enable Aave MCP server for lending protocol",
    )
    morpho_enabled: bool = Field(
        default=True,
        description="Enable Morpho Protocol MCP server for yield optimization",
    )

    # Perpetuals
    hyperliquid_enabled: bool = Field(
        default=True,
        description="Enable Hyperliquid MCP server for perpetual futures trading",
    )

    # Cross-chain
    layerzero_enabled: bool = Field(
        default=True,
        description="Enable LayerZero MCP server for cross-chain messaging",
    )

    # Portfolio
    portfolio_enabled: bool = Field(
        default=True,
        description="Enable Portfolio MCP server for tracking",
    )


class MCPRetrySettings(BaseModel):
    """Settings for MCP server retry behavior."""

    enabled: bool = Field(
        default=True,
        description="Enable retry logic for MCP servers",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
    )
    initial_backoff_seconds: float = Field(
        default=1.0,
        description="Initial backoff delay in seconds",
    )
    max_backoff_seconds: float = Field(
        default=30.0,
        description="Maximum backoff delay in seconds",
    )
    backoff_multiplier: float = Field(
        default=2.0,
        description="Multiplier for exponential backoff",
    )


class MCPSettings(BaseModel):
    """MCP configuration settings."""

    enabled: bool = Field(
        default=True,
        description="Master switch for all MCP servers",
    )
    servers: MCPServerSettings = Field(
        default_factory=MCPServerSettings,
        description="Individual server enable/disable flags",
    )
    retry: MCPRetrySettings = Field(
        default_factory=MCPRetrySettings,
        description="Retry configuration for MCP servers",
    )


class MCPServerDisabledError(Exception):
    """Raised when attempting to use a disabled MCP server."""

    pass
