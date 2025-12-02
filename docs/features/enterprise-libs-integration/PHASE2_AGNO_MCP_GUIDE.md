# Phase 2: Agno + MCP Implementation Guide

**Priority**: 🥇 Highest (Biggest DX Win)  
**Duration**: 8 weeks  
**Team**: 2 Backend Devs + 0.5 DevOps  
**Dependencies**: None  

---

## 📋 Why Agno First?

**Strategic Reasons**:
1. **80% faster agent development** - Immediate productivity gain
2. **Low risk** - MCP is a proven, mature pattern
3. **Foundation for other phases** - Agent Squad can use Agno agents
4. **Performance critical** - Handles 10K concurrent users

**Technical Reasons**:
1. **µs instantiation** - Agno agents start in <100ms (vs. 400ms current)
2. **Tool abstraction** - No more hardcoded API integrations
3. **Built-in telemetry** - Auto-populates `agent_executions` table
4. **Memory management** - Efficient context window handling

---

## 🏗️ Architecture Overview

### Current State
```python
# src/app/infrastructure/adapters/ai/agent_gateway_impl.py
class AgentGatewayImpl:
    async def process_message(self, message):
        # Manual routing, hardcoded integrations
        intent = self._classify_intent_simple(message)
        
        # Hardcoded LLM call
        response = await self.llm_gateway.generate(
            prompt=message,
            system_message=self._get_system_prompt(intent)
        )
        
        # Manual tool integration (if needed)
        if intent == "trade_swap":
            # Hardcoded 1inch API call
            data = requests.post("https://api.1inch.dev/swap", ...)
```

### Target State (Agno + MCP)
```python
# src/app/infrastructure/agents/agno/trading_agent.py
from agno import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

trading_agent = Agent(
    name="DeFi Trading Agent",
    model=OpenAIChat(id="gpt-4-turbo"),
    tools=[
        MCPTools(url="http://localhost:8080/mcp/1inch"),
        MCPTools(url="http://localhost:8080/mcp/aave"),
        MCPTools(url="http://localhost:8080/mcp/portfolio"),
    ],
    instructions="""You are a DeFi trading specialist.
    Use the available tools to:
    - Get swap quotes
    - Execute swaps
    - Check allowances
    - Monitor positions""",
    markdown=True,
    show_tool_calls=True,  # For debugging
)

# Agent auto-discovers tools and calls them as needed
response = await trading_agent.run(user_message)
```

---

## 📦 Deliverables Breakdown

### Week 1-2: MCP Server Infrastructure

**Goal**: Build the foundation for MCP tool servers

#### 1.1: MCP Server Base Class
**File**: `src/app/infrastructure/mcp/base.py`

```python
"""Base MCP server implementation."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable


class MCPServer(ABC):
    """Base MCP server for exposing tools to agents."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.app = FastAPI(title=f"{name} MCP Server")
        
        # Register MCP endpoints
        self._register_routes()
    
    def _register_routes(self):
        """Register standard MCP routes."""
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools."""
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                    for tool in self.tools.values()
                ]
            }
        
        @self.app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, params: Dict[str, Any]):
            """Call a specific tool."""
            if tool_name not in self.tools:
                raise HTTPException(404, f"Tool '{tool_name}' not found")
            
            tool = self.tools[tool_name]
            try:
                result = await tool.handler(**params)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ):
        """Register a tool with this MCP server."""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
    
    @abstractmethod
    def setup_tools(self):
        """Subclasses override this to register their tools."""
        pass
```

#### 1.2: 1inch MCP Server
**File**: `src/app/infrastructure/mcp/protocols/oneinch_mcp.py`

