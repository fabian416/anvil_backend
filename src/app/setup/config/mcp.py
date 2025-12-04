"""
MCP Server configuration settings.

Provides granular enable/disable controls for each MCP server.
"""

from pydantic import BaseModel, Field


class MCPServerSettings(BaseModel):
    """Settings for individual MCP servers."""
    
    defillama_enabled: bool = Field(
        default=True,
        description="Enable DeFiLlama MCP server for TVL & protocol data",
    )
    oneinch_enabled: bool = Field(
        default=True,
        description="Enable 1inch MCP server for DEX aggregation",
    )
    thegraph_enabled: bool = Field(
        default=True,
        description="Enable The Graph MCP server for blockchain indexing",
    )
    coingecko_enabled: bool = Field(
        default=True,
        description="Enable CoinGecko MCP server for market data",
    )
    aave_enabled: bool = Field(
        default=True,
        description="Enable Aave MCP server for lending protocol",
    )
    portfolio_enabled: bool = Field(
        default=True,
        description="Enable Portfolio MCP server for tracking",
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


class MCPServerDisabledError(Exception):
    """Raised when attempting to use a disabled MCP server."""
    pass
