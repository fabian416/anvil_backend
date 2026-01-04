# Feature Flags - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Feature Flags proporciona control granular sobre funcionalidades:

1. **Telemetry Feature Flags**: Control de observabilidad (API, LLM, DB, Tracing)
2. **Agent Feature Flags**: Control de 18 agentes de IA especializados
3. **Agno Agent Feature Flags**: Control de 5 agentes DeFi routing
4. **External API Feature Flags**: Control de 15+ integraciones externas
5. **Integration Feature Flags**: Control de chat y proyectos
6. **Runtime Toggle**: Cambios en tiempo real via API y Redis
7. **Subscription Tier Filtering**: Agentes por tier (Free, Pro, Enterprise)
8. **Sampling Rates**: Control de volumen de telemetría

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           FEATURE FLAGS ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │            Configuration Sources         │
                    │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
                    │  │   ENV    │  │   TOML   │  │ Redis  │ │
                    │  │ Variables│  │  Config  │  │ Runtime│ │
                    │  └────┬─────┘  └────┬─────┘  └───┬────┘ │
                    └───────┼─────────────┼────────────┼──────┘
                            │             │            │
         ┌──────────────────┼─────────────┼────────────┼───────────────────┐
         │                  │             │            │                   │
         ▼                  ▼             ▼            ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Telemetry     │ │  Agent Squad    │ │    Agno         │ │  Integration    │
│  Feature Flags  │ │  Feature Flags  │ │  Feature Flags  │ │  Feature Flags  │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│• global_enabled │ │• 18 agents      │ │• 5 DeFi agents  │ │• chat tools     │
│• api_telemetry  │ │• per-agent cfg  │ │• intent routing │ │• project scopes │
│• llm_telemetry  │ │• subscription   │ │• fallback mode  │ │• risk validation│
│• db_telemetry   │ │• capabilities   │ │• retry config   │ │• permissions    │
│• tracing        │ │                 │ │                 │ │                 │
│• sampling rates │ │                 │ │                 │ │                 │
│• per-API flags  │ │                 │ │                 │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │                   │
         └───────────────────┴───────────────────┴───────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │    Admin API / DI      │
                          │ Runtime Toggle Support │
                          └────────────────────────┘
```

---

## 1. Telemetry Feature Flags

### TelemetryFeatureFlags

**Location**: `src/app/infrastructure/telemetry/feature_flags.py`

Control granular de todos los componentes de telemetría.

```python
@dataclass
class TelemetryFeatureFlags:
    """Granular feature flags for telemetry components."""
    
    # =========================================================================
    # MASTER SWITCH
    # =========================================================================
    global_enabled: bool = True
    
    # =========================================================================
    # COMPONENT-LEVEL FLAGS
    # =========================================================================
    api_telemetry_enabled: bool = True     # External API tracking
    llm_telemetry_enabled: bool = True     # LLM provider tracking
    db_telemetry_enabled: bool = True      # Database query tracking
    tracing_enabled: bool = True           # Distributed tracing
    metrics_export_enabled: bool = True    # Prometheus export
    endpoint_telemetry_enabled: bool = True # HTTP endpoint tracking
    admin_telemetry_enabled: bool = True   # Admin route tracking
    
    # =========================================================================
    # PER-API GRANULAR CONTROL
    # =========================================================================
    enabled_apis: Set[str] = field(default_factory=set)   # Empty = all enabled
    disabled_apis: Set[str] = field(default_factory=set)  # Explicit disable
    
    # =========================================================================
    # PER-LLM PROVIDER CONTROL
    # =========================================================================
    enabled_llm_providers: Set[str] = field(default_factory=set)   # Empty = all
    disabled_llm_providers: Set[str] = field(default_factory=set)  # Explicit disable
    
    # =========================================================================
    # DATABASE TELEMETRY SUB-FLAGS
    # =========================================================================
    db_slow_query_logging: bool = True
    db_query_patterns: bool = True
    db_connection_pool: bool = True
    
    # =========================================================================
    # SAMPLING RATES (0.0 - 1.0)
    # =========================================================================
    api_sample_rate: float = 1.0
    llm_sample_rate: float = 1.0
    db_sample_rate: float = 1.0
    trace_sample_rate: float = 1.0
    
    # =========================================================================
    # PER-ENDPOINT CONTROL
    # =========================================================================
    disabled_endpoints: Set[str] = field(default_factory=set)
    enabled_endpoint_prefixes: Set[str] = field(default_factory=set)
    disabled_endpoint_prefixes: Set[str] = field(default_factory=set)
