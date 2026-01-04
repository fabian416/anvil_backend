# Agent Router - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El Agent Router proporciona enrutamiento inteligente de consultas a agentes especializados DeFi:

1. **5 Specialized Agents**: Trading, Lending, Perpetual, Analytics, Portfolio
2. **MCP Integration**: Conexión con 11+ servidores MCP para herramientas DeFi
3. **Keyword-Based Classification**: Enrutamiento rápido sin llamadas LLM
4. **Feature Flags**: Control granular de activación/desactivación
5. **Fallback System**: Routing resiliente cuando agentes no están disponibles
6. **Agno Runtime**: Framework de agentes con sesiones, streaming y memoria

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT ROUTER ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   User Query    │
                                    │ "Swap 1 ETH..."│
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │      Agent Router        │
                              │  (Keyword Classification)│
                              └──────────┬───────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
     ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
     │ Trading Agent  │         │ Lending Agent  │         │Perpetual Agent │
     │  (1inch/Curve) │         │ (Aave/Morpho)  │         │  (Hyperliquid) │
     └───────┬────────┘         └───────┬────────┘         └───────┬────────┘
             │                          │                          │
             ▼                          ▼                          ▼
     ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
     │   MCP Tools    │         │   MCP Tools    │         │   MCP Tools    │
     │  get_swap_quote│         │ get_market_data│         │ get_funding_rate│
     │  get_token_price│         │ get_positions │         │ get_positions  │
     └────────────────┘         └────────────────┘         └────────────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────────┐
                              │     MCP Server Manager   │
                              │   (Port 8080 - Gateway)  │
                              └──────────┬───────────────┘
                                         │
      ┌──────────┬───────────┬───────────┼───────────┬──────────┬──────────┐
      ▼          ▼           ▼           ▼           ▼          ▼          ▼
  ┌──────┐  ┌──────┐   ┌──────────┐  ┌──────┐  ┌──────────┐  ┌──────┐  ┌──────┐
  │1inch │  │Aave  │   │Hyperliquid│  │Morpho│  │DeFiLlama │  │Curve │  │ ...  │
  │:8081 │  │:8085 │   │  :8090   │  │:8088 │  │  :8083   │  │:8089 │  │      │
  └──────┘  └──────┘   └──────────┘  └──────┘  └──────────┘  └──────┘  └──────┘
```

---

## Agent Router

### Core Implementation

**Location**: `src/app/infrastructure/agno/agent_router.py`

```python
class AgentRouter:
    """
    Intelligent router for specialized DeFi agents.
    
    Routing Logic:
    - Trading queries → TradingAgent (1inch, Curve)
    - Lending queries → LendingAgent (Aave, Morpho)
    - Perpetual queries → PerpetualAgent (Hyperliquid)
    - Analytics queries → AnalyticsAgent (DeFiLlama)
    - Portfolio queries → PortfolioAgent
    - Multi-domain queries → Orchestrates multiple agents
    """
    
    def __init__(
        self,
        config: AgnoConfig,
        settings: Optional[AgnoSettings] = None,
        debug_mode: bool = False,
    ): ...
    
    def classify_intent(self, query: str) -> tuple[AgentType, float]:
        """
        Classify user intent based on query keywords.
        Returns (agent_type, confidence_score)
        """
        ...
    
    async def route(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        stream: bool = False,
    ):
        """Route query to appropriate agent(s)."""
        ...
    
    def get_agent_info(self) -> dict[str, Any]:
        """Get information about all available agents."""
        ...
