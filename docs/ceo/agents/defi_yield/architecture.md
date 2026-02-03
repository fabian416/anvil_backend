# DeFi Yield Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **DEFI_YIELD** agent, providing yield farming and APY optimization using DeFiLlama data and LLM analysis.

### Key Components

- **DefiYieldAgent**: Agent Squad implementation
- **DeFiLlamaClient**: External API client for yield data
- **Risk Scoring**: APY and TVL-based risk calculation

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEFI YIELD AGENT ARCHITECTURE                         │
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
                    ┌────────────▼─────────────┐
                    │     DefiYieldAgent       │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   DeFiLlama Client      │           │      Vertex AI LLM      │
│   (Yield Pools API)     │           │   (Recommendations)     │
└─────────────────────────┘           └─────────────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    DEFI_YIELD = "defi_yield"  # Yield farming
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
AGENT_MAPPING = {
    "find_yield": AgentType.DEFI_YIELD,
    "yield_farming": AgentType.DEFI_YIELD,
    "compare_lending_rates": AgentType.DEFI_YIELD,
    "lending_yield": AgentType.DEFI_YIELD,
}
```

---

## Infrastructure Layer

### DefiYieldAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent.py`
**Lines**: ~326

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

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 65-264 | Main entry point |
| `is_available()` | 266-268 | Availability check |
| `_get_system_prompt()` | 270-325 | Yield analysis prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    defi_llama_client: Any | None = None,  # DeFiLlama API
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,           # Balanced
    max_tokens: int = 1500,
):
```

---

## Execution Flow

### Main Execute Method

```python
async def execute(self, conversation_id, message, conversation_context):
    # 1. Validate DeFiLlama client
    defi_llama_client = self._validate_defillama_client()
    
    # 2. Detect protocol from message
    protocol_filter = self._detect_protocol(message.value.lower())
    
    # 3. Fetch yield pools from DeFiLlama
    yields = await defi_llama_client.get_protocol_yields(
        protocol=protocol_filter,
        chain=chain_filter,
    )
    
    # 4. Sort by APY and take top 10
    top_yields = sorted(yields, key=lambda y: y.apy, reverse=True)[:10]
    
    # 5. Format as markdown table
    yield_data_context = self._format_yield_table(top_yields)
    
    # 6. Build enhanced message with data
    enhanced_message = f"{message.value}\n\n{yield_data_context}"
    
    # 7. LLM generates recommendations
    response = await self._llm_client.chat(
        messages=[
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": enhanced_message},
        ],
        model=self._model,
        temperature=self._temperature,
    )
    
    # 8. Return with sources
    return AgentResponse(
        content=response["content"],
        sources=[llm_source, defillama_source],
        metadata={"latency_ms": latency_ms},
    )
```

---

## Protocol Detection

### Keyword Detection

```python
# From defi_yield_agent.py

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
```

---

## Yield Table Formatting

### Table Structure

```python
yield_data_context = "\n\n**REAL-TIME APY DATA FROM DEFILLAMA:**\n\n"
yield_data_context += "Top yield opportunities (sorted by APY):\n\n"

# Markdown table header
yield_data_context += "| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |\n"
yield_data_context += "|----------|------|-------|---------|-----|-------------------|----------------------|\n"

for yield_data in top_yields:
    # Format APY
    if yield_data.apy_base and yield_data.apy_reward:
        apy_str = f"{yield_data.apy_base:.2f}% + {yield_data.apy_reward:.2f}%"
    else:
        apy_str = f"{yield_data.apy:.2f}%"
    
    # Format TVL
    if yield_data.tvl_usd >= 1_000_000:
        tvl_str = f"${yield_data.tvl_usd/1_000_000:.2f}M"
    elif yield_data.tvl_usd >= 1_000:
        tvl_str = f"${yield_data.tvl_usd/1_000:.2f}K"
    else:
        tvl_str = f"${yield_data.tvl_usd:,.0f}"
    
    # Calculate risk score
    risk_score = calculate_risk_score(yield_data)
    
    # Format IL risk
    il_risk = format_il_risk(yield_data)
    
    yield_data_context += f"| {protocol} | {pool} | {chain} | {apy_str} | {tvl_str} | {risk_score} | {il_risk} |\n"
