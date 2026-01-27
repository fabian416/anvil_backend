# Lending Shortcuts Configuration

**Version**: 1.0
**Date**: January 27, 2026
**Status**: Specification
**Purpose**: Define shortcuts and command patterns for lending workflows

---

## Executive Summary

This document specifies the shortcut configurations for lending-related intents in the Anvil chat system. These shortcuts enable natural language processing of lending commands and route users through appropriate multi-agent workflows.

---

## Lending Shortcuts Overview

### Command Categories

| Category | Intent | Primary Agent | Flow Type |
|----------|--------|---------------|-----------|
| Health Check | `LENDING_HEALTH_CHECK` | Risk Guardian | Single-step |
| Supply | `LENDING_SUPPLY` | Market Scanner -> Executor | Multi-step |
| Borrow | `LENDING_BORROW` | Risk Guardian -> Executor | Multi-step |
| Leverage Loop | `LENDING_LOOP` | Optimizer -> Risk Guardian -> Executor | Multi-step |
| Yield Comparison | `LENDING_COMPARE` | Market Scanner | Single-step |
| Position View | `LENDING_POSITION` | Risk Guardian | Single-step |

---

## 1. Health Check Flow

**Shortcut**: "Check my lending position"

### Configuration

```json
{
  "intent": "LENDING_HEALTH_CHECK",
  "patterns": [
    "check my lending position",
    "what's my health factor",
    "am I at risk of liquidation",
    "show my loan status",
    "lending health",
    "my lending positions",
    "check my collateral",
    "how safe is my position"
  ],
  "multi_language": {
    "es": [
      "verificar mi posicion de prestamo",
      "cual es mi factor de salud",
      "estoy en riesgo de liquidacion",
      "mostrar estado de mi prestamo"
    ],
    "pt": [
      "verificar minha posicao de emprestimo",
      "qual e meu fator de saude",
      "estou em risco de liquidacao",
      "mostrar status do emprestimo"
    ],
    "zh": [
      "检查我的借贷仓位",
      "我的健康因子是多少",
      "我有清算风险吗",
      "显示贷款状态"
    ]
  },
  "agent_routing": {
    "primary_agent": "RiskGuardian",
    "fallback_agent": "Knowledge",
    "requires_auth": true
  },
  "response_requirements": {
    "include_health_factor": true,
    "include_collateral_breakdown": true,
    "include_debt_breakdown": true,
    "include_price_scenarios": true,
    "include_action_recommendations": true
  }
}
```

### Flow Diagram

```
User: "Check my lending position"
    |
    v
[Auth Check] --> Not Authenticated --> [Educational Response + CTA]
    |
    v
[Fetch Positions] --> MCP: get_user_positions (Aave, Morpho)
    |
    v
[Calculate Health] --> MCP: calculate_health_factor
    |
    v
[Risk Assessment] --> Classify: SAFE/CAUTION/DANGER/CRITICAL
    |
    v
[Generate Response]
    |
    +-- HF > 2.0: "Position healthy, no action needed"
    +-- HF 1.5-2.0: "Monitor position, set alerts"
    +-- HF 1.1-1.5: "DANGER: Repay $X to improve"
    +-- HF < 1.1: "CRITICAL: Immediate action required"
```

### Example Response

**User**: "Check my lending position"

**Response** (HF = 1.25):
```
**POSITION STATUS**: DANGER

**Health Factor**: 1.25

**Aave V3 (Ethereum)**:
- Collateral: 5 ETH ($16,000)
- Debt: $10,000 USDC
- Current LTV: 62.5%

**Risk Assessment**:
A 20% ETH price drop would trigger liquidation.

| Price Drop | New HF | Status |
|------------|--------|--------|
| -10% | 1.12 | Critical |
| -20% | 0.99 | Liquidatable |

**Recommended Action**:
Repay $2,500 USDC to improve HF to 1.65 (CAUTION zone)

Reply "repay 2500 USDC" to execute.
```

---

## 2. Supply Flow

**Shortcut**: "Supply ETH to earn yield"

### Configuration