```

### Intent Keywords

El router utiliza keywords para clasificación rápida sin LLM:

```python
intent_keywords = {
    AgentType.TRADING: [
        "swap", "trade", "exchange", "buy", "sell",
        "price", "quote", "route", "dex", "1inch",
        "liquidity source", "gas cost", "slippage",
        "curve", "pool", "liquidity provider",
    ],
    AgentType.LENDING: [
        "lend", "borrow", "supply", "withdraw", "repay",
        "collateral", "health factor", "liquidation",
        "aave", "compound", "interest rate", "apy",
        "loan", "debt", "ltv", "morpho", "vault",
    ],
    AgentType.PERPETUAL: [
        "perpetual", "perp", "futures", "leverage",
        "long", "short", "funding rate", "funding",
        "hyperliquid", "margin", "liquidation price",
        "position", "orderbook", "10x", "5x", "3x",
    ],
    AgentType.ANALYTICS: [
        "tvl", "protocol", "yield", "apy", "farm",
        "compare", "analysis", "trending", "growth",
        "defillama", "fees", "revenue", "stablecoin",
    ],
    AgentType.PORTFOLIO: [
        "balance", "portfolio", "positions", "holdings",
        "wallet", "assets", "total value", "net worth",
        "my", "show me", "track", "monitor",
    ],
}
```

---

## Specialized Agents

### 1. Trading Agent

**Location**: `src/app/infrastructure/agno/trading_agent.py`

| Feature | Description |
|---------|-------------|
| **Purpose** | DEX swaps, price quotes, route comparison |
| **MCP Servers** | 1inch, Curve |
| **Capabilities** | Swap quotes, price checking, route analysis, LP pools |

```python
class TradingAgent(DeFiAgentBase):
    """
    Trading specialist using 1inch aggregator and Curve Finance.
    
    Capabilities:
    - Get swap quotes across 100+ DEXes (1inch)
    - Compare token prices
    - Analyze swap routes
    - Discover Curve liquidity pools
    - Check pool APYs
    - Estimate gas costs
    """
    
    def __init__(self, config: AgnoConfig, debug_mode: bool = False):
        super().__init__(
            name="Trading Agent",
            role="DeFi trading and liquidity specialist",
            config=config,
            mcp_servers=["1inch", "curve"],
            instructions=[
                "You specialize in DeFi token trading and swaps.",
                "Use 1inch for general swaps, Curve for stablecoins.",
                "ALWAYS get quote before suggesting trade.",
                "Warn about high price impact (>1%).",
                # ... more instructions
            ],
        )
    
    async def get_swap_quote(self, chain_id, from_token, to_token, amount, slippage): ...
    async def get_token_price(self, chain_id, token_address): ...
    async def compare_routes(self, chain_id, from_token, to_token, amount): ...
```

**Key Instructions**:
- Prefer Curve for stablecoin swaps (lower slippage)
- Always show full details: amounts, gas, price impact
- Never execute without user confirmation
- Suggest splitting large trades to reduce impact

### 2. Lending Agent

**Location**: `src/app/infrastructure/agno/lending_agent.py`

| Feature | Description |
|---------|-------------|
| **Purpose** | Lending, borrowing, health factor monitoring |
| **MCP Servers** | Aave, Morpho |
| **Capabilities** | Market rates, positions, risk analysis, yield comparison |

```python
class LendingAgent(DeFiAgentBase):
    """
    Lending specialist using Aave V3 and Morpho Protocol.
    
    Capabilities:
    - Check lending/borrowing rates
    - Compare yields across protocols
    - Manage supply/borrow positions
    - Monitor health factors
    - Analyze liquidation risks
    - Discover MetaMorpho vaults
    """
    
    def __init__(self, config: AgnoConfig, debug_mode: bool = False):
        super().__init__(
            name="Lending Agent",
            role="DeFi lending and borrowing specialist",
            config=config,
            mcp_servers=["aave", "morpho"],
            instructions=[
                "ALWAYS check health factor before suggesting borrows.",
                "Health factor below 1.0 = liquidation risk!",
                "Recommend maintaining HF above 1.5 (2.0+ ideal).",
                # ... more instructions
            ],
        )
    
    async def get_market_rates(self, chain_id, assets): ...
    async def check_health_factor(self, chain_id, user_address): ...
    async def calculate_borrow_capacity(self, chain_id, user_address, asset, target_hf): ...
    async def analyze_liquidation_risk(self, chain_id, user_address): ...
