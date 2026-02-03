# Risk Analyzer Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **RISK_ANALYZER** agent, providing comprehensive risk assessment for DeFi protocols and crypto tokens using DeFiLlama data and LLM analysis.

### Key Components

- **RiskAnalyzerAgent**: Agent Squad implementation with DeFiLlama
- **RiskAnalyzer**: Application service for ML-based analysis
- **DeFiLlamaClient**: External API client for TVL data

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RISK ANALYZER ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Supervisor Coordinator  │
                    │  (Routing Logic)         │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   RiskAnalyzerAgent     │           │     RiskAnalyzer        │
│   (Agent Squad)         │           │     (App Service)       │
│                         │           │                         │
│  - LLM-based analysis   │           │  - ML-based analysis    │
│  - DeFiLlama TVL        │           │  - Historical prices    │
│  - Protocol detection   │           │  - Volatility calc      │
│  - Qualitative assess   │           │  - Quantitative score   │
└───────────┬─────────────┘           └───────────┬─────────────┘
            │                                     │
            ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   DeFiLlama Client      │           │   PriceDataService      │
│   (External API)        │           │   (CoinGecko)           │
└─────────────────────────┘           └─────────────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    RISK_ANALYZER = "risk_analyzer"  # Risk assessment
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
AGENT_MAPPING = {
    "analyze_risk": AgentType.RISK_ANALYZER,
    "risk_assessment": AgentType.RISK_ANALYZER,
}
```

---

## Infrastructure Layer

### RiskAnalyzerAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/risk_analyzer_agent.py`
**Lines**: ~286

```python
class RiskAnalyzerAgent:
    """
    Risk Analyzer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Risk assessment & scoring
    
    Capabilities:
    - Protocol risk scoring (0-100)
    - Smart contract risk analysis
    - Liquidation risk (health factor)
    - Impermanent loss calculation
    - Concentration risk
    - Market risk (volatility)
    - Counterparty risk
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.2 (factual, precise)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 66-241 | Main entry point |
| `is_available()` | 243-245 | Availability check |
| `_get_system_prompt()` | 247-285 | Risk analysis prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    defi_llama_client: Any | None = None,  # DeFiLlama API
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,           # Low for precision
    max_tokens: int = 1500,
):
```

---

## Application Layer

### RiskAnalyzer Service

**File**: `src/app/application/hunter/risk_analyzer.py`
**Lines**: ~543

```python
class RiskAnalyzer:
    """ML-based risk analysis service.

    Analyzes cryptocurrency tokens across 4 risk dimensions:
    - Volatility (price stability)
    - Liquidity (trading volume)
    - Smart Contract (code security)
    - Market Correlation (systemic risk)
    """
```

### Risk Data Classes

```python
@dataclass
class RiskScore:
    """Individual risk factor score."""
    factor: str
    score: float  # 0-100 (0 = low risk, 100 = high risk)
    level: str    # "low", "medium", "high", "extreme"
    details: Dict
    timestamp: datetime

@dataclass
class CompositeRiskAssessment:
    """Complete risk assessment for a token."""
    token_symbol: str
    overall_risk_score: float  # 0-100
    overall_risk_level: str
    risk_factors: Dict[str, RiskScore]
    recommendation: str
    timestamp: datetime
```

### Risk Analysis Methods

| Method | Purpose |
|--------|---------|
| `analyze_comprehensive_risk()` | Full multi-factor analysis |
| `analyze_volatility_risk()` | Price volatility assessment |
| `analyze_liquidity_risk()` | Trading volume analysis |
| `analyze_smart_contract_risk()` | Code security evaluation |
| `analyze_market_correlation_risk()` | Systemic risk measurement |

---

## Execution Flow

### RiskAnalyzerAgent Flow