```

### Check Methods

```python
# Master switches
flags.is_enabled() -> bool
flags.is_api_telemetry_enabled() -> bool
flags.is_llm_telemetry_enabled() -> bool
flags.is_db_telemetry_enabled() -> bool
flags.is_tracing_enabled() -> bool

# Per-component checks
flags.is_api_enabled("coingecko") -> bool
flags.is_llm_provider_enabled("vertex_ai") -> bool
flags.is_endpoint_enabled("/api/v1/user/chat") -> bool
flags.is_admin_endpoint("/api/v1/admin/users") -> bool

# Sampling decisions
flags.should_sample_api("coingecko") -> bool
flags.should_sample_llm("openai") -> bool
flags.should_sample_db() -> bool
flags.should_sample_trace() -> bool
```

### Environment Variables

```bash
# Master switch
TELEMETRY_ENABLED=true

# Component flags
TELEMETRY_API_ENABLED=true
TELEMETRY_LLM_ENABLED=true
TELEMETRY_DB_ENABLED=true
TELEMETRY_TRACING_ENABLED=true
TELEMETRY_METRICS_ENABLED=true

# Per-API config (comma-separated)
TELEMETRY_ENABLED_APIS=coingecko,defillama
TELEMETRY_DISABLED_APIS=uniswap

# Per-LLM provider config
TELEMETRY_ENABLED_LLM_PROVIDERS=vertex_ai,openai
TELEMETRY_DISABLED_LLM_PROVIDERS=anthropic

# Sampling rates (0.0-1.0)
TELEMETRY_API_SAMPLE_RATE=1.0
TELEMETRY_LLM_SAMPLE_RATE=1.0
TELEMETRY_DB_SAMPLE_RATE=0.5
TELEMETRY_TRACE_SAMPLE_RATE=0.1

# Database sub-flags
TELEMETRY_DB_SLOW_QUERY_LOGGING=true
TELEMETRY_DB_QUERY_PATTERNS=true
TELEMETRY_DB_CONNECTION_POOL=true

# Endpoint config
TELEMETRY_ENDPOINT_ENABLED=true
TELEMETRY_ADMIN_ENABLED=true
TELEMETRY_DISABLED_ENDPOINTS=/api/v1/health
TELEMETRY_DISABLED_ENDPOINT_PREFIXES=/api/v1/internal
```

### Redis Persistence

```python
# Save flags to Redis (persists across restarts)
await save_flags_to_redis(flags, redis_client)

# Load flags from Redis
flags = await load_flags_from_redis(redis_client)

# Delete saved flags (fallback to env)
await delete_flags_from_redis(redis_client)

# Initialize with Redis priority
flags = await initialize_feature_flags(redis_client)
# Priority: 1. Redis → 2. Environment → 3. Defaults
```

---

## 2. Agent Squad Feature Flags

### AgentSquadSettings

**Location**: `src/app/setup/config/agent_squad.py`

Control de los 18 agentes especializados.

```python
class AgentSquadSettings(BaseModel):
    """Agent Squad configuration from TOML."""
    
    # =========================================================================
    # MASTER TOGGLE
    # =========================================================================
    enabled: bool = True
    
    # =========================================================================
    # INTENT CLASSIFICATION
    # =========================================================================
    enable_intent_classification: bool = True
    log_intent_classification: bool = False
    log_agent_selection: bool = False
    intent_classification_model: str = "gpt-4o-mini"
    intent_confidence_threshold: float = 0.85
    fallback_agent: str = "chat"
    max_context_messages: int = 10
    
    # =========================================================================
    # SUPERVISOR COORDINATION
    # =========================================================================
    enable_supervisor: bool = True
    supervisor_model: str = "gpt-4o"
    supervisor_max_agents: int = 5
    supervisor_timeout_seconds: int = 120
    
    # =========================================================================
    # PERFORMANCE LIMITS
    # =========================================================================
    max_concurrent_agents: int = 3
    routing_timeout_seconds: int = 5
    execution_timeout_seconds: int = 60
    
    # =========================================================================
    # TELEMETRY
    # =========================================================================
    telemetry_enabled: bool = True
    telemetry_sample_rate: float = 1.0
    
    # =========================================================================
    # EXTERNAL API FLAGS (see section below)
    # =========================================================================
    external_apis: ExternalAPIsConfig
    
    # =========================================================================
    # PER-AGENT CONFIGURATION (18 agents)
    # =========================================================================
    agents: AgentSquadAgentsConfig