```

**Risk Tiers (Morpho)**:
- `LOW`: Blue-chip assets, conservative LTVs
- `MEDIUM`: Balanced risk/reward
- `HIGH`: Higher yields, more risk
- `VERY_HIGH`: Maximum yields, experienced users only

### 3. Perpetual Agent

**Location**: `src/app/infrastructure/agno/perpetual_agent.py`

| Feature | Description |
|---------|-------------|
| **Purpose** | Perpetual futures, leverage, funding rates |
| **MCP Servers** | Hyperliquid |
| **Capabilities** | Market analysis, liquidation calc, funding arbitrage |

```python
class PerpetualAgent(DeFiAgentBase):
    """
    Perpetual futures specialist using Hyperliquid DEX.
    
    Capabilities:
    - Discover perpetual markets
    - Analyze funding rates
    - Calculate liquidation prices
    - Monitor open positions
    - Track recent liquidations
    - Find funding arbitrage
    """
    
    def __init__(self, config: AgnoConfig, debug_mode: bool = False):
        super().__init__(
            name="Perpetual Agent",
            role="Perpetual futures trading specialist",
            config=config,
            mcp_servers=["hyperliquid"],
            instructions=[
                "ALWAYS calculate liquidation price before suggesting leveraged position.",
                "NEVER recommend >5x leverage without explicit risk warnings.",
                "At 10x leverage, 10% move against you = liquidation.",
                # ... more instructions
            ],
        )
    
    async def get_funding_rate(self, symbol): ...
    async def calculate_liquidation_price(self, entry_price, leverage, side): ...
    async def analyze_position_risk(self, entry_price, size, leverage, side, symbol): ...
    async def find_funding_arbitrage(self, min_rate): ...
```

**Leverage Risk Education**:
- 10x leverage: 10% adverse move = liquidation
- 5x leverage: 20% adverse move = liquidation
- Recommended: 2-3x for beginners, max 5x for most users

### 4. Analytics Agent

**Location**: `src/app/infrastructure/agno/analytics_agent.py`

| Feature | Description |
|---------|-------------|
| **Purpose** | Protocol research, yield discovery, market trends |
| **MCP Servers** | DeFiLlama |
| **Capabilities** | TVL tracking, yield farming, protocol comparison |

```python
class AnalyticsAgent(DeFiAgentBase):
    """
    Analytics specialist using DeFiLlama data.
    
    Capabilities:
    - Protocol TVL and growth tracking
    - Yield farming opportunity discovery
    - Protocol fee and revenue analysis
    - Stablecoin market analysis
    - Protocol comparison
    - Trending protocols identification
    """
    
    def __init__(self, config: AgnoConfig, debug_mode: bool = False):
        super().__init__(
            name="Analytics Agent",
            role="DeFi protocol analyst and researcher",
            config=config,
            mcp_servers=["defillama"],
            instructions=[
                "Always provide context with numbers.",
                "For yields, mention associated risks.",
                "High APY often means higher risk.",
                # ... more instructions
            ],
        )
    
    async def get_protocol_analysis(self, protocol): ...
    async def find_yields(self, chain, stablecoin_only, min_tvl, min_apy): ...
    async def compare_protocols(self, protocols: list): ...
    async def get_trending(self, timeframe, limit): ...
```

### 5. Portfolio Agent

**Location**: `src/app/infrastructure/agno/portfolio_agent.py`

| Feature | Description |
|---------|-------------|
| **Purpose** | Portfolio tracking, balance monitoring |
| **MCP Servers** | Portfolio |
| **Capabilities** | Multi-chain balances, DeFi positions, diversification |

```python
class PortfolioAgent(DeFiAgentBase):
    """
    Portfolio management specialist.
    
    Capabilities:
    - Track token balances across chains
    - Monitor DeFi positions (lending, LP, staking)
    - Generate portfolio summaries with USD valuation
    - Multi-chain portfolio aggregation
    """
    
    def __init__(self, config: AgnoConfig, debug_mode: bool = False):
        super().__init__(
            name="Portfolio Agent",
            role="Portfolio management and tracking specialist",
            config=config,
            mcp_servers=["portfolio"],
            instructions=[
                "Always show balances with USD values.",
                "Group by type: tokens, lending, LP, staking.",
                "Highlight concentration risk (>50% single asset).",
                # ... more instructions
            ],
        )
    
    async def get_balances(self, user_id, chain_id): ...
    async def get_positions(self, user_id): ...
    async def get_portfolio_summary(self, user_id): ...
    async def analyze_diversification(self, user_id): ...