```python
"""1inch DEX MCP server."""
from app.infrastructure.mcp.base import MCPServer
from app.infrastructure.defi.oneinch_client import OneInchClient


class OneInchMCPServer(MCPServer):
    """MCP server for 1inch DEX operations."""
    
    def __init__(self, api_key: str):
        super().__init__(name="1inch", version="1.0.0")
        self.client = OneInchClient(api_key=api_key)
        self.setup_tools()
    
    def setup_tools(self):
        """Register 1inch tools."""
        
        # Tool 1: Get swap quote
        self.register_tool(
            name="get_swap_quote",
            description="Get a quote for swapping tokens on 1inch",
            parameters={
                "type": "object",
                "properties": {
                    "from_token": {"type": "string", "description": "Source token address"},
                    "to_token": {"type": "string", "description": "Destination token address"},
                    "amount": {"type": "number", "description": "Amount to swap (in wei)"},
                    "chain_id": {"type": "integer", "description": "Chain ID (default: 1 for Ethereum)"},
                },
                "required": ["from_token", "to_token", "amount"],
            },
            handler=self._get_swap_quote,
        )
        
        # Tool 2: Execute swap
        self.register_tool(
            name="execute_swap",
            description="Execute a token swap on 1inch",
            parameters={
                "type": "object",
                "properties": {
                    "from_token": {"type": "string"},
                    "to_token": {"type": "string"},
                    "amount": {"type": "number"},
                    "from_address": {"type": "string"},
                    "slippage": {"type": "number", "description": "Max slippage % (default: 1)"},
                    "chain_id": {"type": "integer"},
                },
                "required": ["from_token", "to_token", "amount", "from_address"],
            },
            handler=self._execute_swap,
        )
        
        # Tool 3: Check allowance
        self.register_tool(
            name="check_allowance",
            description="Check token allowance for 1inch router",
            parameters={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string"},
                    "wallet_address": {"type": "string"},
                    "chain_id": {"type": "integer"},
                },
                "required": ["token_address", "wallet_address"],
            },
            handler=self._check_allowance,
        )
    
    async def _get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain_id: int = 1,
    ) -> Dict[str, Any]:
        """Get swap quote from 1inch."""
        quote = await self.client.get_quote(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            chain_id=chain_id,
        )
        return {
            "from_token": from_token,
            "to_token": to_token,
            "amount_in": amount,
            "amount_out": quote["toTokenAmount"],
            "estimated_gas": quote["estimatedGas"],
            "price_impact": quote.get("priceImpact", "0"),
        }
    
    async def _execute_swap(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        from_address: str,
        slippage: float = 1.0,
        chain_id: int = 1,
    ) -> Dict[str, Any]:
        """Execute swap on 1inch."""
        # This would call the actual 1inch API
        # For now, return a mock transaction
        return {
            "tx_hash": "0x...",
            "status": "pending",
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
        }
    
    async def _check_allowance(
        self,
        token_address: str,
        wallet_address: str,
        chain_id: int = 1,
    ) -> Dict[str, Any]:
        """Check token allowance."""
        allowance = await self.client.check_allowance(
            token_address=token_address,
            wallet_address=wallet_address,
            chain_id=chain_id,
        )
        return {
            "token": token_address,
            "wallet": wallet_address,
            "allowance": allowance,
            "needs_approval": allowance < 1e18,  # Example threshold
        }
```

#### 1.3: Portfolio MCP Server (Internal)
**File**: `src/app/infrastructure/mcp/internal/portfolio_mcp.py`

```python
"""Internal portfolio MCP server."""
from app.infrastructure.mcp.base import MCPServer
from app.domain.ports.portfolio_repository import PortfolioRepository


class PortfolioMCPServer(MCPServer):
    """MCP server for internal portfolio operations."""
    
    def __init__(self, portfolio_repo: PortfolioRepository):
        super().__init__(name="portfolio", version="1.0.0")
        self.portfolio_repo = portfolio_repo
        self.setup_tools()
    
    def setup_tools(self):
        """Register portfolio tools."""
        
        self.register_tool(
            name="get_user_balance",
            description="Get user's token balances",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "chain_id": {"type": "integer"},
                },
                "required": ["user_id"],
            },
            handler=self._get_user_balance,
        )
        
        self.register_tool(
            name="get_positions",
            description="Get user's open positions (lending, staking, LPs)",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "protocol": {"type": "string", "description": "Filter by protocol"},
                },
                "required": ["user_id"],
            },
            handler=self._get_positions,
        )
    
    async def _get_user_balance(
        self,
        user_id: str,
        chain_id: int = 1,
    ) -> Dict[str, Any]:
        """Get user balances."""
        balances = await self.portfolio_repo.get_balances(user_id, chain_id)
        return {
            "user_id": user_id,
            "chain_id": chain_id,
            "balances": [
                {
                    "token": b["token"],
                    "symbol": b["symbol"],
                    "balance": b["balance"],
                    "usd_value": b["usd_value"],
                }
                for b in balances
            ],
            "total_usd": sum(b["usd_value"] for b in balances),
        }
    
    async def _get_positions(
        self,
        user_id: str,
        protocol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get user positions."""
        positions = await self.portfolio_repo.get_positions(user_id, protocol)
        return {
            "user_id": user_id,
            "positions": [
                {
                    "protocol": p["protocol"],
                    "type": p["type"],  # lending, staking, lp
                    "token": p["token"],
                    "amount": p["amount"],
                    "usd_value": p["usd_value"],
                    "apy": p["apy"],
                }
                for p in positions
            ],
        }
```

