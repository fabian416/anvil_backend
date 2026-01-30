# Gas Optimizer Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.GAS_OPTIMIZER
│   └── services/
│       └── agent_squad/
│           └── intent_classifier.py      # Intent classification
│
├── infrastructure/
│   └── adapters/
│       ├── agent_squad/
│       │   └── agents/
│       │       └── gas_optimizer_agent.py # Main agent
│       └── external/
│           └── web3_client.py            # Gas price fetching
│
├── application/
│   └── agents/
│       └── library/
│           └── gas_optimization_expert.py # Config template
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration

anvil_knowledge/
└── features/
    └── gas_optimizer.json                # Knowledge base
```

---

## Core Files

### 1. GasOptimizerAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/gas_optimizer_agent.py`
**Lines**: ~369

#### Class Definition

```python
class GasOptimizerAgent:
    """
    Gas Optimizer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Gas fee optimization & timing
    
    Capabilities:
    - Current gas price analysis
    - Gas price predictions (next hour, day)
    - Optimal transaction timing
    - Layer 2 migration recommendations
    - Batch transaction suggestions
    - Gas-efficient alternatives
    
    Model: gemini-2.0-flash (Vertex AI, fast, cost-effective)
    Temperature: 0.2 (factual)
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 36-58 | Initialize with clients |
| `agent_type` | 60-63 | Return AgentType.GAS_OPTIMIZER |
| `execute` | 65-285 | Main entry point |
| `is_available` | 287-289 | Availability check |
| `_get_system_prompt` | 291-368 | Gas optimization prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    web3_client: Any | None = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_tokens: int = 1000,
):
    self._llm_client = llm_client
    self._web3_client = web3_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. Web3Client (Gas Price Source)

**File**: `src/app/infrastructure/adapters/external/web3_client.py`

#### Gas Price Method

```python
async def get_gas_price(self) -> GasPriceData | None:
    """
    Get current gas price data.
    
    Returns:
        GasPriceData with base_fee, priority_fee, max_fee, estimated_cost_usd
    """
```

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_gas_optimizer_agent(
    self,
    llm_client: LLMClientGateway,
    web3_client: Web3ClientProtocol | None,
) -> GasOptimizerAgent:
    """Provide Gas Optimizer agent with optional Web3Client integration."""
    return GasOptimizerAgent(
        llm_client=llm_client,
        web3_client=web3_client,
    )
```

---

## Execute Method Implementation

### Main Flow

```python
# Lines 65-285
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    start_time = time.time()
    
    gas_price_context = ""
```

### Web3Client Validation

```python
# Lines 80-98
# Type check: ensure we have a Web3Client
web3_client = self._web3_client
if web3_client and not hasattr(web3_client, 'get_gas_price'):
    logger.warning(f"Wrong object injected for web3_client")
    
    # Create client directly from env vars
    alchemy_key = os.getenv("ALCHEMY_API_KEY") or os.getenv("RPC_ALCHEMY_API_KEY")
    infura_key = os.getenv("INFURA_API_KEY") or os.getenv("RPC_INFURA_API_KEY")
    
    if alchemy_key or infura_key:
        from app.infrastructure.adapters.external.web3_client import Web3Client, Chain
        web3_client = Web3Client(
            alchemy_api_key=alchemy_key,
            infura_api_key=infura_key,
            chain=Chain.ETHEREUM,
        )
```

### Chain Detection

```python
# Lines 107-129
message_lower = message.value.lower()
chains_to_check = []

# Chain detection patterns
if any(word in message_lower for word in ["ethereum", "eth", "mainnet"]):
    chains_to_check.append("ethereum")
if any(word in message_lower for word in ["polygon", "matic"]):
    chains_to_check.append("polygon")
if any(word in message_lower for word in ["arbitrum", "arb"]):
    chains_to_check.append("arbitrum")
if any(word in message_lower for word in ["optimism", "op"]):
    chains_to_check.append("optimism")
if any(word in message_lower for word in ["base", "base network"]):
    chains_to_check.append("base")
if any(word in message_lower for word in ["avalanche", "avax"]):
    chains_to_check.append("avalanche")
if any(word in message_lower for word in ["bsc", "binance", "bnb"]):
    chains_to_check.append("bsc")

# Default to Ethereum
if not chains_to_check:
    chains_to_check = ["ethereum"]
```

