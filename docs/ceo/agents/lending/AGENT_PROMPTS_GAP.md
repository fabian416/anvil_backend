# Lending Agent Prompts Gap Analysis

**Version**: 1.0
**Date**: January 27, 2026
**Status**: Gap Analysis
**Author**: AI Analysis

---

## Executive Summary

This document provides a comprehensive gap analysis between the specified lending agent prompts and the current implementation. The analysis covers:

1. Agent configuration inventory and prompt quality
2. Prompt engineering gaps with temperature and feature comparisons
3. Knowledge base completeness
4. Shortcuts implementation status
5. **CRITICAL**: User approval and safety requirements in prompts

---

## 1. Current Agent Configuration Inventory

### 1.1 Existing Lending-Related Agents

| Agent | File Location | Status | Purpose |
|-------|---------------|--------|---------|
| LendingWorkflowAgent | `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py` | **EXISTS** | Multi-step deposit workflow (Morpho/Aave) |
| LendingBorrowingAgent | `src/app/infrastructure/adapters/agent_squad/agents/advanced/lending_borrowing_agent_aave.py` | **EXISTS** | Aave-based borrowing (legacy) |
| ExecutionAgentPrivy | `src/app/infrastructure/adapters/agent_squad/agents/execution_agent_privy.py` | **EXISTS** | Transaction execution with Privy wallets |
| DeFiYieldAgent | `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent.py` | **EXISTS** | Yield farming recommendations |
| RiskAnalyzerAgent | `src/app/infrastructure/adapters/agent_squad/agents/risk_analyzer_agent.py` | **EXISTS** | Risk assessment |

### 1.2 Missing Agents (From Specification)

| Specified Agent | Status | Gap Description |
|-----------------|--------|-----------------|
| **Market Scanner Agent** | **MISSING** | No dedicated agent for lending rate scanning/comparison |
| **Risk Guardian Agent** | **PARTIAL** | RiskAnalyzerAgent exists but lacks lending-specific health factor monitoring |
| **Executor Agent (Lending)** | **PARTIAL** | ExecutionAgentPrivy exists but not specialized for lending operations |
| **Optimizer Agent** | **PARTIAL** | DeFiYieldAgent exists but lacks cross-protocol optimization |

### 1.3 Current Prompt Quality Assessment

**LendingWorkflowAgent** - Quality: **GOOD**
- Multi-language support (en, es, pt, zh)
- User context awareness (balance, portfolio state)
- APY display and comparison
- Step-by-step workflow handling
- **Missing**: Chain-of-thought reasoning, few-shot examples in prompts

**ExecutionAgentPrivy** - Quality: **MODERATE**
- Safety features documented (limits, 2FA, confirmation)
- Temperature: 0.1 (correct for precision)
- **Issue**: Generic prompt, not specialized for lending
- **Missing**: Lending-specific chain-of-thought, health factor checks

---

## 2. Prompt Engineering Gap Matrix

### 2.1 Temperature Settings Comparison

| Agent | Specified Temp | Current Temp | Gap | Impact |
|-------|----------------|--------------|-----|--------|
| Market Scanner | 0.3 | N/A (missing) | **MISSING AGENT** | No factual market data responses |
| Risk Guardian | 0.2 | 0.7* (default) | **-0.5 GAP** | Responses too creative for safety-critical |
| Executor | 0.1 | 0.1 | **MATCH** | Correct for precision |
| Optimizer | 0.4 | 0.7* (default) | **-0.3 GAP** | Too creative for strategies |

*Note: Default temperature in `agent_squad.py` is 0.7; most agents inherit this default.

### 2.2 Feature Comparison Matrix

