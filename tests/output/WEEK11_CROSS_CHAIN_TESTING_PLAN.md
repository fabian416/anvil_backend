# Week 11: Cross-Chain Testing Plan

**Date**: 2026-01-15
**Priority**: P2
**Goal**: Implement comprehensive cross-chain testing (5-7 tests)
**Scope**: Ethereum → Base swaps, Bridge integration, Multi-chain validation

---

## Current State Analysis

### Existing Bridge Tests (Agent Squad)

**File**: `tests/integration/chat/test_agent_squad_ultra_hunter_full.py`

**Test 1**: `squad_bridge_001` - Bridge agent - cross-chain transfer
- **Input**: "Bridge 100 USDC from Ethereum to Arbitrum"
- **Coverage**: Basic bridge transfer routing
- **Agent**: BridgeCrosschainAgentAxelar

**Test 2**: `squad_bridge_002` - Bridge agent - best bridge route
- **Input**: "Find the cheapest bridge route from Polygon to Optimism"
- **Coverage**: Bridge route comparison/optimization
- **Agent**: BridgeCrosschainAgentAxelar

### Gaps Identified

1. ❌ **No Ethereum → Base swaps** (P2 requirement)
2. ❌ **No multi-chain balance validation**
3. ❌ **No cross-chain error handling tests**
4. ❌ **No gas estimation across chains**
5. ❌ **No bridge security validation**
6. ❌ **No L2 → L2 direct bridging tests**
7. ❌ **No bridge time estimation tests**

---

## Test Scenarios (5-7 tests)

### Test 1: Ethereum → Base Token Swap ⭐ (P2 Required)
**Scenario**: User wants to swap USDC from Ethereum to Base

```python
{
    "id": "cross_chain_001",
    "description": "Ethereum to Base USDC swap with bridge",
    "input": {"content": "Swap 500 USDC from Ethereum to Base"},
    "expected_routing": {
        "intent": "swap",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "task_type": "cross_chain_swap",
        "source_chain": "ethereum",
        "dest_chain": "base",
        "token": "USDC",
        "amount": 500,
    },
    "expected_response_contains": [
        "bridge",
        "gas",
        "estimate",
        "time",
        "base",
    ],
}
```

**Validates**:
- Cross-chain swap routing detection
- Bridge protocol selection (Axelar, LayerZero, native)
- Gas cost estimation on both chains
- Time estimation (5min - 7 days)
- Slippage protection

---

### Test 2: Multi-Chain Balance Validation
**Scenario**: User wants to check balances across multiple chains

```python
{
    "id": "cross_chain_002",
    "description": "Multi-chain balance check",
    "input": {"content": "Show my USDC balance on Ethereum, Arbitrum, and Base"},
    "expected_routing": {
        "intent": "check_balance",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "chains": ["ethereum", "arbitrum", "base"],
        "token": "USDC",
    },
    "expected_response_contains": [
        "ethereum",
        "arbitrum",
        "base",
        "usdc",
        "total",
    ],
}
```

**Validates**:
- Multi-chain RPC integration
- Balance aggregation across chains
- Chain-specific token addresses
- Total portfolio calculation

---

### Test 3: L2 → L2 Direct Bridge (Optimistic Rollup)
**Scenario**: User wants to bridge between two L2s without going through L1

```python
{
    "id": "cross_chain_003",
    "description": "L2 to L2 direct bridge (Arbitrum to Optimism)",
    "input": {"content": "Bridge 1000 USDC from Arbitrum to Optimism using fastest route"},
    "expected_routing": {
        "intent": "specialist_task",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "task_type": "l2_to_l2_bridge",
        "bridge_type": "direct",  # Hop Protocol, not via L1
    },
    "expected_response_contains": [
        "hop protocol",  # or other L2-L2 bridge
        "faster",
        "cheaper",
        "optimism",
        "arbitrum",
    ],
}
```

**Validates**:
- L2-L2 direct bridging support
- Route optimization (L2-L2 vs L1 intermediate)
- Bridge protocol selection (Hop, Connext, Across)
- Cost/time tradeoffs

---