---

### Week 3-4: Agno Agent Implementation

**Goal**: Convert existing agents to use Agno + MCP tools

#### 2.1: Agno Trading Agent
**File**: `src/app/infrastructure/agents/agno/trading_agent.py`

```python
"""Agno-powered trading agent with MCP tools."""
from agno import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from app.setup.config.agno import AgnoConfig


def create_trading_agent(config: AgnoConfig) -> Agent:
    """Create a trading agent with Agno."""
    
    return Agent(
        name="DeFi Trading Agent",
        agent_id="trading-agent-v1",
        model=OpenAIChat(
            id=config.model_id or "gpt-4-turbo",
            temperature=0.3,  # Low temperature for precise execution
        ),
        tools=[
            # MCP tool servers (auto-discovery)
            MCPTools(url="http://localhost:8080/mcp/1inch"),
            MCPTools(url="http://localhost:8080/mcp/aave"),
            MCPTools(url="http://localhost:8080/mcp/portfolio"),
        ],
        instructions="""You are a DeFi trading specialist.

Your capabilities:
- Execute token swaps on DEXes (1inch, Uniswap)
- Supply/borrow on lending protocols (Aave, Compound)
- Check user balances and positions
- Analyze swap routes and gas costs

When a user asks to trade:
1. Check their current balance first (use get_user_balance)
2. Get a swap quote (use get_swap_quote)
3. Explain the trade details (amount, price impact, gas)
4. Ask for confirmation
5. Execute the swap (use execute_swap) only after confirmation

Always prioritize safety:
- Check slippage
- Warn about high price impact (>2%)
- Verify user has sufficient balance
- Check token allowances first

Be concise but complete. Use markdown formatting.""",
        
        # Telemetry
        markdown=True,
        show_tool_calls=config.show_tool_calls,
        monitoring=True,  # Agno's built-in telemetry
        
        # Memory
        add_history_to_messages=True,
        num_history_responses=5,  # Last 5 exchanges
    )


# Example usage:
# agent = create_trading_agent(config)
# response = await agent.run("Swap 1 ETH for USDC")
```

#### 2.2: Agno Research Agent
**File**: `src/app/infrastructure/agents/agno/research_agent.py`

```python
"""Agno-powered research agent."""
from agno import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.knowledge import Knowledge
from app.setup.config.agno import AgnoConfig


def create_research_agent(
    config: AgnoConfig,
    knowledge_base_id: str,
) -> Agent:
    """Create a research agent with knowledge base access."""
    
    return Agent(
        name="DeFi Research Agent",
        agent_id="research-agent-v1",
        model=OpenAIChat(id=config.model_id or "gpt-4-turbo"),
        tools=[
            MCPTools(url="http://localhost:8080/mcp/defillama"),
            MCPTools(url="http://localhost:8080/mcp/coingecko"),
        ],
        knowledge=Knowledge(
            # Integrate with our existing pgvector knowledge base
            # This is a custom adapter we'll build
            sources=[
                f"anvil://knowledge_base/{knowledge_base_id}"
            ],
            num_documents=5,  # Top 5 relevant chunks
        ),
        instructions="""You are a DeFi research specialist.

Your capabilities:
- Answer questions about DeFi protocols
- Provide market data (TVL, APY, prices)
- Explain protocol mechanics
- Compare protocols

Always:
- Cite sources (protocol docs, audits)
- Provide data-backed insights
- Explain risks and trade-offs
- Use markdown for clarity

When asked about a protocol:
1. Fetch latest data (use defillama tools)
2. Query knowledge base for protocol details
3. Synthesize into clear explanation""",
        
        markdown=True,
        show_tool_calls=config.show_tool_calls,
        monitoring=True,
    )
```

#### 2.3: Agno Gateway Adapter
**File**: `src/app/infrastructure/adapters/ai/agno_gateway.py`

