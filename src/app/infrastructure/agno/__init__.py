"""Agno Agent Infrastructure.

Provides Agno-based AI agents for DeFi operations, integrated with
MCP (Model Context Protocol) tool servers.

Agents:
    - DeFiAgentBase: Base class for all agents
    - TradingAgent: Trading operations (1inch)
    - LendingAgent: Lending operations (Aave)
    - AnalyticsAgent: Protocol analytics (DeFiLlama)
    - PortfolioAgent: Portfolio management
    - AgentRouter: Intelligent routing to appropriate agent

Performance:
    - AgentResponseCache: Response caching for agents
    - ToolCallBatcher: Parallel tool execution
    - AgentPool: Agent instance pooling
    - AgentMonitor: Performance monitoring
"""

from app.infrastructure.agno.base_agent import DeFiAgentBase, MCPToolDefinition
from app.infrastructure.agno.trading_agent import TradingAgent
from app.infrastructure.agno.lending_agent import LendingAgent
from app.infrastructure.agno.analytics_agent import AnalyticsAgent
from app.infrastructure.agno.portfolio_agent import PortfolioAgent
from app.infrastructure.agno.agent_router import AgentRouter, AgentType
from app.infrastructure.agno.cache import (
    AgentResponseCache,
    get_cache,
    initialize_cache,
)
from app.infrastructure.agno.batch import ToolCallBatcher, ToolCall, ToolResult
from app.infrastructure.agno.pool import AgentPool, PooledAgent, AgentStatus
from app.infrastructure.agno.monitoring import AgentMonitor, AgentMetrics, get_monitor

__all__ = [
    # Core agents
    "DeFiAgentBase",
    "MCPToolDefinition",
    "TradingAgent",
    "LendingAgent",
    "AnalyticsAgent",
    "PortfolioAgent",
    "AgentRouter",
    "AgentType",
    # Performance
    "AgentResponseCache",
    "get_cache",
    "initialize_cache",
    "ToolCallBatcher",
    "ToolCall",
    "ToolResult",
    "AgentPool",
    "PooledAgent",
    "AgentStatus",
    "AgentMonitor",
    "AgentMetrics",
    "get_monitor",
]