```json
{
  "intent": "LENDING_SUPPLY",
  "patterns": [
    "supply {amount} {asset} to earn yield",
    "deposit {asset} to morpho",
    "lend my {asset}",
    "earn yield on {asset}",
    "supply {asset} to {protocol}",
    "deposit to lending",
    "start earning on my {asset}",
    "put my {asset} to work"
  ],
  "multi_language": {
    "es": [
      "suministrar {amount} {asset}",
      "depositar {asset} en morpho",
      "prestar mi {asset}",
      "ganar rendimiento en {asset}"
    ],
    "pt": [
      "fornecer {amount} {asset}",
      "depositar {asset} no morpho",
      "emprestar meu {asset}",
      "ganhar rendimento em {asset}"
    ],
    "zh": [
      "供应 {amount} {asset}",
      "存入 {asset} 到 morpho",
      "借出我的 {asset}",
      "赚取 {asset} 收益"
    ]
  },
  "agent_routing": {
    "primary_agent": "MarketScanner",
    "secondary_agent": "Executor",
    "fallback_agent": "Knowledge",
    "requires_auth": true
  },
  "parameter_extraction": {
    "amount": {
      "type": "number",
      "optional": true,
      "default": null,
      "prompt_if_missing": "How much {asset} would you like to supply?"
    },
    "asset": {
      "type": "string",
      "optional": false,
      "valid_values": ["ETH", "USDC", "USDT", "DAI", "WBTC", "WETH"],
      "prompt_if_missing": "Which asset would you like to supply? (USDC, ETH, DAI, etc.)"
    },
    "protocol": {
      "type": "string",
      "optional": true,
      "default": "morpho",
      "valid_values": ["morpho", "aave"]
    }
  },
  "balance_check": {
    "required": true,
    "check_gas": true,
    "minimum_gas_eth": 0.005,
    "insufficient_balance_flow": "suggest_alternatives"
  }
}
```

### Multi-Step Flow

```
Step 1: Parse Request
    |
    v
[Extract: amount, asset, protocol]
    |
    +-- Missing amount --> "How much {asset}?"
    +-- Missing asset --> "Which asset?"
    |
    v
Step 2: Market Scan (MarketScanner)
    |
    v
[Fetch Vaults] --> MCP: morpho_get_vaults
    |
    v
[Compare APY] --> MCP: morpho_compare_yields
    |
    v
[Generate Recommendations]
    |
    v
Step 3: Balance Check
    |
    +-- Insufficient --> [Alternative Options]
    +-- Insufficient Gas --> [Gas Warning]
    +-- Sufficient --> Continue
    |
    v
Step 4: Transaction Preview (Executor)
    |
    v
[Build Transaction]
    |
    v
[Show Preview + Confirm Prompt]
    |
    v
Step 5: Await Confirmation
    |
    +-- "confirm" --> Execute
    +-- "cancel" --> Abort
    +-- timeout --> Abort
    |
    v
Step 6: Execute (Executor)
    |
    v
[Sign + Submit] --> Privy signing
    |
    v
[Report Result]
```

### Example Conversation

**User**: "Supply ETH to earn yield"

**Response (Step 1)**:
```
Great! Let me find the best ETH yield opportunities for you.

**Top ETH Vaults**:

| Vault | Protocol | APY | Risk |
|-------|----------|-----|------|
| Morpho ETH | Morpho | 3.8% | Low |
| Aave V3 ETH | Aave | 2.1% | Low |

How much ETH would you like to supply?
```

**User**: "1.5 ETH"

**Response (Step 2)**:
```
**TRANSACTION PREVIEW**

**Action**: Supply
**Protocol**: Morpho
**Chain**: Base

**Details**:
- Asset: ETH
- Amount: 1.5 ETH ($4,800)
- Vault: Morpho ETH Vault
- APY: 3.8%

**Expected Returns**:
- Daily: ~$0.50
- Monthly: ~$15.20
- Annual: ~$182.40

**Wallet Check**:
- Current: 2.0 ETH
- After: 0.5 ETH
- Gas: ~0.001 ETH ($3.20)

Reply "confirm" to execute or "cancel" to abort.
```

**User**: "confirm"

**Response (Step 3)**:
```
**TRANSACTION EXECUTED**

**Status**: SUCCESS
**Hash**: 0x7f2b3c...4e5d6a

**Summary**:
- Supplied 1.5 ETH to Morpho
- Current APY: 3.8%
- Vault Shares: 1.498 mETH

View on [BaseScan](https://basescan.org/tx/...)
```

---

## 3. Borrow Flow

