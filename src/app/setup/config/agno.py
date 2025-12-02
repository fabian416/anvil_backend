"""Agno agent runtime configuration."""
from typing import Optional
from pydantic import BaseModel


class AgnoConfig(BaseModel):
    """Configuration for Agno agent runtime."""
    
    # Model configuration
    model_id: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # MCP server URLs
    mcp_portfolio_url: str = "http://localhost:8081"
    mcp_1inch_url: str = "http://localhost:8082"
    mcp_aave_url: str = "http://localhost:8083"
    mcp_defillama_url: str = "http://localhost:8084"
    
    # Debug & monitoring
    show_tool_calls: bool = False
    enable_telemetry: bool = True
    log_agent_execution: bool = True
    
    # Performance
    agent_pool_size: int = 10
    agent_timeout_seconds: int = 30
    
    # Memory management
    max_context_messages: int = 10
    enable_memory_compression: bool = True
    
    class Config:
        env_prefix = "AGNO_"


def load_agno_config() -> AgnoConfig:
    """Load Agno configuration from environment."""
    return AgnoConfig()