| Feature | Specified | Current | Gap |
|---------|-----------|---------|-----|
| **Few-Shot Examples** | Yes (2-3 per agent) | **NO** | Major gap - prompts lack examples |
| **Chain-of-Thought** | Yes (explicit reasoning) | **PARTIAL** | Some workflows have steps, not COT |
| **Safety Checks Embedded** | Yes (explicit in prompts) | **PARTIAL** | Balance checks exist, not in prompts |
| **User Context Variables** | Yes (template format) | **YES** | LendingWorkflowAgent uses UserContext |
| **Output Format Specification** | Yes (markdown tables) | **YES** | Good table formatting |
| **Error Handling** | Yes (fallback behaviors) | **PARTIAL** | Some fallbacks, not systematic |
| **MCP Tool References** | Yes (ports in prompts) | **NO** | Prompts don't reference MCP ports |
| **Protocol Comparison Knowledge** | Yes (Aave vs Morpho) | **PARTIAL** | Knowledge exists but not in prompts |
| **Health Factor Classification** | Yes (color-coded ranges) | **NO** | Not implemented |

### 2.3 Prompt Structure Gaps

**Current LendingWorkflowAgent Prompt Issues:**

```
Current State:
- Inline response formatting in Python code
- Multi-language strings hardcoded
- No system prompt with agent identity
- No explicit tool capabilities listed
- No chain-of-thought instruction

Specified State:
- System prompt with agent role
- Tool capabilities section (MCP ports)
- User context template block
- Chain-of-thought reasoning chain
- Few-shot examples section
- Error handling section
```

---

## 3. Knowledge Base Gaps

### 3.1 Current Knowledge Base Content

| File | Content | Quality |
|------|---------|---------|
| `anvil_knowledge/features/lending_morpho.json` | Morpho vault discovery, yield comparison, position management | **GOOD** |
| `anvil_knowledge/features/risk_analyzer.json` | Protocol risk assessment | **MODERATE** |
| `anvil_knowledge/features/shortcuts.json` | Command patterns | **NO LENDING** |

### 3.2 Protocol Comparison Knowledge

| Knowledge Area | Specified | Current | Gap |
|----------------|-----------|---------|-----|
| Aave vs Morpho comparison | **YES** (detailed JSON) | **PARTIAL** | Basic info in lending_morpho.json |
| TVL comparison | Yes | No | Missing TVL comparison data |
| Chain support comparison | Yes | Partial | Only Morpho chains documented |
| Feature comparison (flash loans, E-mode) | Yes | No | Missing advanced features |
| Supply APY ranges | Yes | No | No APY range data |
| MCP tool mappings | Yes | No | No port/tool documentation |

### 3.3 Risk Classification Knowledge

| Risk Knowledge | Specified | Current | Gap |
|----------------|-----------|---------|-----|
| LTV risk classification (6 levels) | **YES** | **NO** | **MISSING** - Critical gap |
| Health factor ranges (5 levels) | **YES** | **NO** | **MISSING** - Critical gap |
| Color-coded status | Yes | No | Not implemented |
| Liquidation thresholds by asset | Yes | No | Missing asset-specific data |
| Price drop tolerance % | Yes | No | Missing calculation reference |

### 3.4 Multi-Language Terminology

| Language | Specified | Current | Gap |
|----------|-----------|---------|-----|
| English | Yes | Yes | Match |
| Spanish | Yes | Yes | Match |
| Portuguese | Yes | Yes | Match |
| Chinese | Yes | Yes | Match |
| **Lending vs Borrowing terminology** | **CRITICAL** | **PRESENT** | Good - lending_morpho.json has warnings |

---

## 4. Shortcuts Gap Analysis

### 4.1 Current Shortcuts Status

**Current `shortcuts.json` contains:**
- Trading & Swaps (Hyperliquid Spot)
- Price queries
- Market Intelligence (Hunter AI)
- DeFi Automation (ULTRA)
- Protocol Research
- Portfolio Management
- General Conversation

**MISSING: Lending shortcuts category entirely**

### 4.2 Specified vs Current Shortcuts

| Shortcut Intent | Specified | Current Status | Gap |
|-----------------|-----------|----------------|-----|
| `LENDING_HEALTH_CHECK` | Yes | **MISSING** | Not in shortcuts.json |
| `LENDING_SUPPLY` | Yes | **MISSING** | Not in shortcuts.json |
| `LENDING_BORROW` | Yes | **MISSING** | Not in shortcuts.json |
| `LENDING_LOOP` | Yes | **MISSING** | Not in shortcuts.json |
| `LENDING_COMPARE` | Yes | **MISSING** | Not in shortcuts.json |
| `LENDING_POSITION` | Yes | **MISSING** | Not in shortcuts.json |