**Shortcut**: "Borrow USDC"

### Configuration

```json
{
  "intent": "LENDING_BORROW",
  "patterns": [
    "borrow {amount} {asset}",
    "take a loan of {amount} {asset}",
    "borrow against my {collateral}",
    "get a loan",
    "borrow {asset} from aave",
    "I want to borrow"
  ],
  "multi_language": {
    "es": [
      "pedir prestado {amount} {asset}",
      "tomar un prestamo de {amount} {asset}",
      "quiero pedir prestado"
    ],
    "pt": [
      "emprestar {amount} {asset}",
      "fazer um emprestimo de {amount} {asset}",
      "quero pedir emprestado"
    ],
    "zh": [
      "借入 {amount} {asset}",
      "获得 {amount} {asset} 贷款",
      "我想借款"
    ]
  },
  "agent_routing": {
    "primary_agent": "RiskGuardian",
    "secondary_agent": "Executor",
    "requires_auth": true,
    "risk_check_required": true
  },
  "parameter_extraction": {
    "amount": {
      "type": "number",
      "optional": true,
      "prompt_if_missing": "How much {asset} would you like to borrow?"
    },
    "asset": {
      "type": "string",
      "optional": false,
      "valid_values": ["USDC", "USDT", "DAI", "ETH"],
      "prompt_if_missing": "Which asset would you like to borrow?"
    }
  },
  "safety_checks": {
    "check_collateral": true,
    "minimum_health_factor_after": 1.2,
    "warn_if_hf_below": 1.5,
    "reject_if_hf_below": 1.1
  },
  "anvil_note": "IMPORTANT: Anvil supports LENDING (supply assets) only. Borrowing is available via Aave but not emphasized in Anvil's primary offering."
}
```

### Safety Flow

```
[Parse Borrow Request]
    |
    v
[Check Current Position] --> No collateral --> "You need collateral first"
    |
    v
[Calculate Impact]
    |
    v
[New HF Check]
    |
    +-- HF >= 1.5: Proceed normally
    +-- HF 1.2-1.5: Show warning, require confirmation
    +-- HF < 1.2: REJECT, suggest lower amount
    |
    v
[If Approved: Execute]
```

---

## 4. Leverage Loop Flow

**Shortcut**: "Loop ETH for leverage"

### Configuration

```json
{
  "intent": "LENDING_LOOP",
  "patterns": [
    "loop {asset} for leverage",
    "leverage my {asset}",
    "recursive {asset} strategy",
    "loop {iterations} times on {asset}",
    "2x leverage on {asset}",
    "3x leverage on {asset}"
  ],
  "multi_language": {
    "es": [
      "apalancar mi {asset}",
      "estrategia recursiva {asset}",
      "apalancamiento 2x en {asset}"
    ],
    "pt": [
      "alavancar meu {asset}",
      "estrategia recursiva {asset}",
      "alavancagem 2x em {asset}"
    ],
    "zh": [
      "循环 {asset} 获得杠杆",
      "杠杆我的 {asset}",
      "2倍杠杆 {asset}"
    ]
  },
  "agent_routing": {
    "primary_agent": "Optimizer",
    "secondary_agents": ["RiskGuardian", "Executor"],
    "requires_auth": true,
    "advanced_strategy": true
  },
  "parameter_extraction": {
    "asset": {
      "type": "string",
      "required": true
    },
    "target_leverage": {
      "type": "number",
      "optional": true,
      "default": 2.0,
      "max": 4.0
    },
    "target_ltv": {
      "type": "number",
      "optional": true,
      "default": 0.65,
      "max": 0.75
    }
  },
  "risk_warnings": {
    "show_warning": true,
    "warning_text": "WARNING: Leverage amplifies both gains AND losses. Liquidation risk increases significantly.",
    "require_acknowledgment": true,
    "max_leverage_by_risk_tolerance": {
      "low": 1.5,
      "medium": 2.5,
      "high": 4.0
    }
  },
  "execution_notes": {
    "multiple_signatures": true,
    "signature_count": "iterations + 1",
    "gas_intensive": true
  }
}
```

### Loop Execution Flow

