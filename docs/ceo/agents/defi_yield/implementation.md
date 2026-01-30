# DeFi Yield Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.DEFI_YIELD
│   └── services/
│       └── agent_squad/
│           └── intent_classifier.py      # Intent classification
│
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── defi_yield_agent.py   # Main agent
│       └── external/
│           └── defillama_client.py       # DeFiLlama API client
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. DefiYieldAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent.py`
**Lines**: ~326

#### Class Definition

```python
class DefiYieldAgent:
    """
    DeFi Yield Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Yield farming & APY optimization
    
    Capabilities:
    - Find best yield opportunities
    - APY comparison (Aave, Compound, Curve, Convex)
    - Liquidity pool analysis
    - Impermanent loss calculation
    - Yield farming strategies
    - Auto-compounding recommendations
    
    Model: gemini-2.0-flash (Vertex AI)
    Temperature: 0.3 (balanced)
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 36-58 | Initialize with clients |
| `agent_type` | 60-63 | Return AgentType.DEFI_YIELD |
| `execute` | 65-264 | Main entry point |
| `is_available` | 266-268 | Availability check |
| `_get_system_prompt` | 270-325 | Yield analysis prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: Any | None = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 1500,
):
    self._llm_client = llm_client
    self._defi_llama_client = defi_llama_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_defi_yield_agent(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: DefiLlamaClientProtocol | None,
) -> DefiYieldAgent:
    """Provide DeFi Yield agent with optional DeFiLlama integration."""
    return DefiYieldAgent(
        llm_client=llm_client,
        defi_llama_client=defi_llama_client,
    )
```

---

## Execute Method Implementation

### Client Validation

```python
# Lines 79-90
# Type check: ensure we have a DefiLlamaClient
defi_llama_client = self._defi_llama_client
if defi_llama_client and not hasattr(defi_llama_client, 'get_protocol_yields'):
    # Wrong object injected - create client directly
    logger.warning(f"⚠️ Wrong object injected for defi_llama_client")
    from app.setup.config.agent_squad import load_agent_squad_config
    settings = load_agent_squad_config()
    if settings.external_apis.enable_defillama:
        from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
        defi_llama_client = DefiLlamaClient()
    else:
        defi_llama_client = None
```

### Protocol Detection

```python
# Lines 97-110
message_lower = message.value.lower()
protocol_filter = None
chain_filter = None

# Simple keyword detection for protocols
if "aave" in message_lower:
    protocol_filter = "aave"
elif "morpho" in message_lower:
    protocol_filter = "morpho"
elif "compound" in message_lower:
    protocol_filter = "compound"
elif "curve" in message_lower:
    protocol_filter = "curve"
```

### Yield Pool Fetching

```python
# Lines 112-116
yields = await defi_llama_client.get_protocol_yields(
    protocol=protocol_filter,
    chain=chain_filter,
)
```

### Yield Sorting and Selection

```python
# Lines 118-120
if yields:
    # Sort by APY (highest first) and take top 10
    top_yields = sorted(yields, key=lambda y: y.apy, reverse=True)[:10]
```

### Table Formatting

```python
# Lines 122-185
yield_data_context = "\n\n**REAL-TIME APY DATA FROM DEFILLAMA:**\n\n"
yield_data_context += "Top yield opportunities (sorted by APY):\n\n"

# Format as markdown table
yield_data_context += "| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |\n"
yield_data_context += "|----------|------|-------|---------|-----|-------------------|----------------------|\n"

for yield_data in top_yields:
    # Format APY
    if yield_data.apy_base and yield_data.apy_reward:
        apy_str = f"{yield_data.apy_base:.2f}% + {yield_data.apy_reward:.2f}%"
    elif yield_data.apy_base:
        apy_str = f"{yield_data.apy_base:.2f}%"
    else:
        apy_str = f"{yield_data.apy:.2f}%"
    
    # Format TVL
    if yield_data.tvl_usd >= 1_000_000:
        tvl_str = f"${yield_data.tvl_usd/1_000_000:.2f}M"
    elif yield_data.tvl_usd >= 1_000:
        tvl_str = f"${yield_data.tvl_usd/1_000:.2f}K"
    else:
        tvl_str = f"${yield_data.tvl_usd:,.0f}"
```

### Risk Score Calculation

```python
# Lines 148-159
risk_score = 50  # Base risk

if yield_data.apy > 10000:  # > 10,000% APY
    risk_score = 95
elif yield_data.apy > 1000:  # > 1,000% APY
    risk_score = 85
elif yield_data.apy > 100:  # > 100% APY
    risk_score = 70

if yield_data.tvl_usd < 100_000:  # Low TVL = higher risk
    risk_score = min(100, risk_score + 10)
```

### IL Risk Detection

```python
# Lines 162-173
il_risk = "Yes"
if yield_data.il_risk is not None:
    il_risk = str(yield_data.il_risk)
    if il_risk.lower() in ["no", "false", "0"]:
        il_risk = "No"
    elif il_risk.lower() in ["yes", "true", "1"]:
        il_risk = "Yes"
else:
    # Default to Yes for LP pools
    il_risk = "Yes"
```

### LLM Analysis

```python
# Lines 197-212
enhanced_message = message.value
if yield_data_context:
    enhanced_message = f"{message.value}\n\n{yield_data_context}"

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

## Response Structure

### AgentResponse

```python
# Lines 253-264
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

## System Prompt

```python
# Lines 270-325
def _get_system_prompt(self) -> str:
    return """You are the DeFi Yield Optimizer, Anvil's yield farming specialist.