```

---

## Base Agent Architecture

### DeFiAgentBase

**Location**: `src/app/infrastructure/agno/base_agent.py`

Clase base para todos los agentes DeFi con integración MCP.

```python
class DeFiAgentBase:
    """
    Base class for all DeFi Agno agents.
    
    Provides:
    - MCP tool integration (auto-discovery from servers)
    - Session management (persistent conversations)
    - Streaming support
    - Error handling with retry
    
    Architecture:
    - Agno Agent as runtime engine
    - MCP servers for tool discovery
    - Async tool loading
    - Type-safe tool registration
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        config: AgnoConfig,
        mcp_servers: list[str] = None,
        mcp_manager_url: str = "http://localhost:8080",
        instructions: list[str] = None,
        debug_mode: bool = False,
    ): ...
    
    async def load_mcp_tools(self):
        """
        Load tools from MCP servers.
        Discovers tools via MCP manager and registers with Agno agent.
        """
        ...
    
    async def run(
        self,
        message: str,
        user_id: str = None,
        session_id: str = None,
        stream: bool = False,
    ) -> RunOutput:
        """Run agent with message."""
        ...
    
    async def run_stream(
        self,
        message: str,
        user_id: str = None,
        session_id: str = None,
    ) -> AsyncIterator[RunEvent]:
        """Run agent with streaming response."""
        ...
    
    def get_available_tools(self) -> list[dict]:
        """Get list of available MCP tools."""
        ...
```

### MCP Tool Integration

```python
@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool loaded from server."""
    server: str          # e.g., "1inch"
    name: str            # e.g., "get_swap_quote"
    qualified_name: str  # e.g., "1inch_get_swap_quote"
    description: str
    parameters: dict     # JSON Schema
    server_url: str

def _create_agno_function(self, tool_def: MCPToolDefinition) -> Function:
    """Create Agno Function from MCP tool with retry logic."""
    
    async def mcp_tool_handler(**kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_manager_url}/tools/{tool_def.name}",
                json={"parameters": kwargs},
                timeout=30.0,
            )
            return response.json()
    
    return Function(
        name=tool_def.qualified_name,
        description=tool_def.description,
        parameters=tool_def.parameters,
        entrypoint=mcp_tool_handler,
    )
```

---

## MCP Server Integration

### Available MCP Servers (11)

| Server | Port | Purpose |
|--------|------|---------|
| **1inch** | 8081 | DEX aggregator, swap quotes |
| **Portfolio** | 8082 | Balance tracking |
| **DeFiLlama** | 8083 | Protocol analytics |
| **CoinGecko** | 8084 | Price data |
| **Aave** | 8085 | Lending protocol |
| **The Graph** | 8086 | Subgraph queries |
| **Morpho** | 8088 | Yield optimization |
| **Curve** | 8089 | Stablecoin DEX |
| **Hyperliquid** | 8090 | Perpetual futures |
| **LayerZero** | 8091 | Cross-chain messaging |
| **Perplexity** | 8087 | Research AI |

### MCP Server Manager

**Location**: `src/app/infrastructure/mcp/manager.py`

```python
class MCPServerManager:
    """
    Central manager for all MCP servers.
    
    Responsibilities:
    - Register and manage multiple servers
    - Start/stop servers on different ports
    - Provide unified tool discovery
    - Route tool calls to appropriate servers
    - Monitor server health
    """
    
    def register_server(self, server: MCPServer, port: int): ...
    async def start_all(self): ...
    async def get_all_tools(self) -> list[MCPToolDescription]: ...
    async def call_tool(self, tool_name: str, params: dict) -> dict: ...
