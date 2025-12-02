"""Agent Router - Intelligent Query Routing to Specialized Agents.

Routes user queries to the most appropriate specialized agent based on
intent classification and query analysis.

Routing Logic:
    - Trading queries → TradingAgent (1inch)
    - Lending queries → LendingAgent (Aave)
    - Analytics queries → AnalyticsAgent (DeFiLlama)
    - Portfolio queries → PortfolioAgent
    - Multi-domain queries → Orchestrates multiple agents

Examples:
    - "Swap ETH for USDC" → TradingAgent
    - "Supply USDC to Aave" → LendingAgent
    - "What's Aave's TVL?" → AnalyticsAgent
    - "Show my portfolio" → PortfolioAgent
    - "Find best yield and show my positions" → AnalyticsAgent + PortfolioAgent
"""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from app.infrastructure.agno.base_agent import DeFiAgentBase
from app.infrastructure.agno.trading_agent import TradingAgent
from app.infrastructure.agno.lending_agent import LendingAgent
from app.infrastructure.agno.analytics_agent import AnalyticsAgent
from app.infrastructure.agno.portfolio_agent import PortfolioAgent
from app.setup.config.agno import AgnoConfig


class AgentType(Enum):
    """Types of specialized agents."""
    TRADING = "trading"
    LENDING = "lending"
    ANALYTICS = "analytics"
    PORTFOLIO = "portfolio"
    MULTI = "multi"  # Requires multiple agents