```

### Per-Agent Configuration

```python
class AgentConfigModel(BaseModel):
    """Individual agent configuration."""
    enabled: bool = True
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000

class AgentSquadAgentsConfig(BaseModel):
    """All 18 agent configurations."""
    
    # Core user-facing agents (10)
    chat: AgentConfigModel            # General chat
    hunter_ai: AgentConfigModel       # Market predictions
    research: AgentConfigModel        # Protocol research
    execution: AgentConfigModel       # Transaction execution
    risk_analyzer: AgentConfigModel   # Risk analysis
    portfolio: AgentConfigModel       # Portfolio management
    tax_optimizer: AgentConfigModel   # Tax optimization
    defi_yield: AgentConfigModel      # Yield farming
    security_auditor: AgentConfigModel # Smart contract auditing
    gas_optimizer: AgentConfigModel   # Gas optimization

    # Enterprise agents (4)
    compliance_monitor: AgentConfigModel  # AML/KYC
    multisig_coordinator: AgentConfigModel # Multi-sig management
    alert_monitoring: AgentConfigModel     # Real-time alerts
    crisis_manager: AgentConfigModel       # Emergency response

    # Advanced agents (4)
    bridge_crosschain: AgentConfigModel    # Cross-chain bridging
    lending_borrowing: AgentConfigModel    # Lending protocols
    nft_asset_manager: AgentConfigModel    # NFT management
    dao_governance: AgentConfigModel       # DAO voting
```

### AgentSquadConfig Value Object

**Location**: `src/app/domain/value_objects/agent_squad/agent_squad_config.py`

```python
@dataclass(frozen=True)
class AgentSquadConfig:
    """Domain value object for agent configuration."""
    
    enabled: bool
    intent_classification_model: str
    intent_confidence_threshold: float
    fallback_agent: AgentType
    enable_supervisor: bool
    supervisor_model: str
    # ... other fields
    
    agents: dict[AgentType, AgentConfig]
    
    def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for specific agent."""
        ...
    
    def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if specific agent is enabled."""
        if not self.enabled:
            return False
        return self.get_agent_config(agent_type).is_enabled
    
    @property
    def enabled_agents(self) -> list[AgentType]:
        """Get list of enabled agents."""
        ...
    
    @property
    def enabled_core_agents(self) -> list[AgentType]:
        """Get enabled core user-facing agents."""
        ...
    
    @property
    def enabled_enterprise_agents(self) -> list[AgentType]:
        """Get enabled enterprise agents."""
        ...