```python
"""Agno-based agent gateway."""
from typing import Dict, Any, Optional
from uuid import UUID

from app.domain.ports.ai.agent_gateway import AgentGateway
from app.infrastructure.agents.agno.trading_agent import create_trading_agent
from app.infrastructure.agents.agno.research_agent import create_research_agent
from app.infrastructure.agents.agno.risk_agent import create_risk_agent
from app.infrastructure.agents.agno.portfolio_agent import create_portfolio_agent
from app.setup.config.agno import AgnoConfig


class AgnoGateway(AgentGateway):
    """Agent gateway powered by Agno agents."""
    
    def __init__(self, config: AgnoConfig):
        self.config = config
        
        # Initialize Agno agents
        self.agents = {
            "trading": create_trading_agent(config),
            "research": create_research_agent(config, knowledge_base_id="default"),
            "risk": create_risk_agent(config),
            "portfolio": create_portfolio_agent(config),
        }
        
        # Intent-to-agent mapping
        self.intent_mapping = {
            "trade_swap": "trading",
            "trade_perp_open": "trading",
            "lend_supply": "trading",
            "market_info": "research",
            "risk_analysis": "risk",
            "portfolio_view": "portfolio",
            # ... etc
        }
    
    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggested_model: Optional[str] = None,
        suggested_agent: Optional[str] = None,
    ) -> str:
        """Process message through Agno agents."""
        
        # Determine which agent to use
        agent_type = suggested_agent or self._classify_intent(message)
        agent = self.agents.get(agent_type, self.agents["research"])
        
        # Build Agno context
        agno_context = {
            "user_id": str(user_id),
            "session_id": session_id,
        }
        if context:
            agno_context.update(context)
        
        # Run agent (Agno handles tool calls automatically)
        response = await agent.run(message, context=agno_context)
        
        # Agno's built-in telemetry auto-logs to our DB
        # (via custom telemetry adapter we'll build in Week 5)
        
        return response.content
    
    def _classify_intent(self, message: str) -> str:
        """Simple intent classification."""
        # Reuse existing logic from AgentGatewayImpl
        # Or delegate to distillation engine
        pass
```

---

### Week 5-6: Integration & Telemetry

#### 3.1: Agno Telemetry Adapter
**File**: `src/app/infrastructure/adapters/ai/agno_telemetry.py`

```python
"""Agno telemetry adapter for our database."""
from agno.telemetry import TelemetryProvider
from app.domain.ports.ai.agent_execution_repository import AgentExecutionRepository


class AnvilTelemetryProvider(TelemetryProvider):
    """Custom telemetry provider that writes to our DB."""
    
    def __init__(self, execution_repo: AgentExecutionRepository):
        self.execution_repo = execution_repo
    
    async def log_execution(
        self,
        agent_id: str,
        session_id: str,
        message: str,
        response: str,
        model_used: str,
        tokens_used: int,
        latency_ms: int,
        tools_called: List[str],
    ):
        """Log agent execution to our database."""
        await self.execution_repo.create_execution(
            agent_id=agent_id,
            session_id=session_id,
            input_message=message,
            output_message=response,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            tools_called=tools_called,
        )
```

#### 3.2: MCP Server Manager
**File**: `src/app/infrastructure/mcp/manager.py`

```python
"""MCP server manager - starts/stops all MCP servers."""
import asyncio
import uvicorn
from app.infrastructure.mcp.protocols.oneinch_mcp import OneInchMCPServer
from app.infrastructure.mcp.internal.portfolio_mcp import PortfolioMCPServer


class MCPManager:
    """Manages all MCP servers."""
    
    def __init__(self):
        self.servers = []
    
    def register_server(self, server: MCPServer, port: int):
        """Register an MCP server."""
        self.servers.append((server, port))
    
    async def start_all(self):
        """Start all MCP servers."""
        tasks = []
        for server, port in self.servers:
            task = asyncio.create_task(
                uvicorn.Server(
                    config=uvicorn.Config(server.app, host="0.0.0.0", port=port)
                ).serve()
            )
            tasks.append(task)
        await asyncio.gather(*tasks)


# Usage in main.py:
# mcp_manager = MCPManager()
# mcp_manager.register_server(OneInchMCPServer(api_key=...), port=8080)
# mcp_manager.register_server(PortfolioMCPServer(repo=...), port=8081)
# await mcp_manager.start_all()
```

---

### Week 7-8: Testing & Optimization

#### 4.1: Integration Tests
**File**: `tests/integration/test_agno_agents.py`

