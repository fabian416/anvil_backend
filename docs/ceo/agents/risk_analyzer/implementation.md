# Risk Analyzer Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.RISK_ANALYZER
│   └── services/
│       └── agent_squad/
│           └── intent_classifier.py      # Intent classification
│
├── application/
│   └── hunter/
│       └── risk_analyzer.py              # ML-based risk service
│
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── risk_analyzer_agent.py  # Main agent
│       └── external/
│           └── defillama_client.py        # DeFiLlama API client
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. RiskAnalyzerAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/risk_analyzer_agent.py`
**Lines**: ~286

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 37-59 | Initialize with clients |
| `agent_type` | 61-64 | Return AgentType.RISK_ANALYZER |
| `execute` | 66-241 | Main entry point |
| `is_available` | 243-245 | Availability check |
| `_get_system_prompt` | 247-285 | Risk analysis prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: Any | None = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_tokens: int = 1500,
):
    self._llm_client = llm_client
    self._defi_llama_client = defi_llama_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. RiskAnalyzer Service

**File**: `src/app/application/hunter/risk_analyzer.py`
**Lines**: ~543

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 102-114 | Initialize with config |
| `analyze_comprehensive_risk` | 116-172 | Full multi-factor analysis |
| `analyze_volatility_risk` | 174-251 | Price volatility |
| `analyze_liquidity_risk` | 253-326 | Trading volume |
| `analyze_smart_contract_risk` | 328-393 | Code security |
| `analyze_market_correlation_risk` | 395-479 | Systemic risk |
| `_calculate_max_drawdown` | 481-492 | Max drawdown |
| `_score_to_level` | 494-510 | Score to level |
| `_generate_recommendation` | 512-543 | Recommendations |

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_risk_analyzer_agent(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: DefiLlamaClientProtocol | None,
) -> RiskAnalyzerAgent:
    """Provide Risk Analyzer agent with optional DeFiLlama integration."""
    return RiskAnalyzerAgent(
        llm_client=llm_client,
        defi_llama_client=defi_llama_client,
    )
```

---

## Execute Method Implementation

### Main Flow

```python
# Lines 66-241
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    start_time = time.time()
    
    # Fetch protocol risk data from DeFiLlama if available
    risk_data_context = ""
    
    # Type check: ensure we have a DefiLlamaClient
    defi_llama_client = self._defi_llama_client
    if defi_llama_client and not hasattr(defi_llama_client, 'get_protocol_tvl'):
        # Wrong object injected - create client directly
        from app.setup.config.agent_squad import load_agent_squad_config
        settings = load_agent_squad_config()
        if settings.external_apis.enable_defillama:
            from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
            defi_llama_client = DefiLlamaClient()
```

### Protocol Detection

```python
# Lines 98-112
message_lower = message.value.lower()
protocol_filter = None

# Simple keyword detection for protocols
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

### TVL Data Fetching

```python
# Lines 114-143
if protocol_filter:
    try:
        protocol_tvl = await defi_llama_client.get_protocol_tvl(protocol_filter)
        
        if protocol_tvl:
            risk_data_context = "\n\n**PROTOCOL DATA FROM DEFILLAMA:**\n"
            risk_data_context += f"**{protocol_filter.upper()} Protocol:**\n"
            risk_data_context += f"- Total TVL: ${protocol_tvl.tvl:,.0f}\n"
            
            # Calculate risk indicators from TVL
            if protocol_tvl.tvl > 1_000_000_000:  # > $1B
                risk_data_context += "- Size: Very Large (Lower risk due to scale)\n"
            elif protocol_tvl.tvl > 100_000_000:  # > $100M
                risk_data_context += "- Size: Large (Moderate risk)\n"
            elif protocol_tvl.tvl > 10_000_000:  # > $10M
                risk_data_context += "- Size: Medium (Higher risk)\n"
            else:
                risk_data_context += "- Size: Small (Higher risk)\n"
            
            # Chain distribution
            if protocol_tvl.chain_tvls:
                risk_data_context += f"- Chain Distribution: {len(protocol_tvl.chain_tvls)} chains\n"
                top_chains = sorted(protocol_tvl.chain_tvls.items(), key=lambda x: x[1], reverse=True)[:3]
                for chain, tvl in top_chains:
                    risk_data_context += f"  - {chain}: ${tvl:,.0f}\n"
```

### Top Protocols Comparison

```python
# Lines 145-166
try:
    all_protocols = await defi_llama_client.get_all_protocols()
    if all_protocols:
        top_protocols = sorted(all_protocols, key=lambda p: p.tvl, reverse=True)[:10]
        
        if not risk_data_context:
            risk_data_context = "\n\n**PROTOCOL RISK CONTEXT FROM DEFILLAMA:**\n"
        else:
            risk_data_context += "\n**Top Protocols by TVL (for comparison):**\n"
        
        for i, protocol in enumerate(top_protocols, 1):
            risk_data_context += f"{i}. {protocol.name}: ${protocol.tvl:,.0f} TVL"
            if protocol.change_7d:
                change_sign = "+" if protocol.change_7d >= 0 else ""
                risk_data_context += f" ({change_sign}{protocol.change_7d:.1f}% 7d)"
            risk_data_context += "\n"
```

### LLM Analysis

```python
# Lines 174-189
enhanced_message = message.value
if risk_data_context:
    enhanced_message = f"{message.value}\n\n{risk_data_context}"

messages = [
    {"role": "system", "content": self._get_system_prompt()},
    {"role": "user", "content": enhanced_message},
]

