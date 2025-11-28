# Python Toon Specification

## 1. Strategic Overview (CTO Perspective)
**Python Toon** provides support for **Token-Oriented Object Notation (TOON)**. This is a specialized data format optimized for Large Language Models (LLMs). It significantly reduces token usage (30-60%) compared to JSON by removing redundant syntax.

In an AI-centric application like Anvil Backend, where we pay per token and latency is correlated with token count, adopting TOON for **Agent-to-Agent communication** and **Data Retrieval** (e.g., fetching large datasets for the agent to analyze) is a strategic cost and performance optimization.

## 2. Use Cases

### Primary: Context Injection
- **Scenario**: Injecting the user's last 100 transactions into the LLM context for analysis.
- **Execution**: Convert the transaction list to TOON format instead of JSON.
- **Benefit**: Reduces context window usage, saving cost and allowing more history to fit.

### Secondary: Structured Output
- **Scenario**: Agent returning a list of 50 potential yield farms.
- **Execution**: Instruct the LLM to respond in TOON format.
- **Benefit**: Faster generation (fewer tokens to generate) and lower latency for the user.

## 3. Architecture & Integration

### System Fit
TOON sits in the **Infrastructure Layer** as a serialization/deserialization utility, similar to `orjson`.

### Key Components
- `encode(value)`: Python dict -> TOON string.
- `decode(string)`: TOON string -> Python dict.

## 4. Implementation Examples

### Encoding Data for LLM Context
```python
from libs.python_toon import encode

transactions = [
    {"id": 1, "asset": "ETH", "amount": 1.5, "type": "SWAP"},
    {"id": 2, "asset": "USDC", "amount": 5000, "type": "FUND"},
    # ... 100 more items
]

# JSON would be heavy. TOON is compact.
context_str = encode(transactions)
# Output:
# [100,]{id,asset,amount,type}:
#   1,ETH,1.5,SWAP
#   2,USDC,5000,FUND
```

## 5. Integration Strategy
1.  **Adoption**: Use TOON specifically for *internal* prompts and *context building* where human readability is secondary to machine efficiency.
2.  **Prompt Engineering**: Update our System Prompts to understand and output TOON (e.g., "Output data in TOON format").
3.  **Wrapper**: Create a `Serializer` service in `src/app/application/common/serialization/` that defaults to JSON for frontend API but uses TOON for LLM context.
