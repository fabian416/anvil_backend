# Agent API Integration Priorities

## Executive Summary

**Current State**: Only 2/18 agents use real-time APIs (HunterAI: CoinGecko, Research: Perplexity)
**Gap**: 16 agents rely on LLM knowledge (may be outdated/inaccurate)
**Impact**: Users get estimates instead of real data, reduced trust

## Priority Matrix

### 🔴 Critical (High Impact, Low Effort)

1. **DefiYieldAgent + DeFiLlama**
   - **Impact**: Real APY data (currently LLM estimates)
   - **Effort**: Low (client exists, just needs injection)
   - **ROI**: Very High - Users see actual yields, not guesses

2. **PortfolioAgent + CoinGecko**
   - **Impact**: Real-time token prices for portfolio valuation
   - **Effort**: Low (CoinGecko already used by HunterAI)
   - **ROI**: High - Accurate portfolio values

3. **GasOptimizerAgent + Web3Client**
   - **Impact**: Real-time gas prices
   - **Effort**: Low (Web3Client exists)
   - **ROI**: High - Accurate gas optimization

### 🟡 High Priority (High Impact, Medium Effort)

4. **DefiYieldAgent + Protocol APIs (Aave, Morpho, Compound)**
   - **Impact**: Real lending rates from protocols
   - **Effort**: Medium (inject 3 adapters)
   - **ROI**: High - Protocol-specific rates

5. **RiskAnalyzerAgent + DeFiLlama + Protocol APIs**
   - **Impact**: Real protocol risk scores
   - **Effort**: Medium (multiple APIs)
   - **ROI**: High - Accurate risk assessment

6. **ExecutionAgent + OneInch**
   - **Impact**: Real swap quotes before execution
   - **Effort**: Medium (OneInch client exists)
   - **ROI**: Medium - Better UX

### 🟢 Medium Priority (Medium Impact, Variable Effort)

7. **PortfolioAgent + MPT Calculator**
   - **Impact**: Real mathematical optimization
   - **Effort**: High (requires scipy.optimize)
   - **ROI**: Medium - Better than LLM estimates

8. **TaxOptimizerAgent + Transaction History**
   - **Impact**: Real capital gains calculations
   - **Effort**: Medium (database integration)
   - **ROI**: Medium - Accurate tax data

## Recommended Implementation Order

### Week 1: Quick Wins (Low Effort, High Impact)
1. DefiYieldAgent + DeFiLlama
2. PortfolioAgent + CoinGecko
3. GasOptimizerAgent + Web3Client

### Week 2: Protocol Integrations
4. DefiYieldAgent + Aave/Morpho/Compound
5. RiskAnalyzerAgent + DeFiLlama
6. ExecutionAgent + OneInch

### Week 3: Advanced Features
7. PortfolioAgent + MPT Calculator
8. RiskAnalyzerAgent + Protocol APIs

## Implementation Pattern

All integrations follow the same pattern:

```python
# 1. Inject client in __init__
def __init__(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: DefiLlamaClient | None = None,  # NEW
    ...
):
    self._defi_llama_client = defi_llama_client

# 2. Fetch data in execute()
if self._defi_llama_client:
    yields = await self._defi_llama_client.get_protocol_yields()
    # Add to prompt context

# 3. Update IOC provider
@provide
def provide_defi_yield_agent(
    self,
    llm_client: LLMClientGateway,
    defi_llama_client: DefiLlamaClient | None,  # NEW
) -> DefiYieldAgent:
    return DefiYieldAgent(
        llm_client=llm_client,
        defi_llama_client=defi_llama_client,  # NEW
    )
```

## Success Metrics

- **Accuracy**: Real data vs LLM estimates
- **User Trust**: Actual numbers from protocols
- **Response Quality**: More specific, actionable recommendations
- **Reduced Hallucination**: Less LLM guessing