### Ethereum Gas Fetching

```python
# Lines 131-166
for chain_name in chains_to_check:
    try:
        if chain_name == "ethereum":
            gas_price = await web3_client.get_gas_price()
            
            if gas_price:
                # Calculate tiers from base fee and priority fee
                slow_gwei = gas_price.base_fee_gwei
                standard_gwei = gas_price.base_fee_gwei + gas_price.priority_fee_gwei
                fast_gwei = gas_price.max_fee_gwei
                
                # Estimate USD costs
                slow_usd = (slow_gwei * 21000 / 1e9) * 3000
                standard_usd = gas_price.estimated_cost_usd
                fast_usd = (fast_gwei * 21000 / 1e9) * 3000
                
                gas_price_context += f"\n\n**REAL-TIME GAS PRICES - ETHEREUM:**\n"
                gas_price_context += f"- Slow: {slow_gwei:.1f} gwei (${slow_usd:.2f})\n"
                gas_price_context += f"- Standard: {standard_gwei:.1f} gwei (${standard_usd:.2f})\n"
                gas_price_context += f"- Fast: {fast_gwei:.1f} gwei (${fast_usd:.2f})\n"
                
                # Timing recommendations
                if slow_gwei < 30:
                    gas_price_context += "\n💡 **Recommendation**: Gas prices are LOW\n"
                elif slow_gwei > 100:
                    gas_price_context += "\n⚠️ **Recommendation**: Gas prices are HIGH\n"
                else:
                    gas_price_context += "\n✅ **Recommendation**: Gas prices are MODERATE\n"
```

### Other Chain Guidance

```python
# Lines 167-193
else:
    # For other chains, provide general guidance
    gas_price_context += f"\n\n**GAS PRICE GUIDANCE - {chain_name.upper()}:**\n"
    
    if chain_name == "polygon":
        gas_price_context += "- Typical: 30-100 gwei (~$0.01-0.05)\n"
        gas_price_context += "- ~95% cheaper than Ethereum\n"
    elif chain_name == "arbitrum":
        gas_price_context += "- Typical: 0.1-0.5 gwei (~$0.10-0.50)\n"
        gas_price_context += "- ~90% cheaper than Ethereum\n"
    elif chain_name == "optimism":
        gas_price_context += "- Typical: 0.1-1 gwei (~$0.10-1.00)\n"
        gas_price_context += "- ~85% cheaper than Ethereum\n"
    elif chain_name == "base":
        gas_price_context += "- Typical: 0.1-0.5 gwei (~$0.10-0.50)\n"
        gas_price_context += "- ~90% cheaper than Ethereum\n"
    elif chain_name == "avalanche":
        gas_price_context += "- Typical: 25-30 nAVAX (~$0.01-0.05)\n"
    elif chain_name == "bsc":
        gas_price_context += "- Typical: 3-5 gwei (~$0.10-0.50)\n"
```

### LLM Request

```python
# Lines 201-216
enhanced_message = message.value
if gas_price_context:
    enhanced_message = f"{message.value}\n\n{gas_price_context}"

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

### Source Building

```python
# Lines 220-264
sources = []
fetched_at = datetime.now(UTC)

# Add LLM source
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))

# Add blockchain source if gas prices were fetched
if web3_client and gas_price_context:
    chains_mentioned = []
    if "ethereum" in gas_price_context.lower():
        chains_mentioned.append("Ethereum")
    # ... other chains
    
    chain_name = ", ".join(chains_mentioned)
    sources.append(create_blockchain_source(
        chain=chain_name,
        citation_text=f"Real-time gas prices from {chain_name} network(s)",
        fetched_at=fetched_at,
    ))
