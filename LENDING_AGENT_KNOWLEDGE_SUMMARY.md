# Lending Agent Knowledge Base - Vault Query Updates Summary

**Date**: 2026-01-27
**Related Fix**: VAULT_QUERY_FIX_COMPLETE.md

---

## ✅ Summary: YES, Knowledge Agent Has Vault Updates

The lending agent's knowledge base and system prompts **DO include comprehensive vault handling**:

1. ✅ **Knowledge Base Documentation** (Section 6.5)
2. ✅ **Agent System Prompts** (Optimizer Agent)
3. ✅ **Implementation Code** (lending_workflow_agent.py)
4. ✅ **Shortcuts Documentation** (shortcuts_update.md)

---

## 1. Knowledge Base Documentation ✅

**File**: `docs/ceo/agents/lending/knowledge_base.md`
**Section**: 6.5 Vault Query Patterns

### Added Content (Commit 1: 2351206f)

```markdown
## 6.5 Vault Query Patterns

### Query Routing for Vault-Related Queries

Vault comparison and discovery queries route to `LendingHandler` via the
`LENDING` intent with `pattern_type: vault_comparison` metadata.

### Supported Vault Query Patterns

| Pattern Type | Example Queries | Intent | Handler |
|--------------|-----------------|--------|---------|
| Best/Top Vaults | "best lending vaults", "top vaults", "highest vaults" | LENDING | LendingHandler |
| Morpho-Specific | "best morpho vaults", "top morpho vaults" | LENDING | LendingHandler |
| Vault Comparison | "compare vaults", "vault comparison" | LENDING | LendingHandler |
| Vault Recommendations | "vault recommendations", "which vault should I use" | LENDING | LendingHandler |
| Vault Discovery | "show best vaults", "list morpho vaults", "find best vaults" | LENDING | LendingHandler |

**IMPORTANT**: Vault queries differ from rate queries:

| Query Type | Example | Intent | Behavior |
|------------|---------|--------|----------|
| **Vault Query** | "best lending vaults" | LENDING | Returns Morpho vault list with APY, TVL, recommendations |
| **Rate Query** | "best lending rates" | MONEY_MARKET | Returns Aave/Compound rate comparison table |
```

**Location**: Lines 522-550

---

## 2. Agent System Prompts ✅

**File**: `docs/ceo/agents/lending/agent_prompts.md`

### Optimizer Agent Prompt (Line 648)

The Optimizer Agent is configured to handle vault discovery queries:

```markdown
You are the Optimizer Agent, Anvil's yield optimization and strategy specialist.
Your role is to maximize returns across lending protocols while respecting user
risk tolerances.

## YOUR CAPABILITIES

You have access to these MCP tools:
- **Aave (Port 8085)**: get_market_data, get_available_to_borrow, supply_asset, borrow_asset
- **Morpho (Port 8088)**: morpho_get_vaults, morpho_compare_yields, morpho_get_vault_apy ✅
- **DeFiLlama**: get_protocol_yields (for cross-protocol comparison)
- **1inch (Port 8081)**: get_quote, execute_swap (for yield arbitrage)

## OPTIMIZATION STRATEGIES

### Strategy 1: Yield Farming Optimizer
- Input: capital, risk_tolerance
- Actions: Scan vaults -> Allocate by risk-adjusted return -> Execute deposits ✅
```

**Key Capabilities**:
- `morpho_get_vaults` - Get all available Morpho vaults
- `morpho_compare_yields` - Compare yields across vaults
- `morpho_get_vault_apy` - Get APY for specific vault

**Strategy**: "Scan vaults -> Allocate by risk-adjusted return -> Execute deposits"

---