```
[Parse Loop Request]
    |
    v
[Validate Risk Tolerance] --> Low risk --> "Loop strategy not recommended"
    |
    v
[Calculate Loop Plan]
    |
    v
[Show Simulation]
    |
    +-- Iteration 1: Supply X -> Borrow Y
    +-- Iteration 2: Supply Y -> Borrow Z
    +-- ... (up to target leverage)
    |
    v
[Show Final Position]
    |
    v
[Risk Warning + Acknowledge]
    |
    v
[Execute Step-by-Step]
    |
    +-- Each step requires signature
    +-- Show progress after each
    +-- Can abort mid-loop
```

---

## 5. Yield Comparison Flow

**Shortcut**: "What's the best yield?"

### Configuration

```json
{
  "intent": "LENDING_COMPARE",
  "patterns": [
    "what's the best yield",
    "compare lending rates",
    "best apy for {asset}",
    "morpho vs aave rates",
    "where should I lend my {asset}",
    "highest yield for {asset}",
    "compare {protocol1} and {protocol2}"
  ],
  "multi_language": {
    "es": [
      "cual es el mejor rendimiento",
      "comparar tasas de prestamo",
      "mejor apy para {asset}"
    ],
    "pt": [
      "qual e o melhor rendimento",
      "comparar taxas de emprestimo",
      "melhor apy para {asset}"
    ],
    "zh": [
      "最好的收益率是多少",
      "比较借贷利率",
      "{asset} 的最佳 apy"
    ]
  },
  "agent_routing": {
    "primary_agent": "MarketScanner",
    "requires_auth": false,
    "guest_allowed": true
  },
  "parameter_extraction": {
    "asset": {
      "type": "string",
      "optional": true,
      "default": "USDC"
    },
    "chain": {
      "type": "string",
      "optional": true,
      "default": "base"
    }
  },
  "response_format": {
    "include_table": true,
    "sort_by": "apy",
    "limit": 5,
    "include_risk_tier": true,
    "include_tvl": true
  }
}
```

### Example Response

**User**: "What's the best yield for USDC?"

**Response**:
```
**USDC LENDING RATES** (Updated: Just now)

| Protocol | Vault/Pool | Chain | APY | Risk | TVL |
|----------|------------|-------|-----|------|-----|
| Morpho | Universal USDC | Base | 7.26% | Low | $313B |
| Morpho | Edge UltraYield | Base | 6.22% | Low | $500B |
| Aave V3 | USDC Pool | Ethereum | 4.15% | Low | $2.1B |
| Aave V3 | USDC Pool | Base | 3.85% | Low | $890M |
| Compound | cUSDCv3 | Ethereum | 3.42% | Low | $720M |

**Recommendation**: Morpho Universal USDC on Base offers the best yield (7.26%) with low risk.

Would you like to supply USDC to this vault?
```

---

## 6. Position View Flow

**Shortcut**: "Show my lending positions"

### Configuration

```json
{
  "intent": "LENDING_POSITION",
  "patterns": [
    "show my lending positions",
    "my lending portfolio",
    "what am I earning",
    "my defi positions",
    "show all my supplies",
    "where is my money earning"
  ],
  "multi_language": {
    "es": [
      "mostrar mis posiciones de prestamo",
      "mi cartera de prestamos",
      "que estoy ganando"
    ],
    "pt": [
      "mostrar minhas posicoes de emprestimo",
      "minha carteira de emprestimos",
      "o que estou ganhando"
    ],
    "zh": [
      "显示我的借贷仓位",
      "我的借贷投资组合",
      "我赚了多少"
    ]
  },
  "agent_routing": {
    "primary_agent": "RiskGuardian",
    "requires_auth": true
  },
  "response_format": {
    "group_by_protocol": true,
    "show_total_value": true,
    "show_weighted_apy": true,
    "show_earnings_summary": true
  }
}
```

### Example Response

**User**: "Show my lending positions"

**Response**:
```
**YOUR LENDING PORTFOLIO**

**Total Value**: $15,420
**Weighted APY**: 5.82%
**Monthly Earnings**: ~$74.80

---

**Morpho (Base)**

| Vault | Amount | APY | Monthly |
|-------|--------|-----|---------|
| Universal USDC | $8,000 | 7.26% | $48.40 |
| ETH Vault | 1.5 ETH ($4,800) | 3.8% | $15.20 |

---

**Aave V3 (Ethereum)**

| Pool | Amount | APY | Monthly |
|------|--------|-----|---------|
| USDC | $2,620 | 4.15% | $9.07 |

---

**Health Status**: SAFE (No debt positions)

**Optimization Opportunity**:
Move $2,620 from Aave to Morpho for +3.11% APY gain (~$81/year extra)

Would you like to optimize your positions?
```