### 4.3 Intent Classifier Mapping

**Current `intent_classifier.py` mappings:**
```python
"borrow_assets": AgentType.LENDING_BORROWING,
"leverage_position": AgentType.LENDING_BORROWING,
"find_yield": AgentType.DEFI_YIELD,
"yield_farming": AgentType.DEFI_YIELD,
```

**Missing mappings for:**
- `LENDING_HEALTH_CHECK`
- `LENDING_SUPPLY`
- `LENDING_LOOP`
- `LENDING_COMPARE`
- `LENDING_POSITION`

### 4.4 Pattern Matching Quality

| Aspect | Specified | Current | Gap |
|--------|-----------|---------|-----|
| Multi-language patterns | Yes (en, es, pt, zh) | No | Only English in intent classifier |
| Parameter extraction | Yes (amount, asset, protocol) | Partial | LendingWorkflowAgent extracts params |
| Balance check integration | Yes | Yes | LendingWorkflowAgent checks balance |
| Agent routing config | Yes | Partial | Basic routing exists |

---

## 5. User Approval Prompt Requirements - CRITICAL

### 5.1 Current State Analysis

**ExecutionAgentPrivy Safety Features:**
```python
# From execution_agent_privy.py line 36-42
"""
Safety Features:
- Transaction limits (max $10k by default)
- 2FA requirement
- User confirmation required    # <-- DOCUMENTED
- Simulation before execution
"""
```

**Response Metadata:**
```python
metadata={
    "requires_confirmation": True,  # <-- CORRECT
}
```

**Current Prompt Response (line 424-437):**
```
**Next Steps:**
1. Review the quote above
2. Confirm the swap details
3. Sign the transaction with your wallet
4. Transaction will be submitted to the blockchain

**Safety Features:**
- Transaction limits: Max $10k per transaction
- Slippage protection: 1% default
- Gas estimation included
- Pre-flight simulation before execution

Would you like to proceed with this swap?
```

### 5.2 Gap Assessment for User Approval

| Requirement | Specified | Current | Status |
|-------------|-----------|---------|--------|
| "User approval required" in prompt | **YES** | **PARTIAL** | Says "confirm" but not explicit "approval" |
| Privy "execute" field usage | **YES** | **PARTIAL** | `execute_data` generated but not shown in prompts |
| No batch/automatic execution | **YES** | **YES** | No auto-execution logic |
| Safety checks in prompts | **YES** | **YES** | Limits and simulation mentioned |
| Explicit "sign transaction" language | **YES** | **YES** | "Sign the transaction with your wallet" |

### 5.3 CRITICAL Missing Elements

**1. LendingWorkflowAgent Missing User Approval Language:**

Current `_format_vault_quote` (line 1243-1256):
```python
**Ready to deposit?**
Reply "yes" to confirm or "cancel" to abort.
```

**Should Include:**
```
IMPORTANT: This action requires your wallet signature.
No funds will be moved without your explicit approval.
Reply "yes" to proceed to wallet signing, or "cancel" to abort.
```

**2. Health Factor Check Before Borrow/Withdraw - MISSING:**

No prompt-level health factor validation for borrow/withdraw operations that could cause liquidation.

**3. Multi-Signature Warning for Loop Strategy - MISSING:**

Current LendingWorkflowAgent has no loop strategy implementation.
Specified prompts require:
```
**EXECUTION REQUIREMENTS**:
- **4 separate signatures** (one per iteration)
- Must monitor position actively
```

### 5.4 Privy Integration Analysis

**Current State (from lending_workflow_agent.py):**
```python
# execute_data is built and returned
state.execute_data = self._build_deposit_execute_data(
    vault_data=vault_data,
    amount=amount,
    chain=chain,
)
```

**Execute Data Structure:**
```python
{
    "action_type": "deposit",
    "provider": "morpho",
    "vault_address": "...",
    "asset_address": "...",
    "amount": "...",
    # ... other fields
}
```

**GAP**: The `execute_data` is correctly structured but prompts don't explain:
1. What happens when user confirms
2. That Privy will open a signing modal
3. That user must approve in wallet