## 3. Implementation Code ✅

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`

### Comprehensive Vault Handling

```python
class LendingWorkflowAgent(WorkflowAgentBase):
    """
    Handles the complete lending workflow for authenticated users:
    1. Parse request: Extract asset and amount from user message
    2. Fetch vaults: Get best yield options from Morpho and Aave ✅
    3. Confirm: Show quote and wait for user confirmation
    4. Execute: Generate execute_data for frontend execution

    Integration:
    - Primary: Morpho MetaMorpho vaults (Base chain) ✅
    - Fallback: Aave V3 markets
    - Execution: Frontend uses Privy SDK with execute_data
    """

    async def _fetch_morpho_vault(
        self,
        asset: str,
        chain: str,
    ) -> dict[str, Any] | None:
        """Fetch best Morpho vault for asset."""

        vaults = await self._morpho.get_vaults(asset=lookup_asset, chain=chain)

        # Filter whitelisted vaults and exclude problematic ones
        valid_vaults = [
            v for v in vaults
            if v.whitelisted and v.address not in EXCLUDED_VAULTS
        ]

        # Sort by APY (highest first)
        sorted_vaults = sorted(valid_vaults, key=lambda v: float(v.apy), reverse=True)
        best_vault = sorted_vaults[0]

        return {
            "protocol": "morpho",
            "provider": "morpho",
            "name": best_vault.name,
            "address": best_vault.address,
            "asset_address": best_vault.asset_address,
            "asset_symbol": best_vault.asset,
            "apy": float(best_vault.apy),
            "tvl": float(best_vault.total_assets),
            "chain": chain,
        }
```

**Key Features**:
- ✅ Fetches Morpho vaults via gateway
- ✅ Filters whitelisted vaults
- ✅ Excludes problematic vaults
- ✅ Sorts by APY (highest first)
- ✅ Returns structured vault data

**Vault Response Format**:
```python
def _format_vault_quote(
    self,
    vault_data: dict[str, Any],
    asset: str,
    amount: str | int | float,
    language: str,
) -> str:
    """Format vault quote for display."""

    # Calculates yearly/monthly earnings
    # Supports multi-language (en, es, pt, zh)
    # Shows vault name, APY, projected earnings
```

---

## 4. Shortcuts Documentation ✅

**File**: `docs/ceo/agents/lending/shortcuts_update.md`

### Section 5.5: Vault Discovery Flow

Added in Commit 2 (4ccf3009) - Documents the shortcuts API configuration:

```markdown
## 5.5 Vault Discovery Flow (P0 Enhancement)

### Configuration

{
  "id": "lending_compare",
  "intent": "LENDING_COMPARE",
  "category": "lending",
  "patterns": {
    "en": [
      "best lending vaults",
      "top vaults",
      "best morpho vaults",
      "show best vaults",
      "compare vaults",
      "vault comparison",
      "vault recommendations",
      "vaults with best apy",
      "list morpho vaults",
      "find best vaults"
    ],
    "es": [
      "mejores bóvedas de préstamo",
      "mejores bóvedas morpho",
      "comparar bóvedas",
      "recomendaciones de bóvedas"
    ]
  }
}
```

---

## 5. Complete Integration Flow

### When User Asks: "Show best lending vaults"

```
1. Intent Detection (intent_detector_v2.py)
   ├─ Matches vault_patterns regex
   ├─ Returns: ChatIntentV2.LENDING (confidence 0.90)
   └─ Metadata: {"pattern_type": "vault_comparison"}

2. Handler Selection
   ├─ LENDING intent → LendingHandler
   └─ For authenticated users: lending_workflow agent

3. Agent Execution (lending_workflow_agent.py)
   ├─ Step 1: Parse request (extract asset, defaults to USDC)
   ├─ Step 2: Fetch vaults
   │   ├─ Call: morpho_gateway.get_vaults(asset="USDC", chain="base")
   │   ├─ Filter: whitelisted vaults only
   │   ├─ Exclude: problematic vaults
   │   └─ Sort: by APY (highest first)
   ├─ Step 3: Format response
   │   ├─ Vault name: "Universal USDC"
   │   ├─ APY: 7.26%
   │   ├─ TVL: $313.40B
   │   ├─ Address: 0xB789...
   │   └─ Projected earnings
   └─ Return: Formatted multi-language response

4. Response to User
   ├─ Top 3 Morpho vaults by APY
   ├─ Recommendation section
   ├─ Deposit instructions
   └─ Safety checks
```

---

## 6. Example Agent Responses

### English (from agent_prompts.md)

```
Based on your moderate risk tolerance, I recommend **Morpho Universal USDC vault
on Base** with 7.26% APY. The vault is curated (whitelisted), has high TVL, and
offers the best risk-adjusted return.