```

---

## Risk Score Calculation

### APY-Based Risk

```python
risk_score = 50  # Base risk

if yield_data.apy > 10000:  # > 10,000% APY
    risk_score = 95  # Likely unsustainable
elif yield_data.apy > 1000:  # > 1,000% APY
    risk_score = 85  # Very high risk
elif yield_data.apy > 100:  # > 100% APY
    risk_score = 70  # High risk
```

### TVL-Based Risk

```python
if yield_data.tvl_usd < 100_000:  # Low TVL
    risk_score = min(100, risk_score + 10)
```

### IL Risk Detection

```python
il_risk = "Yes"  # Default for LP pools

if yield_data.il_risk is not None:
    il_risk = str(yield_data.il_risk)
    if il_risk.lower() in ["no", "false", "0"]:
        il_risk = "No"
    elif il_risk.lower() in ["yes", "true", "1"]:
        il_risk = "Yes"
```

---

## System Prompt

```python
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

Analysis includes:
- Current APY (base rate + rewards)
- Impermanent loss risk
- Pool composition
- Reward tokens
- Protocol risk
- Gas costs

**DO NOT use generic language like "need real-time data"**
"""
```

---

## Supervisor Routing

### Yield vs Swap Distinction

```python
# CRITICAL: This is the most common mistake!

# Yield queries → defi_yield
"best yield for USDC" → defi_yield
"highest APY" → defi_yield
"yield farming options" → defi_yield

# Swap queries → hunter_ai (NOT defi_yield!)
"best swap rate for ETH to USDC" → hunter_ai  # ✅
"best swap rate for ETH to USDC" → defi_yield  # ❌ WRONG
```

### Combined Queries

```python
# With risk analysis
"suggest low-risk DeFi yield opportunities" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["defi_yield"]}
]

# With portfolio
"best yields and my balance" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "portfolio", "depends_on": []}
]

# With allocation optimization
"allocation optimization" → [
    {"agent_type": "portfolio", "depends_on": []},
    {"agent_type": "defi_yield", "depends_on": []}
]
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
if validated_client and yield_data_context:
    sources.append(create_api_source(
        source_name="DeFiLlama",
        url="https://defillama.com/yields",
        endpoint="/pools",
        citation_text="Real-time APY data from DeFiLlama",
        fetched_at=fetched_at,
    ))
```

---

## Testing

### Test Cases

```python
# Protocol detection
def test_detect_protocol():
    assert detect_protocol("Best yield on Aave") == "aave"
    assert detect_protocol("Morpho rates") == "morpho"
    assert detect_protocol("Best USDC yield") is None  # General query

# Risk score calculation
def test_risk_score():
    # Very high APY = high risk
    assert calculate_risk_score(apy=15000, tvl=1000000) == 95
    # High APY = high risk
    assert calculate_risk_score(apy=500, tvl=1000000) == 85
    # Low TVL = higher risk
    assert calculate_risk_score(apy=50, tvl=50000) == 60

# APY formatting
def test_apy_format():
    assert format_apy(base=3.5, reward=2.0) == "3.50% + 2.00%"
    assert format_apy(total=5.5) == "5.50%"

# TVL formatting
def test_tvl_format():
    assert format_tvl(1500000000) == "$1.50B"
    assert format_tvl(250000000) == "$250.00M"
    assert format_tvl(50000) == "$50.00K"
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| DeFiLlama API | < 500ms | ~400ms |
| LLM analysis | < 800ms | ~700ms |
| Total | < 1.5s | ~1.1s |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added DeFiLlama integration |
| 2026-01-29 | Added risk score calculation |
| 2026-01-29 | Added yield table formatting |