```python
"""Integration tests for Agno agents."""
import pytest
from app.infrastructure.agents.agno.trading_agent import create_trading_agent


@pytest.mark.asyncio
async def test_trading_agent_swap_quote():
    """Test trading agent can get swap quote."""
    agent = create_trading_agent(config)
    
    response = await agent.run("Get me a quote to swap 1 ETH for USDC")
    
    assert "ETH" in response.content
    assert "USDC" in response.content
    # Agent should have called get_swap_quote tool
    assert len(response.tools_called) > 0
    assert response.tools_called[0]["name"] == "get_swap_quote"


@pytest.mark.asyncio
async def test_research_agent_protocol_info():
    """Test research agent can fetch protocol info."""
    agent = create_research_agent(config, knowledge_base_id="test")
    
    response = await agent.run("What is Aave?")
    
    assert "Aave" in response.content
    assert "lending" in response.content.lower()
    # Agent should have queried knowledge base
    assert response.knowledge_used is True
```

#### 4.2: Performance Benchmarks
**File**: `tests/benchmarks/bench_agno_vs_legacy.py`

```python
"""Benchmark Agno vs legacy agent gateway."""
import time
import asyncio


async def bench_legacy_agent():
    """Benchmark legacy AgentGatewayImpl."""
    from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
    
    gateway = AgentGatewayImpl(...)
    
    start = time.time()
    for _ in range(100):
        await gateway.process_message(user_id, session_id, "What's the price of ETH?")
    elapsed = time.time() - start
    
    return elapsed / 100  # Avg per request


async def bench_agno_agent():
    """Benchmark Agno gateway."""
    from app.infrastructure.adapters.ai.agno_gateway import AgnoGateway
    
    gateway = AgnoGateway(config)
    
    start = time.time()
    for _ in range(100):
        await gateway.process_message(user_id, session_id, "What's the price of ETH?")
    elapsed = time.time() - start
    
    return elapsed / 100


# Expected results:
# Legacy: ~2.5s per request
# Agno: ~0.8s per request (3x faster)
```

---

## 🚀 Deployment Guide

### 1. Docker Compose (MCP Servers)
**File**: `docker-compose.mcp.yml`

```yaml
version: '3.8'

services:
  mcp-1inch:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    command: ["python", "-m", "app.infrastructure.mcp.protocols.oneinch_mcp"]
    ports:
      - "8080:8080"
    environment:
      - ONEINCH_API_KEY=${ONEINCH_API_KEY}
  
  mcp-portfolio:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    command: ["python", "-m", "app.infrastructure.mcp.internal.portfolio_mcp"]
    ports:
      - "8081:8081"
    depends_on:
      - db
  
  mcp-defillama:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    command: ["python", "-m", "app.infrastructure.mcp.protocols.defillama_mcp"]
    ports:
      - "8082:8082"
```

### 2. Kubernetes (Production)
**File**: `k8s/mcp-servers.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-1inch
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-1inch
  template:
    metadata:
      labels:
        app: mcp-1inch
    spec:
      containers:
      - name: mcp-1inch
        image: anvil/mcp-1inch:latest
        ports:
        - containerPort: 8080
        env:
        - name: ONEINCH_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: oneinch-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-1inch
spec:
  selector:
    app: mcp-1inch
  ports:
  - port: 8080
    targetPort: 8080
```

---

## 📊 Success Metrics

### Week 2 Checkpoint
- ✅ 3 MCP servers implemented (1inch, Portfolio, DeFiLlama)
- ✅ All tools tested in isolation

### Week 4 Checkpoint
- ✅ 4 Agno agents implemented (Trading, Research, Risk, Portfolio)
- ✅ Agents can call MCP tools successfully

### Week 6 Checkpoint
- ✅ Telemetry integrated with database
- ✅ MCP manager running all servers

### Week 8 Final
- ✅ **Performance**: 80ms avg agent instantiation (vs. 400ms legacy)
- ✅ **Scale**: 10K concurrent users supported
- ✅ **DX**: 3 new protocol integrations added (via MCP)
- ✅ **Cost**: 20% reduction in LLM costs (faster, more efficient agents)

---

## 🎯 Next Steps (Post-Phase 2)

After completing Agno + MCP:

1. **Phase 1: Agent Squad** - Use Agno agents in Agent Squad orchestrator
2. **Phase 4: Recommenders** - Add recommendation MCP tools
3. **Phase 3: GraphRAG** - Add graph query MCP tools

**Foundation Complete**: With Agno + MCP, you now have:
- 🛠️ **Pluggable tool ecosystem** (easy to extend)
- ⚡ **High-performance runtime** (10K users)
- 📊 **Built-in observability** (telemetry auto-logged)
- 🚀 **80% faster agent development** (DX win)

---

**Status**: Ready to start Week 1! 🚀  
**Questions?**: Review STRATEGIC_PLAN.md for full context