```

### FeatureFlagsGateway Port

**Location**: `src/app/domain/ports/agent_squad/feature_flags_gateway.py`

```python
class FeatureFlagsGateway(Protocol):
    """Port for feature flag access."""
    
    async def is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if agent is enabled."""
        ...
    
    async def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """Get configuration for specific agent."""
        ...
    
    async def get_enabled_agents(self) -> list[AgentType]:
        """Get list of all enabled agents."""
        ...
```

### FeatureFlagsConfig Adapter

**Location**: `src/app/infrastructure/adapters/agent_squad/feature_flags_config.py`

```python
class FeatureFlagsConfig:
    """Adapter implementing FeatureFlagsGateway from TOML config."""
    
    def __init__(self, config: AgentSquadConfig):
        self._config = config
    
    async def is_agent_enabled(self, agent_type: AgentType) -> bool:
        return self._config.is_agent_enabled(agent_type)
    
    async def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        return self._config.get_agent_config(agent_type)
    
    async def get_enabled_agents(self) -> list[AgentType]:
        return self._config.enabled_agents
```

---

## 3. Subscription Tier Filtering

### GetEnabledAgents Query

**Location**: `src/app/application/agent_squad/queries/get_enabled_agents.py`

Filtra agentes por tier de suscripción.

```python
class GetEnabledAgents:
    """Query for retrieving enabled agents by subscription tier."""
    
    async def execute(
        self,
        user_subscription_tier: str | None = None,
    ) -> dict:
        """
        Get enabled agents for user's subscription tier.
        
        Tiers:
        - Free: 5 agents (chat, hunter_ai, research, portfolio, gas_optimizer)
        - Pro: 10 agents (Free + execution, risk_analyzer, tax_optimizer, 
                         defi_yield, security_auditor)
        - Enterprise: All 18 agents
        """
        ...
```

### Tier Configuration

| Tier | Agents | Count |
|------|--------|-------|
| **Free** | chat, hunter_ai, research, portfolio, gas_optimizer | 5 |
| **Pro** | Free + execution, risk_analyzer, tax_optimizer, defi_yield, security_auditor | 10 |
| **Enterprise** | All agents including compliance_monitor, multisig_coordinator, alert_monitoring, crisis_manager, bridge_crosschain, lending_borrowing, nft_asset_manager, dao_governance | 18 |

---

## 4. External API Feature Flags

### ExternalAPIsConfig

**Location**: `src/app/setup/config/agent_squad.py`

Control de integraciones con APIs externas.

```python
class ExternalAPIsConfig(BaseModel):
    """External API feature flags."""
    
    # =========================================================================
    # DEFI DATA APIS (Week 1)
    # =========================================================================
    enable_1inch: bool = True       # DEX aggregator
    enable_defillama: bool = True   # Protocol analytics
    enable_coingecko: bool = True   # Price data
    enable_hyperliquid: bool = True # Perpetuals DEX
    enable_uniswap: bool = True     # DEX
    enable_curve: bool = True       # Stableswap
    enable_aave: bool = True        # Lending protocol
    
    # =========================================================================
    # ENTERPRISE APIS (Week 2)
    # =========================================================================
    enable_chainalysis: bool = False  # Requires paid license
    enable_trm_labs: bool = False     # Requires paid license
    enable_gnosis_safe: bool = True   # Multi-sig
    enable_forta: bool = True         # Security monitoring
    enable_twilio: bool = False       # Requires paid account
    
    # =========================================================================
    # ADVANCED APIS (Week 3)
    # =========================================================================
    enable_privy: bool = False        # Requires app ID
    enable_axelar: bool = True        # Cross-chain
    enable_layerzero: bool = True     # Cross-chain messaging
    enable_opensea: bool = False      # Requires API key
    enable_snapshot: bool = True      # DAO governance
```

---

## 5. Agno Agent Feature Flags

### AgnoSettings

**Location**: `src/app/setup/config/agno.py`

Control de 5 agentes DeFi especializados (Agno framework).

```python
class AgnoAgentSettings(BaseModel):
    """Settings for individual Agno agents."""
    
    trading_enabled: bool = True     # DEX swaps (1inch, Curve)
    lending_enabled: bool = True     # Lending (Aave, Morpho)
    perpetual_enabled: bool = True   # Futures (Hyperliquid)
    portfolio_enabled: bool = True   # Portfolio tracking
    analytics_enabled: bool = True   # DeFi analytics (DeFiLlama)


class AgnoSettings(BaseModel):
    """Agno agent system configuration."""
    
    # Master switch
    enabled: bool = True
    
    # Intent routing
    intent_classification_enabled: bool = True
    fallback_to_general: bool = True
    
    # Per-agent flags
    agents: AgnoAgentSettings
```

### AgnoConfig

```python
class AgnoConfig(BaseModel):
    """Agno configuration with retry settings."""
    
    # Model configuration
    default_model: str = "gpt-4-turbo"
    fallback_model: str = "gpt-3.5-turbo"
    intent_threshold: float = 0.75
    
    # Context settings
    session_timeout: int = 3600
    max_context_messages: int = 20
    
    # Feature flags
    enable_intent_classification: bool = True
    enable_context_memory: bool = True
    enable_multi_agent_routing: bool = True
    
    # Debug settings
    debug_mode: bool = False
    log_intent_classification: bool = True
    log_agent_selection: bool = True
    
    # Retry configuration
    retry: AgnoRetryConfig


class AgnoRetryConfig(BaseModel):
    """Retry configuration for MCP tool calls."""
    
    enabled: bool = True
    max_attempts: int = 2
    initial_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 5.0
    exponential_base: float = 2.0
    circuit_breaker_enabled: bool = True
    telemetry_enabled: bool = True
```

### AgentRouter Feature Flag Usage

**Location**: `src/app/infrastructure/agno/agent_router.py`

```python
class AgentRouter:
    """Routes queries to specialized agents based on feature flags."""
    
    def __init__(
        self,
        config: AgnoConfig,
        settings: Optional[AgnoSettings] = None,
        debug_mode: bool = False,
    ):
        self.config = config
        self.settings = settings or AgnoSettings()
    
    def _is_agent_enabled(self, agent_type: AgentType) -> bool:
        """Check if agent is enabled via feature flags."""
        if not self.settings.enabled:
            return False
        
        agents = self.settings.agents
        return {
            AgentType.TRADING: agents.trading_enabled,
            AgentType.LENDING: agents.lending_enabled,
            AgentType.PERPETUAL: agents.perpetual_enabled,
            AgentType.ANALYTICS: agents.analytics_enabled,
            AgentType.PORTFOLIO: agents.portfolio_enabled,
        }.get(agent_type, False)
```

---

## 6. Integration Feature Flags

### IntegrationSettings

**Location**: `src/app/setup/config/integrations.py`

Control de funcionalidades de chat y proyectos.

```python
class ChatIntegrationSettings(BaseModel):
    """Chat integration feature flags."""
    
    enabled: bool = True
    hunter_tools_enabled: bool = True      # Hunter AI sentiment/predictions
    ultra_tools_enabled: bool = True       # ULTRA arbitrage tools
    comprehensive_analysis_enabled: bool = True  # Parallel tool execution
    max_parallel_tools: int = 10


class ProjectIntegrationSettings(BaseModel):
    """Project integration feature flags."""
    
    enabled: bool = True
    templates_enabled: bool = True          # Pre-built project templates
    risk_validation_enabled: bool = True    # Risk limit validation
    tool_permissions_enabled: bool = True   # Tool permission enforcement


class IntegrationSettings(BaseModel):
    """Master integration settings."""
    
    chat: ChatIntegrationSettings
    projects: ProjectIntegrationSettings
```

---

## 7. Admin API Endpoints

### Telemetry Feature Flags API

**Location**: `src/app/presentation/http/controllers/telemetry/router.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/telemetry/flags` | GET | Get current feature flags |
| `/api/v1/telemetry/flags` | PUT | Update feature flags at runtime |
| `/api/v1/telemetry/flags/disable-api/{api_name}` | POST | Disable telemetry for specific API |
| `/api/v1/telemetry/flags/enable-api/{api_name}` | POST | Enable telemetry for specific API |
| `/api/v1/telemetry/flags/disable-llm/{provider}` | POST | Disable telemetry for LLM provider |
| `/api/v1/telemetry/flags/enable-llm/{provider}` | POST | Enable telemetry for LLM provider |
| `/api/v1/telemetry/flags/save` | POST | Persist flags to Redis |
| `/api/v1/telemetry/flags/load` | POST | Load flags from Redis |
| `/api/v1/telemetry/flags/saved` | DELETE | Delete saved flags from Redis |

### Example: Update Telemetry Flags

```bash
# Toggle global telemetry and adjust sampling
curl -X PUT "/api/v1/telemetry/flags" \
  -H "Authorization: Bearer $TOKEN" \
  -G \
  -d "global_enabled=true" \
  -d "api_telemetry_enabled=true" \
  -d "llm_telemetry_enabled=false" \
  -d "api_sample_rate=0.5"
```

### Example: Disable Specific API Telemetry

```bash
# Disable telemetry for CoinGecko API
curl -X POST "/api/v1/telemetry/flags/disable-api/coingecko" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Usage Examples

### Check If Agent Is Enabled

```python
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.enums.agent_type import AgentType

class MyInteractor:
    def __init__(self, feature_flags: FeatureFlagsGateway):
        self._flags = feature_flags
    
    async def execute(self):
        # Check if agent is enabled
        if not await self._flags.is_agent_enabled(AgentType.DEFI_YIELD):
            raise AgentDisabledError("DeFi Yield agent is disabled")
        
        # Get enabled agents list
        enabled = await self._flags.get_enabled_agents()
        
        # Get agent configuration
        config = await self._flags.get_agent_config(AgentType.RISK_ANALYZER)
        model = config.model
        temperature = config.temperature
```

### Check Telemetry Before Recording

```python
from app.infrastructure.telemetry.feature_flags import get_feature_flags

flags = get_feature_flags()

# Check if API telemetry is enabled for specific API
if flags.is_api_enabled("coingecko"):
    ctx = telemetry.start_call("coingecko", "get_price")
    # ... make API call
    await telemetry.record(ctx)

# Check sampling before recording
if flags.should_sample_api("coingecko"):
    await telemetry.record(ctx)
```

### Runtime Toggle via DI

```python
from dishka import Provider, Scope, provide

class MyProvider(Provider):
    scope = Scope.APP
    
    @provide
    def provide_feature_flags(self) -> TelemetryFeatureFlags:
        return get_feature_flags()
```

---

## 9. TOML Configuration Example

```toml
# config/local/config.toml

[agent_squad]
enabled = true
enable_intent_classification = true
intent_classification_model = "gpt-4o-mini"
intent_confidence_threshold = 0.85
fallback_agent = "chat"

enable_supervisor = true
supervisor_model = "gpt-4o"
supervisor_max_agents = 5

telemetry_enabled = true
telemetry_sample_rate = 1.0

[agent_squad.agents.chat]
enabled = true
model = "gpt-4o-mini"
temperature = 0.7
max_tokens = 1000

[agent_squad.agents.hunter_ai]
enabled = true
model = "gpt-4o"
temperature = 0.5
max_tokens = 2000

[agent_squad.agents.defi_yield]
enabled = true
model = "gpt-4o-mini"
temperature = 0.3
max_tokens = 1500

# Enterprise agents (disabled by default)
[agent_squad.agents.compliance_monitor]
enabled = false

[agent_squad.external_apis]
enable_1inch = true
enable_defillama = true
enable_coingecko = true
enable_chainalysis = false  # Requires paid license
enable_twilio = false       # Requires paid account

[agno]
enabled = true
default_model = "gpt-4-turbo"
fallback_model = "gpt-3.5-turbo"
intent_threshold = 0.75
debug_mode = false

[agno.agents]
trading_enabled = true
lending_enabled = true
perpetual_enabled = true
portfolio_enabled = true
analytics_enabled = true

[agno.retry]
enabled = true
max_attempts = 2
initial_backoff_seconds = 1.0
circuit_breaker_enabled = true
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Telemetry Flags** | `infrastructure/telemetry/feature_flags.py` | TelemetryFeatureFlags class |
| **Agent Squad Config** | `setup/config/agent_squad.py` | AgentSquadSettings, ExternalAPIsConfig |
| **Agent Config VO** | `domain/value_objects/agent_squad/agent_squad_config.py` | AgentSquadConfig, AgentConfig |
| **Feature Flags Port** | `domain/ports/agent_squad/feature_flags_gateway.py` | FeatureFlagsGateway protocol |
| **Feature Flags Adapter** | `infrastructure/adapters/agent_squad/feature_flags_config.py` | FeatureFlagsConfig adapter |
| **Agno Config** | `setup/config/agno.py` | AgnoSettings, AgnoConfig |
| **Integration Config** | `setup/config/integrations.py` | IntegrationSettings |
| **Enabled Agents Query** | `application/agent_squad/queries/get_enabled_agents.py` | Tier-based filtering |
| **Agent Router** | `infrastructure/agno/agent_router.py` | Routing with feature flags |
| **Telemetry API** | `presentation/http/controllers/telemetry/router.py` | Admin endpoints |
| **Telemetry DI** | `setup/ioc/telemetry.py` | TelemetryProvider |

---

## Feature Flag Categories Summary

| Category | Scope | Configuration Source | Runtime Toggle |
|----------|-------|---------------------|----------------|
| **Telemetry** | Global, per-API, per-LLM | Environment + Redis | ✅ Yes |
| **Agent Squad** | 18 agents, per-agent config | TOML | ❌ Restart required |
| **Agno** | 5 DeFi agents | TOML + Pydantic | ❌ Restart required |
| **External APIs** | 15+ integrations | TOML | ❌ Restart required |
| **Integrations** | Chat, Projects | TOML | ❌ Restart required |

---

## Best Practices

### 1. Use Feature Flags for Progressive Rollout

```python
# Enable new feature for subset of users
if feature_flags.is_agent_enabled(AgentType.NEW_FEATURE):
    await new_feature.execute()
else:
    await legacy_feature.execute()
```

### 2. Graceful Degradation

```python
# Fallback when agent is disabled
try:
    if not await self._flags.is_agent_enabled(AgentType.DEFI_YIELD):
        raise AgentDisabledError()
    return await defi_yield_agent.execute(query)
except AgentDisabledError:
    return await chat_agent.execute(query)  # Fallback to chat
```

### 3. Use Sampling to Control Volume

```python
# Reduce telemetry volume in production
TELEMETRY_API_SAMPLE_RATE=0.1     # 10% of API calls
TELEMETRY_LLM_SAMPLE_RATE=1.0     # 100% of LLM calls (expensive, track all)
TELEMETRY_TRACE_SAMPLE_RATE=0.05  # 5% of traces
```

### 4. Persist Critical Changes

```python
# Save flags to Redis for persistence across restarts
await save_flags_to_redis(flags, redis_client)
```

---

**Last Updated**: January 2, 2026