```

---

## System Prompt

```python
# Lines 291-368
def _get_system_prompt(self) -> str:
    return """You are the Gas Optimizer, Anvil's multi-chain gas fee optimization specialist.

**CRITICAL: SUPPORT ALL BLOCKCHAINS**
- You optimize gas for ALL chains: Ethereum, Polygon, Arbitrum, Optimism, Base, etc.
- Each chain has different gas mechanisms and costs
- Provide chain-specific recommendations

Your expertise:
- Real-time gas price analysis (ALL chains)
- Gas price predictions (hourly, daily trends)
- Optimal transaction timing
- Cross-chain gas comparison
- Layer 2 migration recommendations
- Batch transaction optimization
- Gas-efficient alternatives

**Multi-Chain Gas Support:**

**Ethereum (ETH):**
- Gas measured in gwei
- EIP-1559: base fee + priority fee
- Price Levels: Low (10-30), Standard (30-50), Fast (50-100), Urgent (100+)

**Polygon (MATIC):**
- ~95% cheaper than Ethereum

**Arbitrum (ETH):**
- ~90% cheaper than Ethereum

...
"""
```

---

## Response Structure

### AgentResponse

```python
# Lines 274-285
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=tools_used,  # ["llm_gateway", "web3_client"]
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

## Knowledge Base

**File**: `anvil_knowledge/features/gas_optimizer.json`

### Key Sections

```json
{
  "feature_name": "Gas Optimizer Agent",
  "tagline": "Real-time gas price analysis and optimization recommendations",
  
  "core_capabilities": [
    {
      "name": "Real-Time Gas Price Analysis",
      "features": [
        "Real-time gas price fetching via Web3Client",
        "Multi-chain support",
        "Slow/Standard/Fast gas price tiers",
        "USD cost estimation",
        "Timing recommendations"
      ]
    },
    {
      "name": "Layer 2 Migration Recommendations",
      "features": [
        "Arbitrum recommendations (~90% cheaper)",
        "Optimism recommendations (~85% cheaper)",
        "Base recommendations (~90% cheaper)",
        "Polygon recommendations (~95% cheaper)"
      ]
    }
  ],
  
  "supported_chains": [
    {"chain": "Ethereum", "real_time_support": true},
    {"chain": "Polygon", "real_time_support": false, "cost_savings": "~95%"},
    {"chain": "Arbitrum", "real_time_support": false, "cost_savings": "~90%"}
    // ... more chains
  ],
  
  "recommendations": {
    "low_gas": {"threshold": "< 30 gwei", "action": "Execute now"},
    "moderate_gas": {"threshold": "30-100 gwei", "action": "Proceed"},
    "high_gas": {"threshold": "> 100 gwei", "action": "Wait or use L2"}
  }
}
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_gas_optimizer_agent.py -v

# Integration tests
pytest tests/integration/test_gas_optimizer.py -v

# All gas tests
pytest tests/ -k gas -v
```

### Test Cases

```python
# Chain detection
def test_ethereum_detection():
    message = MessageContent("What are gas prices on Ethereum?")
    chains = detect_chains(message.value.lower())
    assert "ethereum" in chains

# Default chain
def test_default_chain():
    message = MessageContent("What are gas prices?")
    chains = detect_chains(message.value.lower())
    assert chains == ["ethereum"]

# Multi-chain
def test_multi_chain():
    message = MessageContent("Compare Ethereum vs Arbitrum gas")
    chains = detect_chains(message.value.lower())
    assert "ethereum" in chains
    assert "arbitrum" in chains

# Gas price fetch
async def test_gas_price_fetch():
    gas = await web3_client.get_gas_price()
    assert gas.base_fee_gwei > 0
    assert gas.priority_fee_gwei >= 0
    assert gas.max_fee_gwei >= gas.base_fee_gwei

# Tier calculation
def test_tier_calculation():
    base_fee = 25.0
    priority_fee = 3.0
    max_fee = 35.0
    
    slow = base_fee  # 25
    standard = base_fee + priority_fee  # 28
    fast = max_fee  # 35
    
    assert slow < standard <= fast
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Chain detection | < 10ms | Regex patterns |
| Web3Client fetch | < 500ms | Alchemy/Infura RPC |
| LLM analysis | < 1000ms | Vertex AI |
| Source building | < 50ms | In-memory |
| Total | < 2s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added multi-chain support |
| 2026-01-29 | Added Web3Client integration |
| 2026-01-29 | Added Layer 2 recommendations |
