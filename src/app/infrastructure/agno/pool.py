"""Agent Pooling.

Manages a pool of reusable agent instances to reduce initialization overhead.

Features:
    - Agent instance pooling
    - Lazy initialization
    - Resource management
    - Usage statistics
    - Automatic cleanup
"""
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from app.infrastructure.agno import (
    TradingAgent,
    LendingAgent,
    AnalyticsAgent,
    PortfolioAgent,
    AgentType,
)
from app.setup.config.agno import AgnoConfig


logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent instance status."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    INITIALIZING = "initializing"
    ERROR = "error"


@dataclass
class PooledAgent:
    """Represents a pooled agent instance."""
    
    agent: any  # TradingAgent | LendingAgent | AnalyticsAgent | PortfolioAgent
    agent_type: AgentType
    status: AgentStatus = AgentStatus.AVAILABLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0
    
    def mark_in_use(self):
        """Mark agent as in use."""
        self.status = AgentStatus.IN_USE
        self.last_used_at = datetime.utcnow()
        self.use_count += 1
    
    def mark_available(self):
        """Mark agent as available."""
        self.status = AgentStatus.AVAILABLE
    
    def mark_error(self):
        """Mark agent as error."""
        self.status = AgentStatus.ERROR
        self.error_count += 1


class AgentPool:
    """
    Manages a pool of reusable agent instances.
    
    Reduces initialization overhead by maintaining a pool of pre-initialized
    agents that can be reused across multiple requests.
    
    Usage:
        pool = AgentPool(config, pool_size=5)
        await pool.initialize()
        
        # Acquire agent
        agent = await pool.acquire(AgentType.TRADING)
        
        try:
            result = await agent.run("Swap ETH for USDC")
        finally:
            # Release agent back to pool
            await pool.release(AgentType.TRADING, agent)
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        pool_size: int = 3,
        max_pool_size: int = 10,
    ):
        """
        Initialize agent pool.
        
        Args:
            config: Agno configuration
            pool_size: Initial pool size per agent type
            max_pool_size: Maximum pool size per agent type
        """
        self.config = config
        self.pool_size = pool_size
        self.max_pool_size = max_pool_size
        
        # Pools per agent type
        self.pools: Dict[AgentType, List[PooledAgent]] = {
            AgentType.TRADING: [],
            AgentType.LENDING: [],
            AgentType.ANALYTICS: [],
            AgentType.PORTFOLIO: [],
        }
        
        # Locks for thread-safe access
        self.locks: Dict[AgentType, asyncio.Lock] = {
            agent_type: asyncio.Lock()
            for agent_type in AgentType
            if agent_type != AgentType.MULTI
        }
        
        # Statistics
        self._stats = {
            agent_type: {
                "acquires": 0,
                "releases": 0,
                "creates": 0,
                "errors": 0,
            }
            for agent_type in AgentType
            if agent_type != AgentType.MULTI
        }
    
    async def initialize(self):
        """Initialize agent pools."""
        logger.info(f"Initializing agent pools (size={self.pool_size})...")
        
        for agent_type in [AgentType.TRADING, AgentType.LENDING, AgentType.ANALYTICS, AgentType.PORTFOLIO]:
            for _ in range(self.pool_size):
                await self._create_agent(agent_type)
        
        logger.info("Agent pools initialized")
    
    async def _create_agent(self, agent_type: AgentType) -> PooledAgent:
        """
        Create a new agent instance.
        
        Args:
            agent_type: Agent type to create
        
        Returns:
            Pooled agent instance
        """
        try:
            # Create agent based on type
            if agent_type == AgentType.TRADING:
                agent = TradingAgent(self.config)
            elif agent_type == AgentType.LENDING:
                agent = LendingAgent(self.config)
            elif agent_type == AgentType.ANALYTICS:
                agent = AnalyticsAgent(self.config)
            elif agent_type == AgentType.PORTFOLIO:
                agent = PortfolioAgent(self.config)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            # Load MCP tools
            await agent.load_mcp_tools()
            
            # Create pooled agent
            pooled = PooledAgent(
                agent=agent,
                agent_type=agent_type,
                status=AgentStatus.AVAILABLE,
            )
            
            self._stats[agent_type]["creates"] += 1
            logger.debug(f"Created {agent_type.value} agent")
            
            return pooled
        
        except Exception as e:
            logger.error(f"Failed to create {agent_type.value} agent: {e}")
            raise
    
    async def acquire(self, agent_type: AgentType, timeout: float = 30.0) -> any:
        """
        Acquire an agent from the pool.
        
        Args:
            agent_type: Agent type to acquire
            timeout: Timeout in seconds
        
        Returns:
            Agent instance
        
        Raises:
            TimeoutError: If no agent available within timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        async with self.locks[agent_type]:
            self._stats[agent_type]["acquires"] += 1
            
            while True:
                # Check for available agent
                for pooled in self.pools[agent_type]:
                    if pooled.status == AgentStatus.AVAILABLE:
                        pooled.mark_in_use()
                        logger.debug(f"Acquired {agent_type.value} agent (use count: {pooled.use_count})")
                        return pooled.agent
                
                # No available agent, create new if below max
                if len(self.pools[agent_type]) < self.max_pool_size:
                    pooled = await self._create_agent(agent_type)
                    self.pools[agent_type].append(pooled)
                    pooled.mark_in_use()
                    logger.debug(f"Created and acquired {agent_type.value} agent")
                    return pooled.agent
                
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(f"No {agent_type.value} agent available within {timeout}s")
                
                # Wait and retry
                await asyncio.sleep(0.1)
    
    async def release(self, agent_type: AgentType, agent: any):
        """
        Release an agent back to the pool.
        
        Args:
            agent_type: Agent type
            agent: Agent instance to release
        """
        async with self.locks[agent_type]:
            self._stats[agent_type]["releases"] += 1
            
            # Find pooled agent
            for pooled in self.pools[agent_type]:
                if pooled.agent is agent:
                    pooled.mark_available()
                    logger.debug(f"Released {agent_type.value} agent")
                    return
            
            logger.warning(f"Agent not found in pool: {agent_type.value}")
    
    async def close(self):
        """Close all agents and cleanup resources."""
        logger.info("Closing agent pools...")
        
        for agent_type, pool in self.pools.items():
            for pooled in pool:
                # Agent cleanup if needed
                pass
            pool.clear()
        
        logger.info("Agent pools closed")
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get pool statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {}
        
        for agent_type in [AgentType.TRADING, AgentType.LENDING, AgentType.ANALYTICS, AgentType.PORTFOLIO]:
            pool = self.pools[agent_type]
            
            stats[agent_type.value] = {
                "pool_size": len(pool),
                "available": sum(1 for p in pool if p.status == AgentStatus.AVAILABLE),
                "in_use": sum(1 for p in pool if p.status == AgentStatus.IN_USE),
                "errors": sum(1 for p in pool if p.status == AgentStatus.ERROR),
                "total_acquires": self._stats[agent_type]["acquires"],
                "total_releases": self._stats[agent_type]["releases"],
                "total_creates": self._stats[agent_type]["creates"],
                "total_errors": self._stats[agent_type]["errors"],
            }
        
        return stats


# Context manager for automatic release

class PooledAgentContext:
    """
    Context manager for automatic agent acquisition and release.
    
    Usage:
        async with pool.agent(AgentType.TRADING) as agent:
            result = await agent.run("Swap ETH for USDC")
    """
    
    def __init__(self, pool: AgentPool, agent_type: AgentType):
        """
        Initialize context.
        
        Args:
            pool: Agent pool
            agent_type: Agent type to acquire
        """
        self.pool = pool
        self.agent_type = agent_type
        self.agent = None
    
    async def __aenter__(self):
        """Acquire agent."""
        self.agent = await self.pool.acquire(self.agent_type)
        return self.agent
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release agent."""
        if self.agent:
            await self.pool.release(self.agent_type, self.agent)


# Add context manager method to AgentPool

def _add_context_manager():
    """Add context manager method to AgentPool."""
    def agent(self, agent_type: AgentType) -> PooledAgentContext:
        """
        Get agent context manager.
        
        Args:
            agent_type: Agent type
        
        Returns:
            Context manager
        """
        return PooledAgentContext(self, agent_type)
    
    AgentPool.agent = agent


_add_context_manager()