```

---

## Configuration

### AgnoConfig

**Location**: `src/app/setup/config/agno.py`

```python
class AgnoConfig(BaseModel):
    """Agno configuration."""
    
    default_model: str = "gpt-4-turbo"
    fallback_model: str = "gpt-3.5-turbo"
    intent_threshold: float = 0.75
    session_timeout: int = 3600       # 1 hour
    max_context_messages: int = 20
    enable_intent_classification: bool = True
    enable_context_memory: bool = True
    enable_multi_agent_routing: bool = True
    debug_mode: bool = False
    
    retry: AgnoRetryConfig
```

### AgnoSettings (Feature Flags)

```python
class AgnoAgentSettings(BaseModel):
    """Settings for individual Agno agents."""
    
    trading_enabled: bool = True   # 1inch, Curve
    lending_enabled: bool = True   # Aave, Morpho
    perpetual_enabled: bool = True # Hyperliquid
    portfolio_enabled: bool = True # Portfolio tracking
    analytics_enabled: bool = True # DeFiLlama


class AgnoSettings(BaseModel):
    """Agno agent system configuration."""
    
    enabled: bool = True                   # Master switch
    intent_classification_enabled: bool = True
    fallback_to_general: bool = True       # Fallback if agent disabled
    agents: AgnoAgentSettings
```

### Retry Configuration

```python
class AgnoRetryConfig(BaseModel):
    """Retry configuration for MCP tool calls."""
    
    enabled: bool = True
    max_attempts: int = 2           # Fast feedback priority
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 5.0
    exponential_base: float = 2.0
    circuit_breaker_enabled: bool = True
    telemetry_enabled: bool = True
```

---

## Dependency Injection

### AgnoProvider

**Location**: `src/app/setup/ioc/agno.py`

```python
class AgnoProvider(Provider):
    """Provider for Agno agents."""
    
    @provide(scope=Scope.APP)
    def get_agno_config(self) -> AgnoConfig:
        return AgnoConfig(
            model_id="gpt-4-turbo",
            temperature=0.7,
            max_tokens=2000,
            show_tool_calls=True,
            mcp_manager_url="http://localhost:8080",
        )
    
    @provide(scope=Scope.APP)
    async def get_agent_router(self, config: AgnoConfig) -> AgentRouter:
        router = AgentRouter(config, debug_mode=True)
        await router.initialize()
        return router
```

---

## Routing Flow

### Classification Process

```
1. User Query: "Swap 1 ETH for USDC"
                  │
2. Keyword Scan: │
   - "swap" matches TRADING keywords
   - Score: 1 keyword hit
                  │
3. Confidence:   │
   - 1 match / 3 (threshold) = 0.33
   - Below 1.0 confidence
                  │
4. Best Match:   │
   - TRADING: score 1
   - Others: score 0
                  │
5. Route:        │
   └───────────────▶ TradingAgent
```

### Multi-Domain Detection

```python
# Check for multi-agent need
high_scores = [agent for agent, score in scores.items() if score >= 2]
if len(high_scores) > 1:
    return AgentType.MULTI, 0.8
```

### Fallback Behavior

```python
if agent_type not in self.agents:
    if self.settings.fallback_to_general:
        # Try analytics first, then any available
        if AgentType.ANALYTICS in self.agents:
            agent_type = AgentType.ANALYTICS
        elif self.agents:
            agent_type = next(iter(self.agents.keys()))
        else:
            raise AgentDisabledError("All agents disabled")
```

---

## Usage Examples

### Basic Routing

```python
# Create router
config = AgnoConfig(model_id="gpt-4-turbo")
router = AgentRouter(config, debug_mode=True)
await router.initialize()

# Route query
result = await router.route("Swap 1 ETH for USDC on Ethereum")
print(result.content)
```

### With Session Persistence

```python
# First message
result1 = await router.route(
    "What's the current ETH price?",
    user_id="user123",
    session_id="session456",
)