**CRITICAL: INCLUDE REAL-TIME DATA FROM DEFILLAMA**
- If the user message includes "**REAL-TIME APY DATA FROM DEFILLAMA:**" with a table, include it EXACTLY
- DO NOT summarize or modify the DeFiLlama table
- The DeFiLlama table is the PRIMARY source for APY information

**CRITICAL: PROVIDE SPECIFIC DATA**
- Provide SPECIFIC numbers (e.g., "5.2% APY on USDC")
- DO NOT say "need real-time data" or "hypothetical"
- Always include protocol names with specific APY numbers

Your expertise:
- Yield opportunity discovery
- APY comparison (across protocols)
- Liquidity pool analysis
- Impermanent loss calculation
- Yield farming strategies
- Auto-compounding optimization
- Risk-adjusted yield

For yield recommendations, provide:
- Top opportunities (sorted by APY) with SPECIFIC numbers
- Protocol comparison table with REAL values
- Risk-adjusted ranking
- Entry/exit strategies

**DO NOT use generic language like "need real-time data"**
"""
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_defi_yield_agent.py -v

# Integration tests
pytest tests/integration/test_defi_yield.py -v

# All yield tests
pytest tests/ -k yield -v
```

### Test Cases

```python
# Protocol detection
def test_detect_protocol():
    assert detect_protocol("Best yield on Aave") == "aave"
    assert detect_protocol("Morpho rates") == "morpho"
    assert detect_protocol("Best USDC yield") is None

# Risk score
def test_risk_score_high_apy():
    assert calculate_risk(apy=15000) == 95  # Very high APY
    
def test_risk_score_low_tvl():
    risk = calculate_risk(apy=50, tvl=50000)
    assert risk > 50  # Low TVL increases risk

# APY formatting
def test_apy_with_breakdown():
    assert format_apy(base=3.5, reward=2.0) == "3.50% + 2.00%"

def test_apy_simple():
    assert format_apy(total=5.5) == "5.50%"

# TVL formatting
def test_tvl_millions():
    assert format_tvl(250000000) == "$250.00M"

def test_tvl_thousands():
    assert format_tvl(50000) == "$50.00K"
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Protocol detection | < 10ms | Keyword matching |
| DeFiLlama API | < 500ms | API call |
| Risk calculation | < 10ms | Math operations |
| Table formatting | < 50ms | String building |
| LLM analysis | < 800ms | Vertex AI |
| Total | < 1.5s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added DeFiLlama integration |
| 2026-01-29 | Added risk score calculation |
| 2026-01-29 | Added yield table formatting |