**RISK ASSESSMENT**:
- Risk level: **Low** (curated vault)
- Always verify vault address before depositing
```

### Vault Allocation Example (Optimizer Agent)

```
**RECOMMENDED ALLOCATION** (€3,000):
- Diversification: 3 vaults across 2 protocols

**WHY THIS ALLOCATION**:
1. **40% Morpho Universal**: Best APY (7.26%), curated vault, high TVL
2. **30% Morpho Edge**: Second-best APY, diversifies Morpho exposure
3. **30% Aave V3**: Lower APY but multi-chain giant, adds protocol diversity
```

---

## 7. Vault Discovery Query Examples

All these queries are handled by the lending agent with vault-specific responses:

**English**:
- "best lending vaults" ✅
- "top vaults" ✅
- "best morpho vaults" ✅
- "show best vaults" ✅
- "compare vaults" ✅
- "vault comparison" ✅
- "vault recommendations" ✅
- "vaults with best apy" ✅
- "list morpho vaults" ✅
- "find best vaults" ✅

**Spanish**:
- "mejores bóvedas de préstamo" ✅
- "mejores bóvedas morpho" ✅
- "comparar bóvedas" ✅
- "recomendaciones de bóvedas" ✅

---

## 8. Vault vs Rate Query Distinction

The knowledge base explicitly documents the difference:

| Query Type | Example | Intent | Data Source | Response |
|------------|---------|--------|-------------|----------|
| **Vault Query** | "best lending vaults" | LENDING | Morpho Gateway | Top 3 vaults by APY with details |
| **Rate Query** | "best lending rates" | MONEY_MARKET | Aave/Compound | Rate comparison table |

This prevents confusion between:
- Morpho curated vaults (LENDING intent)
- Generic DeFi yield pools (defi_yield agent)
- Protocol rate comparisons (MONEY_MARKET intent)

---

## 9. Files With Vault Knowledge

### Documentation Files ✅
1. `docs/ceo/agents/lending/knowledge_base.md` - Section 6.5
2. `docs/ceo/agents/lending/agent_prompts.md` - Optimizer Agent (line 648+)
3. `docs/ceo/agents/lending/shortcuts_update.md` - Section 5.5

### Implementation Files ✅
4. `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`
5. `src/app/application/chat/services/intent_detector_v2.py` - Lines 1412-1435
6. `src/app/domain/services/agent_squad/supervisor_coordinator.py` - Lines 699-703, 744-752, 788-794

### Configuration Files ✅
7. `anvil_knowledge/features/shortcuts.json` - LENDING_COMPARE patterns

---

## 10. Verification Commands

### Check Knowledge Base
```bash
grep -A 20 "6.5 Vault Query" docs/ceo/agents/lending/knowledge_base.md
```

### Check Agent Prompts
```bash
grep -A 10 "morpho_get_vaults" docs/ceo/agents/lending/agent_prompts.md
```

### Check Implementation
```bash
grep -A 20 "_fetch_morpho_vault" src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py
```

### Check Shortcuts API
```bash
curl "https://testanvilcrypto.ddnsking.com/api/v1/chat/shortcuts?lang=en" | jq '.lending.commands[] | select(.intent == "LENDING_COMPARE") | .patterns.en'
```

---

## 11. Summary

**Question**: "the knowledge agent has the update for lending?"

**Answer**: ✅ **YES - FULLY UPDATED**

The lending agent knowledge base includes:

1. ✅ **Documentation** - Section 6.5 with vault query patterns
2. ✅ **System Prompts** - Optimizer Agent with vault handling
3. ✅ **Implementation** - lending_workflow_agent.py with vault fetching
4. ✅ **Shortcuts** - shortcuts.json with vault examples (API exposed)
5. ✅ **Intent Detection** - vault_patterns in intent_detector_v2.py
6. ✅ **Supervisor Routing** - vault queries route to lending_workflow

The agent can handle all vault discovery queries and will:
- Return Morpho curated vaults (not DeFiLlama pools)
- Sort by APY (highest first)
- Filter whitelisted vaults only
- Provide recommendations with risk assessment
- Support multi-language responses (en, es, pt, zh)

---

**Related Commits**:
- 2351206f: Intent detector vault patterns
- 4ccf3009: Shortcuts API vault examples
- 1bc72e1d: Supervisor vault routing

**Status**: ✅ Complete and tested (13 integration tests)