---

## 7. Shortcuts JSON Update

This section provides the JSON configuration to add to `anvil_knowledge/features/shortcuts.json`:

```json
{
  "lending": {
    "title": "Lending & Yield",
    "description": "Supply assets to earn yield via Morpho and Aave protocols",
    "intent_group": ["LENDING_HEALTH_CHECK", "LENDING_SUPPLY", "LENDING_BORROW", "LENDING_LOOP", "LENDING_COMPARE", "LENDING_POSITION"],
    "commands": [
      {
        "intent": "LENDING_HEALTH_CHECK",
        "pattern": "check my lending position",
        "examples": [
          "check my lending position",
          "what's my health factor",
          "am I at risk of liquidation",
          "show my loan status"
        ],
        "multi_language": {
          "spanish": ["verificar mi posicion", "cual es mi factor de salud"],
          "portuguese": ["verificar minha posicao", "qual e meu fator de saude"],
          "chinese": ["检查我的仓位", "我的健康因子是多少"]
        },
        "response_type": "Health factor analysis with risk assessment and recommendations",
        "requires_auth": true
      },
      {
        "intent": "LENDING_SUPPLY",
        "pattern": "supply {asset} to earn yield",
        "examples": [
          "supply 1000 USDC to Morpho",
          "deposit ETH to earn yield",
          "lend my USDC",
          "earn yield on my ETH"
        ],
        "multi_language": {
          "spanish": ["suministrar USDC", "depositar ETH para ganar rendimiento"],
          "portuguese": ["fornecer USDC", "depositar ETH para ganhar rendimento"],
          "chinese": ["供应 USDC", "存入 ETH 赚取收益"]
        },
        "response_type": "Multi-step: Vault selection -> Balance check -> Transaction preview -> Execution",
        "requires_auth": true
      },
      {
        "intent": "LENDING_BORROW",
        "pattern": "borrow {asset}",
        "examples": [
          "borrow 5000 USDC",
          "take a loan against my ETH",
          "borrow from Aave"
        ],
        "multi_language": {
          "spanish": ["pedir prestado USDC", "tomar un prestamo"],
          "portuguese": ["emprestar USDC", "fazer um emprestimo"],
          "chinese": ["借入 USDC", "获得贷款"]
        },
        "response_type": "Risk assessment -> Health factor simulation -> Execution (with safety checks)",
        "requires_auth": true,
        "note": "Borrowing available via Aave; Anvil emphasizes supply/lending"
      },
      {
        "intent": "LENDING_LOOP",
        "pattern": "loop {asset} for leverage",
        "examples": [
          "loop ETH for leverage",
          "2x leverage on my ETH",
          "recursive ETH strategy"
        ],
        "multi_language": {
          "spanish": ["apalancar mi ETH", "2x apalancamiento"],
          "portuguese": ["alavancar meu ETH", "2x alavancagem"],
          "chinese": ["循环 ETH 获得杠杆", "2倍杠杆"]
        },
        "response_type": "Advanced strategy simulation -> Risk warning -> Multi-step execution",
        "requires_auth": true,
        "risk_level": "HIGH",
        "warning": "Leverage amplifies both gains and losses. Liquidation risk increases."
      },
      {
        "intent": "LENDING_COMPARE",
        "pattern": "what's the best yield",
        "examples": [
          "what's the best yield for USDC",
          "compare lending rates",
          "Morpho vs Aave rates",
          "highest APY for ETH"
        ],
        "multi_language": {
          "spanish": ["cual es el mejor rendimiento", "comparar tasas"],
          "portuguese": ["qual e o melhor rendimento", "comparar taxas"],
          "chinese": ["最好的收益率", "比较利率"]
        },
        "response_type": "Comparison table with APY, risk tier, and TVL across protocols",
        "requires_auth": false
      },
      {
        "intent": "LENDING_POSITION",
        "pattern": "show my lending positions",
        "examples": [
          "show my lending positions",
          "my lending portfolio",
          "what am I earning",
          "where is my money"
        ],
        "multi_language": {
          "spanish": ["mostrar mis posiciones", "mi cartera de prestamos"],
          "portuguese": ["mostrar minhas posicoes", "minha carteira"],
          "chinese": ["显示我的仓位", "我的借贷投资组合"]
        },
        "response_type": "Portfolio overview with positions, earnings, and optimization suggestions",
        "requires_auth": true
      }
    ]
  }
}
```