---

## 6. Revised Prompt Implementation Plan

### 6.1 Priority Order for Updates

| Priority | Task | Impact | Effort |
|----------|------|--------|--------|
| **P0** | Add explicit user approval language to all execution prompts | Safety Critical | Low |
| **P0** | Add health factor checks to borrow/withdraw prompts | Safety Critical | Medium |
| **P1** | Create Market Scanner Agent with temp=0.3 | Core Feature | High |
| **P1** | Create Risk Guardian Agent with temp=0.2 | Core Feature | High |
| **P1** | Add lending shortcuts to shortcuts.json | User Experience | Medium |
| **P2** | Add few-shot examples to all lending prompts | Quality | Medium |
| **P2** | Add chain-of-thought instructions | Quality | Medium |
| **P2** | Add LTV/Health Factor knowledge to knowledge base | Quality | Low |
| **P3** | Add MCP tool references to prompts | Developer Experience | Low |
| **P3** | Implement loop strategy workflow | Advanced Feature | High |

### 6.2 Knowledge Injection Strategy

**Step 1: Update Knowledge Base**
- Add `anvil_knowledge/features/lending_knowledge.json` with:
  - Protocol comparison (Aave vs Morpho)
  - LTV risk classification (6 levels)
  - Health factor ranges (5 levels)
  - Asset-specific liquidation thresholds

**Step 2: Update Intent Classifier**
- Add LENDING_* intents to `intent_classifier.py`
- Add multi-language pattern matching

**Step 3: Update Shortcuts**
- Add "lending" category to `shortcuts.json`
- Add 6 specified shortcuts with patterns

**Step 4: Create/Update Agents**
- Create MarketScannerAgent (temp=0.3)
- Create RiskGuardianAgent (temp=0.2)
- Update LendingWorkflowAgent with few-shot examples
- Add health factor checks to Executor

### 6.3 Testing Approach for Prompts

| Test Category | Test Cases | Validation |
|---------------|------------|------------|
| **Safety Tests** | Confirm prompts require user approval | Manual review + integration tests |
| **Language Tests** | Test all 4 languages for correct terminology | Automated localization tests |
| **Few-Shot Accuracy** | Test example inputs produce expected outputs | LLM evaluation suite |
| **Temperature Validation** | Verify responses are appropriately deterministic | Statistical analysis of outputs |
| **Health Factor Tests** | Test danger zone detection and warnings | Integration tests with mock data |
| **Edge Cases** | Test insufficient balance, no vaults, API failures | Unit tests |

---

## 7. Summary of Critical Gaps

### 7.1 Safety-Critical Gaps (Must Fix Immediately)

1. **User Approval Language**: Prompts must explicitly state "requires your wallet signature" and "no funds moved without approval"

2. **Health Factor Validation**: No prompt-level validation prevents borrow/withdraw operations that would cause liquidation

3. **Multi-Signature Warning**: Loop strategy requires multiple signatures - user must be warned

### 7.2 Feature Gaps (Should Fix for Launch)

1. **Missing Agents**: Market Scanner (rate comparison) and Risk Guardian (health monitoring)

2. **Missing Shortcuts**: All 6 lending shortcuts not in shortcuts.json

3. **Temperature Settings**: Most agents use default 0.7 instead of specified values

4. **Few-Shot Examples**: No agents have few-shot examples in prompts

### 7.3 Quality Gaps (Nice to Have)

1. **Chain-of-Thought**: Explicit reasoning chains not in prompts

2. **MCP Tool References**: Prompts don't reference specific MCP ports

3. **Protocol Comparison Knowledge**: Detailed Aave vs Morpho knowledge not injected

---

## Related Documentation

- **Agent Prompts Specification**: `/docs/ceo/agents/lending/agent_prompts.md`
- **Knowledge Base Specification**: `/docs/ceo/agents/lending/knowledge_base.md`
- **Shortcuts Specification**: `/docs/ceo/agents/lending/shortcuts_update.md`
- **Current Lending Implementation**: `/src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`
- **Current Shortcuts**: `/anvil_knowledge/features/shortcuts.json`