# Follow-up (same session = context preserved)
result2 = await router.route(
    "How about swapping some for USDC?",
    user_id="user123",
    session_id="session456",
)
```

### Streaming Response

```python
async for event in router.agents[AgentType.TRADING].run_stream(
    "Compare swap routes for ETH to DAI",
    user_id="user123",
):
    print(event.content, end="", flush=True)
```

### Check Agent Status

```python
info = router.get_agent_info()
# {
#     "router_status": "initialized",
#     "agents_count": 5,
#     "agents": {
#         "trading": {"name": "Trading Agent", "tools_count": 15},
#         "lending": {"name": "Lending Agent", "tools_count": 12},
#         ...
#     }
# }
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Agent Router** | `infrastructure/agno/agent_router.py` | Intelligent query routing |
| **Base Agent** | `infrastructure/agno/base_agent.py` | DeFi agent base class |
| **Trading Agent** | `infrastructure/agno/trading_agent.py` | DEX swaps (1inch/Curve) |
| **Lending Agent** | `infrastructure/agno/lending_agent.py` | Lending (Aave/Morpho) |
| **Perpetual Agent** | `infrastructure/agno/perpetual_agent.py` | Futures (Hyperliquid) |
| **Analytics Agent** | `infrastructure/agno/analytics_agent.py` | Research (DeFiLlama) |
| **Portfolio Agent** | `infrastructure/agno/portfolio_agent.py` | Portfolio tracking |
| **MCP Manager** | `infrastructure/mcp/manager.py` | MCP server orchestration |
| **Configuration** | `setup/config/agno.py` | Agno config & feature flags |
| **IoC Provider** | `setup/ioc/agno.py` | Dependency injection |

---

## Starting Agents

### Development

```bash
# Start all MCP servers
make mcp.all

# Individual servers
make mcp.oneinch    # Port 8081
make mcp.aave       # Port 8085
make mcp.morpho     # Port 8088
make mcp.curve      # Port 8089
make mcp.defillama  # Port 8083
make mcp.hyperliquid # Port 8090
make mcp.portfolio  # Port 8082
```

### Feature Flags (TOML)

```toml
[agno]
enabled = true
intent_classification_enabled = true
fallback_to_general = true

[agno.agents]
trading_enabled = true
lending_enabled = true
perpetual_enabled = true
portfolio_enabled = true
analytics_enabled = true

[agno.retry]
enabled = true
max_attempts = 2
circuit_breaker_enabled = true
```

---

## Agent Instructions Best Practices

### Safety Guidelines

1. **Trading Agent**: Never execute without confirmation
2. **Lending Agent**: Always check health factor first
3. **Perpetual Agent**: Calculate liquidation before suggesting leverage
4. **Analytics Agent**: High APY = high risk warning
5. **Portfolio Agent**: Highlight concentration risk

### Protocol Preferences

| Query Type | Preferred Protocol |
|------------|-------------------|
| Stablecoin swaps | Curve (lower slippage) |
| General token swaps | 1inch (best aggregation) |
| Conservative lending | Aave V3 (established) |
| Yield optimization | Morpho (capital efficiency) |
| Leverage trading | Hyperliquid (decentralized) |

---

## Error Handling

### MCP Tool Retry

```python
# Built-in retry with exponential backoff
self._mcp_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
```

### Agent Disabled

```python
class AgentDisabledError(Exception):
    """Raised when attempting to use a disabled agent."""
    pass

# In router
if agent_type not in self.agents:
    raise AgentDisabledError(
        f"{agent_type.value} agent is disabled. "
        f"Enable with agno.agents.{agent_type.value}_enabled=true"
    )
```

---

## Security Considerations

### 1. Tool Execution Safety

All agents require explicit user confirmation before executing transactions.

### 2. Risk Warnings

Agents provide risk education (leverage, liquidation, impermanent loss).

### 3. Privacy

Portfolio agent never logs addresses or balances.

### 4. Feature Flags

Granular control over which agents are active in production.

---

**Last Updated**: January 2, 2026