---

## 8. Intent Classification Updates

Add to intent classifier mappings:

```python
# In src/app/domain/services/agent_squad/intent_classifier.py

LENDING_INTENTS = {
    "LENDING_HEALTH_CHECK": {
        "keywords": ["health factor", "lending position", "liquidation risk", "loan status", "collateral check"],
        "agent_type": AgentType.RISK_GUARDIAN,
        "priority": 1
    },
    "LENDING_SUPPLY": {
        "keywords": ["supply", "deposit", "lend", "earn yield", "morpho deposit", "aave supply"],
        "agent_type": AgentType.MARKET_SCANNER,
        "priority": 2
    },
    "LENDING_BORROW": {
        "keywords": ["borrow", "take loan", "get loan", "borrow against"],
        "agent_type": AgentType.RISK_GUARDIAN,
        "priority": 2
    },
    "LENDING_LOOP": {
        "keywords": ["loop", "leverage", "recursive", "2x", "3x", "leveraged position"],
        "agent_type": AgentType.OPTIMIZER,
        "priority": 3
    },
    "LENDING_COMPARE": {
        "keywords": ["best yield", "compare rates", "apy comparison", "morpho vs aave", "highest yield"],
        "agent_type": AgentType.MARKET_SCANNER,
        "priority": 1
    },
    "LENDING_POSITION": {
        "keywords": ["my positions", "lending portfolio", "what am i earning", "my supplies"],
        "agent_type": AgentType.RISK_GUARDIAN,
        "priority": 1
    }
}
```

---

## 9. Handler Integration

### LendingHandler Updates

The existing `LendingHandler` at `/src/app/application/chat/handlers/lending_handler.py` handles Morpho vault operations. Integration points:

1. **Intent Detection**: Route `LENDING_*` intents to appropriate handlers
2. **Multi-Step Flows**: Use `pending_action` and `lending_info` for state management
3. **Agent Coordination**: Call Market Scanner for rates, Risk Guardian for safety, Executor for transactions

### Unified Chat Handler Integration

```python
# In unified_chat_handler.py

async def handle_lending_intent(
    self,
    intent: str,
    message: str,
    context: ConversationContext,
) -> ChatResponse:
    """Route lending intents to appropriate agents."""

    if intent == "LENDING_HEALTH_CHECK":
        return await self._risk_guardian.check_health(context.wallet_address)

    elif intent == "LENDING_SUPPLY":
        # Multi-step: Market scan -> Balance check -> Execute
        rates = await self._market_scanner.get_rates(message)
        return self._build_supply_preview(rates, context)

    elif intent == "LENDING_COMPARE":
        return await self._market_scanner.compare_yields(message)

    elif intent == "LENDING_LOOP":
        # Requires Optimizer -> Risk Guardian -> Executor chain
        return await self._optimizer.plan_loop(message, context)

    # ... etc
```

---

## 10. Testing Scenarios

### Test Cases

| Scenario | Input | Expected Flow | Expected Output |
|----------|-------|---------------|-----------------|
| Guest health check | "check my health factor" | Auth check fails | Educational response + signup CTA |
| Auth supply flow | "supply 1000 USDC" | Market scan -> Preview | Vault options + confirmation prompt |
| Insufficient balance | "supply 10000 USDC" (has 2000) | Balance check fails | Alternative suggestions |
| Dangerous borrow | "borrow 5000 USDC" (HF would be 1.15) | Risk check warns | Warning + safer alternative |
| Loop strategy | "loop ETH for 3x" | Risk warning | Full simulation + acknowledgment required |
| Yield comparison | "best USDC rates" | Market scan | Comparison table |

---

## Related Documentation

- **Agent Prompts**: `/docs/ceo/agents/lending/agent_prompts.md`
- **Knowledge Base**: `/docs/ceo/agents/lending/knowledge_base.md`
- **Existing Shortcuts**: `/anvil_knowledge/features/shortcuts.json`
- **Lending Handler**: `/src/app/application/chat/handlers/lending_handler.py`