class AgentRouter:
    """
    Intelligent router for specialized DeFi agents.
    
    Analyzes user queries and routes them to the most appropriate agent:
    - TradingAgent: For swaps, prices, DEX operations
    - LendingAgent: For lending, borrowing, health factors
    - AnalyticsAgent: For protocol research, yields, TVL
    - PortfolioAgent: For balance checks, position tracking
    
    Can also orchestrate multiple agents for complex queries.
    
    Usage:
        config = AgnoConfig(...)
        router = AgentRouter(config)
        await router.initialize()
        
        result = await router.route("Swap 1 ETH for USDC")
        print(result.content)
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        debug_mode: bool = False,
    ):
        """
        Initialize Agent Router.
        
        Args:
            config: Agno configuration
            debug_mode: Enable debug logging
        """
        self.config = config
        self.debug_mode = debug_mode
        
        # Specialized agents (initialized on first use)
        self.agents: Dict[AgentType, DeFiAgentBase] = {}
        self._initialized = False
        
        # Intent keywords for routing
        self.intent_keywords = {
            AgentType.TRADING: [
                "swap", "trade", "exchange", "buy", "sell",
                "price", "quote", "route", "dex", "1inch",
                "liquidity source", "gas cost", "slippage",
            ],
            AgentType.LENDING: [
                "lend", "borrow", "supply", "withdraw", "repay",
                "collateral", "health factor", "liquidation",
                "aave", "compound", "interest rate", "apy",
                "loan", "debt", "ltv",
            ],
            AgentType.ANALYTICS: [
                "tvl", "protocol", "yield", "apy", "farm",
                "compare", "analysis", "trending", "growth",
                "defillama", "fees", "revenue", "stablecoin",
                "market", "data", "stats", "metrics",
            ],
            AgentType.PORTFOLIO: [
                "balance", "portfolio", "positions", "holdings",
                "wallet", "assets", "total value", "net worth",
                "my", "show me", "track", "monitor",
            ],
        }
    
    async def initialize(self):
        """
        Initialize all specialized agents.
        
        Creates and loads MCP tools for each agent.
        """
        if self._initialized:
            return
        
        if self.debug_mode:
            print("[Router] Initializing specialized agents...")
        
        # Create agents
        self.agents[AgentType.TRADING] = TradingAgent(
            self.config,
            debug_mode=self.debug_mode,
        )
        self.agents[AgentType.LENDING] = LendingAgent(
            self.config,
            debug_mode=self.debug_mode,
        )
        self.agents[AgentType.ANALYTICS] = AnalyticsAgent(
            self.config,
            debug_mode=self.debug_mode,
        )
        self.agents[AgentType.PORTFOLIO] = PortfolioAgent(
            self.config,
            debug_mode=self.debug_mode,
        )
        
        # Load MCP tools for each agent
        for agent_type, agent in self.agents.items():
            if self.debug_mode:
                print(f"[Router] Loading tools for {agent_type.value}...")
            await agent.load_mcp_tools()
        
        self._initialized = True
        
        if self.debug_mode:
            print(f"[Router] ✅ All {len(self.agents)} agents initialized!")
    
    def classify_intent(self, query: str) -> Tuple[AgentType, float]:
        """
        Classify user intent based on query keywords.
        
        Args:
            query: User query text
        
        Returns:
            Tuple of (agent_type, confidence_score)
        """
        query_lower = query.lower()
        
        # Count keyword matches for each agent type
        scores = {}
        for agent_type, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[agent_type] = score
        
        if not scores:
            # Default to analytics for general questions
            return AgentType.ANALYTICS, 0.5
        
        # Get agent with highest score
        best_agent = max(scores.items(), key=lambda x: x[1])
        
        # Calculate confidence (normalize by max possible matches)
        max_keywords = max(len(keywords) for keywords in self.intent_keywords.values())
        confidence = min(best_agent[1] / 3.0, 1.0)  # Cap at 1.0, ~3 keywords = high confidence
        
        # Check for multi-agent need (multiple high scores)
        high_scores = [agent_type for agent_type, score in scores.items() if score >= 2]
        if len(high_scores) > 1:
            return AgentType.MULTI, 0.8
        
        return best_agent[0], confidence
    
    async def route(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        stream: bool = False,
    ):
        """
        Route query to appropriate agent(s).
        
        Args:
            query: User query
            user_id: User identifier
            session_id: Session identifier
            stream: Whether to stream response
        
        Returns:
            Agent response
        """
        # Ensure agents are initialized
        if not self._initialized:
            await self.initialize()
        
        # Classify intent
        agent_type, confidence = self.classify_intent(query)
        
        if self.debug_mode:
            print(f"[Router] Query: {query[:60]}...")
            print(f"[Router] Classified as: {agent_type.value} (confidence: {confidence:.2f})")
        
        # Route to appropriate agent(s)
        if agent_type == AgentType.MULTI:
            # Multi-agent orchestration (future enhancement)
            # For now, default to analytics
            if self.debug_mode:
                print("[Router] Multi-agent query detected, using Analytics agent")
            agent = self.agents[AgentType.ANALYTICS]
        else:
            agent = self.agents[agent_type]
        
        if self.debug_mode:
            print(f"[Router] Routing to: {agent.name}")
        
        # Execute query
        result = await agent.run(
            query,
            user_id=user_id,
            session_id=session_id,
            stream=stream,
        )
        
        return result
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about all available agents.
        
        Returns:
            Dictionary with agent information
        """
        info = {
            "router_status": "initialized" if self._initialized else "not_initialized",
            "agents_count": len(self.agents),
            "agents": {},
        }
        
        for agent_type, agent in self.agents.items():
            info["agents"][agent_type.value] = {
                "name": agent.name,
                "role": agent.role,
                "tools_count": len(agent.mcp_tools),
                "servers": agent.mcp_servers,
            }
        
        return info


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agent_router():
        """Test agent router with various queries."""
        # Create config
        config = AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
        )
        
        # Create router
        router = AgentRouter(config, debug_mode=True)
        
        # Initialize agents
        print("\n🔧 Initializing agent router...")
        await router.initialize()
        
        # Show agent info
        info = router.get_agent_info()
        print(f"\n✅ Router initialized with {info['agents_count']} agents:")
        for agent_type, agent_info in info["agents"].items():
            print(f"   • {agent_info['name']}: {agent_info['tools_count']} tools")
        
        # Test queries for each agent type
        test_queries = [
            # Trading queries
            ("Swap 1 ETH for USDC on Ethereum", AgentType.TRADING),
            ("What's the current price of WBTC?", AgentType.TRADING),
            
            # Lending queries
            ("Supply 1000 USDC to Aave", AgentType.LENDING),
            ("What's my health factor?", AgentType.LENDING),
            
            # Analytics queries
            ("What's the TVL of Uniswap?", AgentType.ANALYTICS),
            ("Find best stablecoin yields", AgentType.ANALYTICS),
            
            # Portfolio queries
            ("Show me my portfolio", AgentType.PORTFOLIO),
            ("What's my ETH balance?", AgentType.PORTFOLIO),
        ]
        
        print("\n" + "="*70)
        print("AGENT ROUTER TEST")
        print("="*70)
        
        for query, expected_type in test_queries:
            print(f"\n📝 User: {query}")
            
            # Classify intent
            agent_type, confidence = router.classify_intent(query)
            print(f"🎯 Classified: {agent_type.value} (confidence: {confidence:.2f})")
            
            # Check if correct
            if agent_type == expected_type:
                print("✅ Correct routing!")
            else:
                print(f"⚠️  Expected {expected_type.value}, got {agent_type.value}")
            
            print("-"*70)
    
    # Run test
    print("""
╔══════════════════════════════════════════════════════════╗
║          Agent Router - Intelligent Routing              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_agent_router())