### Test 4: Cross-Chain Gas Estimation
**Scenario**: User wants to understand total costs before bridging

```python
{
    "id": "cross_chain_004",
    "description": "Cross-chain gas cost estimation",
    "input": {"content": "How much will it cost to bridge 5000 USDC from Ethereum to Polygon?"},
    "expected_routing": {
        "intent": "estimate_gas",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "source_chain": "ethereum",
        "dest_chain": "polygon",
        "operation": "bridge",
    },
    "expected_response_contains": [
        "gas",
        "ethereum",
        "polygon",
        "cost",
        "fee",
        "usd",
    ],
}
```

**Validates**:
- Gas estimation on source chain
- Bridge fee calculation
- Destination chain gas estimation
- Total cost breakdown in USD
- Fee comparison across bridges

---

### Test 5: Bridge Security Validation
**Scenario**: User concerned about bridge security after recent exploits

```python
{
    "id": "cross_chain_005",
    "description": "Bridge security risk assessment",
    "input": {"content": "Is it safe to bridge large amounts from Ethereum to BSC? Any recent exploits?"},
    "expected_routing": {
        "intent": "security_check",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "security_check": True,
        "source_chain": "ethereum",
        "dest_chain": "bsc",
    },
    "expected_response_contains": [
        "security",
        "audit",
        "risk",
        "bridge",
        "recommendation",
    ],
}
```

**Validates**:
- Bridge security scoring
- Recent exploit detection
- Audit status checking
- Risk-based recommendations
- Alternative safer routes

---

### Test 6: Cross-Chain Error Handling (Insufficient Gas)
**Scenario**: User tries to bridge but lacks gas on destination chain

```python
{
    "id": "cross_chain_006",
    "description": "Cross-chain bridge error - insufficient destination gas",
    "input": {"content": "Bridge 1000 USDC from Polygon to Ethereum"},
    "expected_routing": {
        "intent": "specialist_task",
        "confidence_min": 0.7,
    },
    "user_context": {
        "balances": {
            "polygon": {"USDC": 1000, "MATIC": 0},  # No gas!
            "ethereum": {"ETH": 0},  # No gas on dest either
        }
    },
    "expected_response_contains": [
        "gas",
        "eth",
        "insufficient",
        "recommend",
        "matic",
    ],
}
```

**Validates**:
- Pre-flight gas validation
- Clear error messaging
- Actionable recommendations (buy gas tokens)
- Multi-chain gas requirements

---

### Test 7: Bridge Time Estimation with Urgency
**Scenario**: User needs fast bridging for time-sensitive operation

```python
{
    "id": "cross_chain_007",
    "description": "Fast bridge route selection with time priority",
    "input": {"content": "I need to bridge 500 USDC from Ethereum to Arbitrum ASAP, what's the fastest option?"},
    "expected_routing": {
        "intent": "specialist_task",
        "confidence_min": 0.7,
    },
    "expected_enrichment": {
        "priority": "speed",  # vs "cost"
        "source_chain": "ethereum",
        "dest_chain": "arbitrum",
    },
    "expected_response_contains": [
        "fast",
        "minutes",
        "arbitrum native bridge",  # Fast: ~10-15 min
        "time",
        "expensive",  # Trade-off: speed costs more
    ],
}
```

**Validates**:
- Time-priority route selection
- Bridge speed comparison
- Cost vs speed tradeoffs
- Realistic time estimates (5min - 7 days)

---

## Implementation Plan

### Phase 1: Test File Creation (1 hour)
- Create `tests/integration/chat/test_cross_chain_comprehensive.py`
- Set up fixtures for multi-chain testing
- Mock bridge clients (Axelar, LayerZero, Hop)

### Phase 2: Test Implementation (3 hours)
- Implement 5-7 test scenarios
- Add expected response validation
- Add multi-chain context mocking

### Phase 3: Integration with Comprehensive Runner (30 min)
- Add to `scripts/run_comprehensive_integration_tests.py`
- Update advanced test mode
- Add to CI/CD pipeline

### Phase 4: Documentation (1 hour)
- Document test coverage
- Update Week 11 summary
- Add cross-chain testing guide