response = await self._llm_client.chat(
    messages=messages,
    model=self._model,
    temperature=self._temperature,
    max_tokens=self._max_tokens,
)
```

---

## RiskAnalyzer Service Implementation

### Comprehensive Risk Analysis

```python
# Lines 116-172
async def analyze_comprehensive_risk(
    self, token_symbol: str
) -> CompositeRiskAssessment:
    # Analyze all risk factors
    volatility_risk = await self.analyze_volatility_risk(token_symbol)
    liquidity_risk = await self.analyze_liquidity_risk(token_symbol)
    smart_contract_risk = await self.analyze_smart_contract_risk(token_symbol)
    correlation_risk = await self.analyze_market_correlation_risk(token_symbol)

    # Combine scores (weighted average)
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

    overall_level = self._score_to_level(overall_score)
    recommendation = self._generate_recommendation(
        overall_score, overall_level, volatility_risk, liquidity_risk
    )

    return CompositeRiskAssessment(
        token_symbol=token_symbol,
        overall_risk_score=overall_score,
        overall_risk_level=overall_level,
        risk_factors={
            "volatility": volatility_risk,
            "liquidity": liquidity_risk,
            "smart_contract": smart_contract_risk,
            "correlation": correlation_risk,
        },
        recommendation=recommendation,
        timestamp=utc_now(),
    )
```

### Volatility Risk Analysis

```python
# Lines 174-251
async def analyze_volatility_risk(self, token_symbol: str) -> RiskScore:
    # Fetch historical prices
    prices = await self.price_service.fetch_historical_prices(
        token_symbol, days=self.config.volatility_window
    )

    if not prices or len(prices) < 2:
        return RiskScore(
            factor="volatility",
            score=20.0,
            level="low",
            details={"error": "Insufficient data"},
            timestamp=utc_now(),
        )

    closes = np.array([p.close for p in prices])
    returns = np.diff(closes) / closes[:-1]

    # Calculate volatility metrics
    volatility_std = np.std(returns)
    avg_daily_range = np.mean([p.high - p.low for p in prices]) / np.mean(closes)
    max_drawdown = self._calculate_max_drawdown(closes)
    sharp_moves = np.sum(np.abs(returns) > self.config.high_volatility_threshold)

    # Score calculation (0-100, higher = more risky)
    volatility_score = min(100, volatility_std * 100 * 20)
    range_score = min(100, avg_daily_range * 100 * 10)
    drawdown_score = min(100, abs(max_drawdown) * 100)
    sharp_score = min(100, (sharp_moves / len(returns)) * 100 * 5)

    overall_score = (
        volatility_score * 0.40
        + range_score * 0.25
        + drawdown_score * 0.25
        + sharp_score * 0.10
    )

    return RiskScore(
        factor="volatility",
        score=overall_score,
        level=self._score_to_level(overall_score),
        details={
            "historical_volatility": round(volatility_std * 100, 2),
            "avg_daily_range_pct": round(avg_daily_range * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "sharp_movements": int(sharp_moves),
        },
        timestamp=utc_now(),
    )
```

### Score to Level Conversion

```python
# Lines 494-510
def _score_to_level(self, score: float) -> str:
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "extreme"
```

### Recommendation Generation

```python
# Lines 512-543
def _generate_recommendation(
    self,
    overall_score: float,
    overall_level: str,
    volatility_risk: RiskScore,
    liquidity_risk: RiskScore,
) -> str:
    if overall_level == "low":
        return "Low risk profile. Suitable for conservative portfolios with standard position sizing."
    elif overall_level == "medium":
        if volatility_risk.level in ["high", "extreme"]:
            return "Moderate risk with high volatility. Use tighter stop-losses and reduce position size by 30-50%."
        elif liquidity_risk.level in ["high", "extreme"]:
            return "Moderate risk with liquidity concerns. Limit position size and avoid large market orders."
        else:
            return "Moderate risk profile. Suitable for balanced portfolios with standard position sizing."
    elif overall_level == "high":
        return "High risk profile. Reduce position size by 50-70%. Use strict stop-losses and monitor closely."
    else:  # extreme
        return "Extreme risk detected. NOT recommended for most traders. If trading, use minimal position size (<5%) and very tight stops."
```

---

## Response Structure

### AgentResponse

```python
# Lines 230-241
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=tools_used,  # ["llm_gateway", "defillama_api"]
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
        "provider": provider_info,
    },
)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_risk_analyzer_agent.py -v

# Integration tests
pytest tests/integration/test_risk_analyzer.py -v

# All risk tests
pytest tests/ -k risk -v
```

### Test Cases

```python
# Protocol detection
def test_detect_protocol():
    assert detect_protocol("What's the risk of Aave?") == "aave"
    assert detect_protocol("Is Morpho safe?") == "morpho"
    assert detect_protocol("Compound risk analysis") == "compound"

# Size classification
def test_size_classification():
    assert classify_size(2_000_000_000) == "very_large"
    assert classify_size(500_000_000) == "large"
    assert classify_size(50_000_000) == "medium"
    assert classify_size(5_000_000) == "small"

# Risk score levels
def test_score_to_level():
    assert score_to_level(10) == "low"
    assert score_to_level(35) == "medium"
    assert score_to_level(60) == "high"
    assert score_to_level(90) == "extreme"

# Volatility calculation
def test_volatility_risk():
    risk = await analyzer.analyze_volatility_risk("ETH")
    assert 0 <= risk.score <= 100
    assert risk.level in ["low", "medium", "high", "extreme"]
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Protocol detection | < 10ms | Keyword matching |
| DeFiLlama API | < 500ms | API call |
| LLM analysis | < 1000ms | Vertex AI |
| Total | < 1.5s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added DeFiLlama integration |
| 2026-01-29 | Added ML-based risk service |
| 2026-01-29 | Added multi-factor scoring |