```python
async def execute(self, conversation_id, message, conversation_context):
    # 1. Validate DeFiLlama client
    defi_llama_client = self._validate_defillama_client()
    
    # 2. Detect protocol from message
    protocol_filter = self._detect_protocol(message.value.lower())
    
    # 3. Fetch TVL data if protocol detected
    if protocol_filter:
        protocol_tvl = await defi_llama_client.get_protocol_tvl(protocol_filter)
        risk_data_context = self._format_tvl_data(protocol_tvl)
    
    # 4. Fetch top protocols for comparison
    all_protocols = await defi_llama_client.get_all_protocols()
    risk_data_context += self._format_top_protocols(all_protocols)
    
    # 5. Build enhanced message with data
    enhanced_message = f"{message.value}\n\n{risk_data_context}"
    
    # 6. LLM generates risk assessment
    response = await self._llm_client.chat(
        messages=[
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": enhanced_message},
        ],
        model=self._model,
        temperature=self._temperature,
    )
    
    # 7. Return with sources
    return AgentResponse(
        content=response["content"],
        sources=[llm_source, defillama_source],
        metadata={"latency_ms": latency_ms},
    )
```

### RiskAnalyzer Service Flow

```python
async def analyze_comprehensive_risk(self, token_symbol: str):
    # 1. Analyze all risk factors
    volatility_risk = await self.analyze_volatility_risk(token_symbol)
    liquidity_risk = await self.analyze_liquidity_risk(token_symbol)
    smart_contract_risk = await self.analyze_smart_contract_risk(token_symbol)
    correlation_risk = await self.analyze_market_correlation_risk(token_symbol)
    
    # 2. Calculate weighted overall score
    weights = {
        "volatility": 0.30,
        "liquidity": 0.25,
        "smart_contract": 0.25,
        "correlation": 0.20,
    }
    
    overall_score = (
        volatility_risk.score * weights["volatility"]
        + liquidity_risk.score * weights["liquidity"]
        + smart_contract_risk.score * weights["smart_contract"]
        + correlation_risk.score * weights["correlation"]
    )
    
    # 3. Determine level and recommendation
    overall_level = self._score_to_level(overall_score)
    recommendation = self._generate_recommendation(
        overall_score, overall_level, volatility_risk, liquidity_risk
    )
    
    # 4. Return composite assessment
    return CompositeRiskAssessment(
        token_symbol=token_symbol,
        overall_risk_score=overall_score,
        overall_risk_level=overall_level,
        risk_factors={...},
        recommendation=recommendation,
    )
```

---

## Protocol Detection

### Keyword Detection

```python
# From risk_analyzer_agent.py

message_lower = message.value.lower()
protocol_filter = None

if "aave" in message_lower:
    protocol_filter = "aave"
elif "morpho" in message_lower:
    protocol_filter = "morpho"
elif "compound" in message_lower:
    protocol_filter = "compound"
elif "curve" in message_lower:
    protocol_filter = "curve"
elif "uniswap" in message_lower:
    protocol_filter = "uniswap"
```

### Size Classification

```python
# From risk_analyzer_agent.py

if protocol_tvl.tvl > 1_000_000_000:  # > $1B
    risk_data_context += "- Size: Very Large (Lower risk due to scale)\n"
elif protocol_tvl.tvl > 100_000_000:  # > $100M
    risk_data_context += "- Size: Large (Moderate risk)\n"
elif protocol_tvl.tvl > 10_000_000:  # > $10M
    risk_data_context += "- Size: Medium (Higher risk)\n"
else:
    risk_data_context += "- Size: Small (Higher risk)\n"
```

---

## Risk Calculations

### Volatility Risk

```python
# Fetch historical prices
prices = await self.price_service.fetch_historical_prices(
    token_symbol, days=self.config.volatility_window  # 30 days
)

closes = np.array([p.close for p in prices])
returns = np.diff(closes) / closes[:-1]

# Calculate metrics
volatility_std = np.std(returns)
avg_daily_range = np.mean([p.high - p.low for p in prices]) / np.mean(closes)
max_drawdown = self._calculate_max_drawdown(closes)
sharp_moves = np.sum(np.abs(returns) > 0.05)  # > 5% daily

# Score calculation (weighted)
overall_score = (
    volatility_score * 0.40
    + range_score * 0.25
    + drawdown_score * 0.25
    + sharp_score * 0.10
)
```

### Liquidity Risk

```python
volumes = np.array([p.volume for p in prices])
avg_volume = np.mean(volumes)
volume_std = np.std(volumes)
volume_consistency = 1 - (volume_std / (avg_volume + 1e-8))

# Low volume = high risk
volume_score = max(0, 100 - (avg_volume / 1_000_000) * 100)  # $1M threshold
consistency_score = (1 - volume_consistency) * 100
spread_score = 20.0  # Simulated

overall_score = (
    volume_score * 0.50
    + consistency_score * 0.30
    + spread_score * 0.20
)
```