**Total Estimated Time**: 5-6 hours

---

## Success Criteria

✅ **Coverage**:
- Minimum 5 tests, target 7 tests
- All P2 requirements covered (ETH→Base, bridge integration, multi-chain validation)

✅ **Quality**:
- All tests passing (100%)
- Clear failure messages
- Realistic mock data

✅ **Integration**:
- Tests added to comprehensive runner
- CSV export working
- Documentation complete

✅ **Value**:
- Validates cross-chain user flows
- Catches bridge routing issues
- Tests multi-chain balance aggregation
- Validates gas estimation accuracy

---

## Technical Implementation Notes

### Required Mocks

**1. Multi-Chain RPC Responses**:
```python
mock_chain_balances = {
    "ethereum": {"USDC": Decimal("1000.50")},
    "arbitrum": {"USDC": Decimal("500.25")},
    "base": {"USDC": Decimal("250.75")},
}
```

**2. Bridge Route Responses**:
```python
mock_bridge_routes = [
    {
        "protocol": "Axelar",
        "time_estimate_minutes": 15,
        "gas_cost_usd": Decimal("5.50"),
        "security_score": 95,
    },
    {
        "protocol": "Native Bridge",
        "time_estimate_minutes": 10,
        "gas_cost_usd": Decimal("12.00"),
        "security_score": 100,
    },
]
```

**3. Gas Estimation Responses**:
```python
mock_gas_estimates = {
    "source_chain_gas": {"gwei": 25, "usd": Decimal("3.50")},
    "bridge_fee": {"bps": 10, "usd": Decimal("0.50")},
    "dest_chain_gas": {"gwei": 0.5, "usd": Decimal("0.10")},
    "total_usd": Decimal("4.10"),
}
```

### Test Organization

```
tests/integration/chat/
├── test_cross_chain_comprehensive.py       # NEW - 7 tests
├── test_agent_squad_ultra_hunter_full.py   # EXISTING - 2 bridge tests
└── conftest.py                             # Shared fixtures
```

---

## Dependencies

### External Services (Mocked in Tests)
- Axelar API (bridge routes, gas estimation)
- LayerZero API (omnichain messaging)
- Multi-chain RPC endpoints (Alchemy, Infura)

### Internal Components
- `BridgeCrosschainAgentAxelar` (agent)
- `UnifiedChatHandler` (routing)
- `IntentDetection` (intent classification)
- Bridge domain entities (AxelarTransfer, BridgeRoute)

### Test Infrastructure
- `MockLLMClient` (for agent responses)
- `MockAxelarClient` (for bridge APIs)
- `MockRPCProvider` (for multi-chain balances)

---

## Risk Assessment

### Low Risk ✅
- Agent routing (already tested in Agent Squad)
- Mock setup (standard patterns established)
- Test file creation (template exists)

### Medium Risk ⚠️
- Multi-chain balance mocking (complex data structure)
- Gas estimation accuracy (multiple chains)
- Bridge protocol selection logic

### Mitigation
- Start with simpler tests (routing)
- Use existing Agent Squad patterns
- Validate against real bridge API responses
- Add detailed test documentation

---

## References

- **Agent Squad Tests**: `tests/integration/chat/test_agent_squad_ultra_hunter_full.py`
- **Bridge Agent**: `src/app/infrastructure/adapters/agent_squad/agents/advanced/bridge_crosschain_agent_axelar.py`
- **Bridge Domain**: `src/app/domain/entities/bridge/`, `src/app/domain/value_objects/bridge/`
- **Week 9 Summary**: `tests/output/WEEK9_FINAL_SUMMARY.md` (P2 requirements)
- **Week 10 Summary**: `tests/output/WEEK10_P2_SUMMARY.md`

---

**Next Steps**:
1. ✅ Analyze existing bridge functionality (DONE)
2. ✅ Design 7 comprehensive test scenarios (DONE)
3. ⏳ Implement test file (IN PROGRESS)
4. ⏳ Add to comprehensive runner
5. ⏳ Document results

**Status**: Planning Complete - Ready for Implementation