### Correlation Risk

```python
# Fetch token and BTC prices
token_prices = await self.price_service.fetch_historical_prices(token_symbol, days=90)
btc_prices = await self.price_service.fetch_historical_prices("BTC", days=90)

# Calculate returns
token_returns = np.diff(token_closes) / token_closes[:-1]
btc_returns = np.diff(btc_closes) / btc_closes[:-1]

# Calculate correlation
correlation = np.corrcoef(token_returns, btc_returns)[0, 1]

# High correlation = High systemic risk
correlation_score = abs(correlation) * 100
```

---

## System Prompt

```python
def _get_system_prompt(self) -> str:
    return """You are the Risk Analyzer, Anvil's risk assessment specialist.

**CRITICAL: ANVIL IS REAL, NOT SIMULATED**
- Anvil is a REAL, LIVE DeFi platform - NOT simulated
- DO NOT use words like "simulated", "simulation", "mock"

Your expertise:
- Protocol risk scoring (0-100 scale)
- Smart contract risk analysis
- Liquidation risk calculation
- Impermanent loss estimation
- Concentration risk assessment
- Market risk (volatility, correlation)
- Counterparty risk

For each risk assessment, provide:
- Overall risk score (0-100)
  - 0-30: Low risk
  - 31-60: Medium risk
  - 61-80: High risk
  - 81-100: Critical risk
- Risk category breakdown
- Key risk factors
- Mitigation strategies
- Risk/reward analysis

Be conservative in risk assessments - better safe than sorry.
"""
```

---

## Source Attribution

### Building Sources

```python
sources = []
fetched_at = datetime.now(UTC)

# Add LLM source
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))

# Add DeFiLlama source if data was fetched
if validated_client and risk_data_context:
    sources.append(create_api_source(
        source_name="DeFiLlama",
        url="https://defillama.com/",
        citation_text="Protocol TVL and risk data from DeFiLlama",
        fetched_at=fetched_at,
    ))
```

---

## Supervisor Routing

### Combined Queries

```python
# From authenticated_supervisor.py

# Risk with yield
"best yield for USDC" → [
    {"agent_type": "defi_yield", "task_description": "Find yield opportunities"},
    {"agent_type": "risk_analyzer", "task_description": "Assess risk", "depends_on": ["defi_yield"]}
]

# Risk with arbitrage
"find arbitrage opportunities" → [
    {"agent_type": "hunter_ai", "task_description": "Find opportunities"},
    {"agent_type": "risk_analyzer", "task_description": "Assess risk", "depends_on": ["hunter_ai"]}
]

# Risk-adjusted portfolio
"risk-adjusted recommendations" → [
    {"agent_type": "portfolio", "task_description": "Analyze portfolio"},
    {"agent_type": "risk_analyzer", "task_description": "Add risk context", "depends_on": ["portfolio"]}
]
```

---

## Testing

### Test Cases

```python
# Protocol risk
def test_protocol_risk_assessment():
    response = await agent.execute(
        message=MessageContent("What's the risk of Aave?")
    )
    assert "Risk Score" in response.content
    assert response.sources  # Should have DeFiLlama source

# Size classification
def test_size_classification():
    # Very Large (>$1B)
    assert classify_size(2_000_000_000) == "very_large"
    # Large (>$100M)
    assert classify_size(500_000_000) == "large"
    # Medium (>$10M)
    assert classify_size(50_000_000) == "medium"
    # Small (<$10M)
    assert classify_size(5_000_000) == "small"

# Risk score to level
def test_score_to_level():
    assert score_to_level(10) == "low"
    assert score_to_level(35) == "medium"
    assert score_to_level(60) == "high"
    assert score_to_level(90) == "extreme"
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| DeFiLlama API | < 500ms | ~400ms |
| LLM analysis | < 1000ms | ~800ms |
| Total | < 1.5s | ~1.2s |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added DeFiLlama integration |
| 2026-01-29 | Added ML-based risk analysis service |
| 2026-01-29 | Added multi-factor risk scoring |
