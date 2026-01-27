# Lending Agents Knowledge Base

**Version**: 1.0
**Date**: January 27, 2026
**Status**: Specification
**Purpose**: Knowledge injection for lending workflow agents

---

## Executive Summary

This knowledge base provides the structured domain knowledge that lending agents use to provide accurate, context-aware responses. It includes:

- Protocol comparisons (Aave vs Morpho characteristics)
- Risk level classifications by LTV ratio
- Health factor interpretation guidelines
- User context-aware response templates
- Balance-aware response strategies

---

## 1. Protocol Comparison Knowledge

### Aave V3 vs Morpho Blue

```json
{
  "protocol_comparison": {
    "aave_v3": {
      "name": "Aave V3",
      "type": "Lending Pool",
      "tvl_range": "$10B+",
      "supported_chains": ["Ethereum", "Polygon", "Arbitrum", "Optimism", "Avalanche", "Base"],
      "key_features": [
        "Variable and stable interest rates",
        "Flash loans (0.09% fee)",
        "E-Mode for correlated assets",
        "Isolation mode for new assets",
        "Credit delegation"
      ],
      "supply_apy_range": {
        "USDC": "2.5% - 5.5%",
        "ETH": "1.5% - 3.5%",
        "WBTC": "0.5% - 2.0%"
      },
      "borrow_apy_range": {
        "USDC": "4.0% - 8.0%",
        "ETH": "2.5% - 5.5%",
        "WBTC": "1.5% - 4.0%"
      },
      "risk_level": "LOW",
      "audit_status": "Multiple audits (Trail of Bits, OpenZeppelin, Certora)",
      "insurance": "Nexus Mutual, InsurAce coverage available",
      "mcp_port": 8085,
      "mcp_tools": [
        "get_market_data",
        "get_user_positions",
        "calculate_health_factor",
        "get_available_to_borrow",
        "supply_asset",
        "borrow_asset",
        "repay_loan",
        "withdraw_supply",
        "get_liquidation_risk"
      ]
    },
    "morpho": {
      "name": "Morpho Protocol",
      "type": "P2P Lending Optimizer + MetaMorpho Vaults",
      "tvl_range": "$1B - $2B",
      "supported_chains": ["Ethereum", "Base"],
      "key_features": [
        "P2P matching for better rates",
        "MetaMorpho vaults (ERC-4626)",
        "Morpho Blue isolated markets",
        "Curator-managed vault strategies",
        "No flash loans"
      ],
      "supply_apy_range": {
        "USDC": "5.0% - 8.0%",
        "ETH": "2.5% - 5.0%",
        "WBTC": "1.0% - 3.0%"
      },
      "apy_premium_over_aave": "20-30% higher via P2P matching",
      "risk_level": "LOW-MEDIUM",
      "audit_status": "Audited by Spearbit, Cantina",
      "insurance": "Limited coverage",
      "mcp_port": 8088,
      "mcp_tools": [
        "morpho_get_vaults",
        "morpho_get_vault_details",
        "morpho_get_vault_apy",
        "morpho_get_markets",
        "morpho_get_user_positions",
        "morpho_compare_yields"
      ]
    }
  }
}
```

### When to Recommend Each Protocol

| Scenario | Recommended | Reasoning |
|----------|-------------|-----------|
| Maximum yield seeking | Morpho | Higher APY via P2P matching |
| Multi-chain positions | Aave | 6+ chains supported |
| Flash loan strategies | Aave | Native flash loan support |
| Conservative, large TVL | Aave | Battle-tested, $10B+ TVL |
| Yield optimization on Base | Morpho | Strong Base presence, curated vaults |
| Need to borrow against collateral | Aave | Full borrowing support |
| Supply-only yield farming | Morpho | Optimized for suppliers |

---

## 2. Risk Levels by LTV Ratio

### LTV (Loan-to-Value) Risk Classification

```json
{
  "ltv_risk_classification": {
    "ultra_safe": {
      "ltv_range": "0% - 30%",
      "risk_level": "MINIMAL",
      "color": "green",
      "health_factor_range": "> 2.75",
      "description": "Extremely conservative position with massive liquidation buffer",
      "recommendation": "Position is very safe. Can consider increasing utilization if seeking higher returns.",
      "price_drop_tolerance": "> 60%"
    },
    "safe": {
      "ltv_range": "30% - 50%",
      "risk_level": "LOW",
      "color": "green",
      "health_factor_range": "1.65 - 2.75",
      "description": "Healthy position with substantial buffer against market volatility",
      "recommendation": "Good balance of capital efficiency and safety. Monitor during high volatility.",
      "price_drop_tolerance": "40% - 60%"
    },
    "moderate": {
      "ltv_range": "50% - 65%",
      "risk_level": "MEDIUM",
      "color": "yellow",
      "health_factor_range": "1.27 - 1.65",
      "description": "Moderate risk position requiring active monitoring",
      "recommendation": "Set up liquidation alerts. Consider reducing exposure in volatile markets.",
      "price_drop_tolerance": "25% - 40%"
    },
    "aggressive": {
      "ltv_range": "65% - 75%",
      "risk_level": "HIGH",
      "color": "orange",
      "health_factor_range": "1.10 - 1.27",
      "description": "High-risk position close to danger zone",
      "recommendation": "Actively monitor. Prepare to repay debt or add collateral. Not recommended for volatile assets.",
      "price_drop_tolerance": "15% - 25%"
    },
    "danger": {
      "ltv_range": "75% - 82%",
      "risk_level": "CRITICAL",
      "color": "red",
      "health_factor_range": "1.00 - 1.10",
      "description": "Position at imminent liquidation risk",
      "recommendation": "IMMEDIATE ACTION REQUIRED. Repay debt or add collateral NOW.",
      "price_drop_tolerance": "< 15%"
    },
    "liquidatable": {
      "ltv_range": "> 82%",
      "risk_level": "LIQUIDATABLE",
      "color": "red",
      "health_factor_range": "< 1.00",
      "description": "Position can be liquidated",
      "recommendation": "Emergency: Position is being or will be liquidated. Act immediately if possible.",
      "price_drop_tolerance": "0%"
    }
  }
}
```

### Liquidation Thresholds by Asset

| Asset | Aave LT | Morpho LLTV | Liquidation Bonus |
|-------|---------|-------------|-------------------|
| ETH | 82.5% | 86% | 5% |
| WBTC | 75% | 80% | 6.5% |
| USDC | 88% | 91.5% | 4% |
| DAI | 85% | 88% | 4% |
| LINK | 70% | 75% | 7% |
| AAVE | 66% | 70% | 7.5% |

---

## 3. Health Factor Interpretation

### Health Factor Classification System

```json
{
  "health_factor_classification": {
    "safe": {
      "range": "> 2.0",
      "status": "SAFE",
      "emoji": "green_circle",
      "action_required": "None",
      "description": "Position is healthy with strong buffer against liquidation",
      "typical_ltv": "< 40%",
      "agent_behavior": "Provide positive reinforcement, suggest optimization opportunities if user is interested",
      "sample_response": "Your position is healthy! Health Factor of {hf} means you have a strong safety margin. Your collateral would need to drop by approximately {drop_pct}% before reaching liquidation risk."
    },
    "caution": {
      "range": "1.5 - 2.0",
      "status": "CAUTION",
      "emoji": "yellow_circle",
      "action_required": "Monitor closely",
      "description": "Position requires attention during volatile markets",
      "typical_ltv": "40% - 55%",
      "agent_behavior": "Recommend setting up alerts, provide price drop scenarios",
      "sample_response": "Your Health Factor of {hf} is in the CAUTION zone. While not immediately dangerous, I recommend monitoring your position during volatile periods. Set alerts at HF = 1.3 for early warning."
    },
    "danger": {
      "range": "1.1 - 1.5",
      "status": "DANGER",
      "emoji": "orange_circle",
      "action_required": "Repay debt or add collateral",
      "description": "Position at elevated risk - action recommended",
      "typical_ltv": "55% - 75%",
      "agent_behavior": "Urgently recommend risk reduction, calculate exact repayment amounts",
      "sample_response": "WARNING: Your Health Factor of {hf} is in the DANGER zone. A {drop_pct}% price drop would trigger liquidation. I strongly recommend repaying at least ${repay_amount} to improve your position to HF > 1.5."
    },
    "critical": {
      "range": "1.0 - 1.1",
      "status": "CRITICAL",
      "emoji": "red_circle",
      "action_required": "Immediate action required",
      "description": "Liquidation imminent - emergency action needed",
      "typical_ltv": "75% - 82%",
      "agent_behavior": "Provide one-click repayment option, skip educational content",
      "sample_response": "CRITICAL: Your Health Factor is {hf}. Liquidation can occur at any moment. IMMEDIATE ACTION: Repay ${repay_amount} NOW to reach safety. [Execute Repayment]"
    },
    "liquidatable": {
      "range": "< 1.0",
      "status": "LIQUIDATABLE",
      "emoji": "red_circle_exclamation",
      "action_required": "Position can be liquidated NOW",
      "description": "Position is eligible for liquidation",
      "typical_ltv": "> 82%",
      "agent_behavior": "Explain what happened, options for remaining collateral",
      "sample_response": "Your position is LIQUIDATABLE with HF = {hf}. Liquidators may seize your collateral at any moment. If you still have time, repay ${repay_amount} immediately. If already liquidated, I can help you understand what happened."
    }
  }
}
```

### Health Factor Calculation Reference

```
Health Factor = (Total Collateral USD * Weighted Liquidation Threshold) / Total Debt USD

Example:
- Collateral: 10 ETH @ $3,200 = $32,000
- Liquidation Threshold: 82.5%
- Debt: $15,000 USDC

Health Factor = ($32,000 * 0.825) / $15,000 = 1.76 (CAUTION)
```

---

## 4. User Context-Aware Responses

### Guest User Responses

**Characteristics**:
- `is_authenticated: false`
- No wallet connected
- Read-only access

**Response Strategy**:
```json
{
  "guest_user_behavior": {
    "content_type": "Educational",
    "include_cta": true,
    "cta_message": "Sign up to execute this action -> /signup",
    "data_access": "Public market data only",
    "restricted_features": [
      "Transaction execution",
      "Position viewing",
      "Portfolio tracking",
      "Personalized recommendations"
    ],
    "allowed_features": [
      "Market rate viewing",
      "Protocol education",
      "Risk explanations",
      "APY comparisons",
      "Health factor education"
    ],
    "tone": "Educational and informative",
    "example_responses": {
      "rate_query": "Current USDC lending rates:\n- Morpho: 7.26% APY\n- Aave: 4.15% APY\n\nTo start earning yield, connect your wallet and sign up!\n\n👉 Sign up to execute this action -> /signup",
      "position_query": "To check your lending positions, you'll need to connect your wallet first.\n\nHealth Factor is calculated as: (Collateral * Liquidation Threshold) / Debt\n\n[Learn more about Health Factor]\n\n👉 Sign up to check your position -> /signup"
    }
  }
}
```

### Authenticated User Responses

**Characteristics**:
- `is_authenticated: true`
- Wallet connected
- Full access to features

**Response Strategy**:
```json
{
  "authenticated_user_behavior": {
    "content_type": "Actionable",
    "include_cta": false,
    "data_access": "Full position data + market data",
    "personalization": {
      "use_wallet_balance": true,
      "use_current_positions": true,
      "use_risk_tolerance": true,
      "use_preferred_chain": true
    },
    "tone": "Professional and action-oriented",
    "example_responses": {
      "rate_query": "Current rates for your preferred chains:\n\n| Protocol | APY | Your Balance | Potential Annual |\n|----------|-----|--------------|------------------|\n| Morpho Universal | 7.26% | 5,000 USDC | $363 |\n| Aave V3 | 4.15% | 5,000 USDC | $207.50 |\n\nRecommended: Supply to Morpho Universal for best returns.\n\nReply 'supply 5000 USDC to Morpho' to execute.",
      "position_query": "Your Lending Positions:\n\n**Aave V3 (Ethereum)**:\n- Collateral: 5 ETH ($16,000)\n- Debt: $8,000 USDC\n- Health Factor: 1.65 (CAUTION)\n\n**Action Needed**: Consider repaying $2,000 to improve HF to 2.0\n\nReply 'repay 2000 USDC' to execute."
    }
  }
}
```

---

## 5. Balance-Aware Responses

### Sufficient Balance Flow

```json
{
  "sufficient_balance": {
    "trigger": "wallet_balance[asset] >= requested_amount",
    "response_type": "Execution Ready",
    "include": [
      "Transaction preview",
      "Gas estimate",
      "Expected outcomes",
      "Confirmation prompt"
    ],
    "example": {
      "user_request": "Supply 1000 USDC to Morpho",
      "wallet_balance": {"USDC": 5000, "ETH": 0.5},
      "response": "**Ready to Execute**\n\nSupply 1,000 USDC to Morpho Universal Vault\n\n- Current Balance: 5,000 USDC\n- After Transaction: 4,000 USDC\n- Expected APY: 7.26%\n- Gas: ~0.0003 ETH ($0.80)\n\nReply 'confirm' to execute."
    }
  }
}
```

### Insufficient Balance Flow

```json
{
  "insufficient_balance": {
    "trigger": "wallet_balance[asset] < requested_amount",
    "response_type": "Alternative Suggestions",
    "include": [
      "Balance comparison",
      "Alternative amounts",
      "Asset alternatives",
      "Funding options"
    ],
    "example": {
      "user_request": "Supply 10000 USDC to Morpho",
      "wallet_balance": {"USDC": 2500, "ETH": 1.5},
      "response": "**Insufficient USDC Balance**\n\nYou requested 10,000 USDC but have 2,500 USDC.\n\n**Options**:\n1. Supply available 2,500 USDC (APY: 7.26%, Annual: $181.50)\n2. Supply 1.5 ETH instead (APY: 3.8%, Annual: $182.40)\n3. Buy USDC via MoonPay\n4. Bridge USDC from another chain\n\nWhich option would you like?"
    }
  }
}
```

### Insufficient Gas Flow

```json
{
  "insufficient_gas": {
    "trigger": "gas_balance_eth < minimum_required",
    "minimum_required": 0.005,
    "response_type": "Gas Warning",
    "include": [
      "Gas requirement",
      "Current gas balance",
      "Funding options"
    ],
    "example": {
      "user_request": "Supply 1000 USDC to Aave",
      "wallet_balance": {"USDC": 5000, "ETH": 0.001},
      "response": "**Insufficient Gas**\n\nTransaction requires ~0.003 ETH for gas, but you only have 0.001 ETH.\n\n**Options**:\n1. Bridge ETH from another chain\n2. Buy ETH via MoonPay\n3. Use a different chain with lower gas (e.g., Base)\n\nWould you like to proceed on Base instead? Gas costs are 10x lower."
    }
  }
}
```

---

## 6. Multi-Language Support

### Lending-Specific Translations

```json
{
  "i18n": {
    "en": {
      "supply": "Supply",
      "borrow": "Borrow",
      "repay": "Repay",
      "withdraw": "Withdraw",
      "health_factor": "Health Factor",
      "collateral": "Collateral",
      "debt": "Debt",
      "liquidation": "Liquidation",
      "apy": "APY",
      "vault": "Vault",
      "pool": "Pool",
      "safe": "Safe",
      "caution": "Caution",
      "danger": "Danger",
      "critical": "Critical",
      "confirm_action": "Reply 'confirm' to execute",
      "signup_cta": "Sign up to execute this action -> /signup"
    },
    "es": {
      "supply": "Suministrar",
      "borrow": "Pedir prestado",
      "repay": "Pagar",
      "withdraw": "Retirar",
      "health_factor": "Factor de Salud",
      "collateral": "Colateral",
      "debt": "Deuda",
      "liquidation": "Liquidacion",
      "apy": "APY",
      "vault": "Boveda",
      "pool": "Pool",
      "safe": "Seguro",
      "caution": "Precaucion",
      "danger": "Peligro",
      "critical": "Critico",
      "confirm_action": "Responde 'confirmar' para ejecutar",
      "signup_cta": "Registrate para ejecutar esta accion -> /signup"
    },
    "pt": {
      "supply": "Fornecer",
      "borrow": "Emprestar",
      "repay": "Pagar",
      "withdraw": "Retirar",
      "health_factor": "Fator de Saude",
      "collateral": "Colateral",
      "debt": "Divida",
      "liquidation": "Liquidacao",
      "apy": "APY",
      "vault": "Cofre",
      "pool": "Pool",
      "safe": "Seguro",
      "caution": "Cuidado",
      "danger": "Perigo",
      "critical": "Critico",
      "confirm_action": "Responda 'confirmar' para executar",
      "signup_cta": "Cadastre-se para executar esta acao -> /signup"
    },
    "zh": {
      "supply": "供应",
      "borrow": "借款",
      "repay": "还款",
      "withdraw": "提款",
      "health_factor": "健康因子",
      "collateral": "抵押品",
      "debt": "债务",
      "liquidation": "清算",
      "apy": "年化收益率",
      "vault": "金库",
      "pool": "池",
      "safe": "安全",
      "caution": "注意",
      "danger": "危险",
      "critical": "紧急",
      "confirm_action": "回复'确认'执行",
      "signup_cta": "注册以执行此操作 -> /signup"
    }
  }
}
```

### IMPORTANT: Lending vs Borrowing Terminology

```json
{
  "terminology_warning": {
    "critical_note": "Anvil supports LENDING (supply assets to earn yield) only, NOT borrowing",
    "correct_terms": {
      "en": ["supply", "lend", "deposit", "earn yield"],
      "es": ["suministrar", "depositar", "ganar rendimiento"],
      "pt": ["fornecer", "depositar", "ganhar rendimento"],
      "zh": ["供应", "存款", "赚取收益"]
    },
    "incorrect_terms": {
      "en": ["borrow", "take loan", "get loan"],
      "es": ["prestamos", "pedir prestado", "obtener prestamo"],
      "pt": ["emprestimos", "pedir emprestado"],
      "zh": ["借款", "贷款"]
    },
    "agent_instruction": "When discussing Anvil's lending feature, ALWAYS use 'supply assets to earn yield' terminology. NEVER suggest borrowing as an Anvil feature."
  }
}
```

---

## 6.5 Vault Query Patterns

### Query Routing for Vault-Related Queries

Vault comparison and discovery queries route to `LendingHandler` via the `LENDING` intent with `pattern_type: vault_comparison` metadata.

### Supported Vault Query Patterns

| Pattern Type | Example Queries | Intent | Handler |
|--------------|-----------------|--------|---------|
| Best/Top Vaults | "best lending vaults", "top vaults", "highest vaults" | LENDING | LendingHandler |
| Morpho-Specific | "best morpho vaults", "top morpho vaults" | LENDING | LendingHandler |
| Show Vaults | "show me best vaults", "show top vaults" | LENDING | LendingHandler |
| Compare Vaults | "compare vaults", "compare morpho vaults" | LENDING | LendingHandler |
| Vault Features | "vault comparison", "vault recommendations" | LENDING | LendingHandler |
| APY-Focused | "vaults with best apy", "highest yield vaults" | LENDING | LendingHandler |
| Discovery | "list morpho vaults", "find best vaults" | LENDING | LendingHandler |

### Pattern vs Rate Query Distinction

**IMPORTANT**: Vault queries differ from rate queries:

| Query Type | Example | Intent | Behavior |
|------------|---------|--------|----------|
| **Vault Query** | "best lending vaults" | LENDING | Returns Morpho vault list with APY, TVL, recommendations |
| **Rate Query** | "best lending rates" | MONEY_MARKET | Returns Aave/Compound rate comparison table |

### Metadata Support

Vault patterns include `pattern_type: vault_comparison` metadata:
```json
{
  "intent": "LENDING",
  "confidence": 0.90,
  "metadata": {
    "pattern_type": "vault_comparison"
  }
}
```

### Expected Response Format

For vault queries, LendingHandler returns:
```
USDC MORPHO VAULTS ON BASE

Top 3 vaults by APY (Morpho Protocol):

1. Universal USDC
   - APY: 7.26%
   - TVL: $313.40B
   - Address: 0xB7890CEE...6ab863

2. Edge UltraYield USDC
   - APY: 6.22%
   - TVL: $499.91B

3. Extrafi XLend USDC
   - APY: 6.16%
   - TVL: $8.13M

RECOMMENDATION:
Best Vault: Universal USDC
APY: 7.26%
Risk Level: Low (Curated)

Would you like me to help you deposit into Universal USDC?
```

---

## 7. Protocol-Specific Knowledge

### Morpho MetaMorpho Vaults

```json
{
  "morpho_vaults": {
    "vault_types": {
      "curated": {
        "description": "Whitelisted vaults managed by trusted curators",
        "risk_level": "LOW",
        "recommendation": "Recommended for most users",
        "identifier": "whitelisted: true"
      },
      "non_curated": {
        "description": "Community vaults without curator oversight",
        "risk_level": "MEDIUM-HIGH",
        "recommendation": "Only for experienced users who understand risks",
        "identifier": "whitelisted: false"
      }
    },
    "vault_mechanics": {
      "deposit_flow": [
        "1. Approve vault contract to spend your tokens",
        "2. Call vault.deposit(assets, receiver)",
        "3. Receive vault shares (ERC-4626 standard)",
        "4. Shares automatically accrue yield"
      ],
      "withdraw_flow": [
        "1. Call vault.withdraw(assets, receiver, owner)",
        "2. Shares are burned",
        "3. Underlying assets returned to wallet"
      ],
      "yield_accrual": "Automatic - vault shares increase in value over time"
    },
    "top_vaults": {
      "base_usdc": [
        {"name": "Universal USDC", "apy": "7.26%", "tvl": "$313.4B", "address": "0xB7890CEE...6ab863"},
        {"name": "Edge UltraYield USDC", "apy": "6.22%", "tvl": "$499.9B", "address": "0x5435BC53...259ca0"},
        {"name": "Extrafi XLend USDC", "apy": "6.16%", "tvl": "$8.13M", "address": "0x23479229...753B5e"}
      ]
    }
  }
}
```

### Aave V3 Specifics

```json
{
  "aave_v3": {
    "e_mode": {
      "description": "Efficiency Mode for correlated assets (e.g., ETH/stETH)",
      "benefit": "Higher LTV for correlated pairs (up to 97%)",
      "risk": "Only works for specific asset pairs",
      "agent_instruction": "Mention E-Mode when user has correlated assets"
    },
    "isolation_mode": {
      "description": "New assets listed in isolated pools",
      "limitation": "Can only borrow stablecoins, limited debt ceiling",
      "agent_instruction": "Warn users about limitations for isolated assets"
    },
    "flash_loans": {
      "fee": "0.09%",
      "use_cases": ["Arbitrage", "Collateral swaps", "Self-liquidation"],
      "agent_instruction": "Mention flash loans for advanced users seeking arbitrage"
    }
  }
}
```

---

## 8. Error Response Templates

### Common Error Scenarios

```json
{
  "error_templates": {
    "position_not_found": {
      "condition": "No lending positions found for wallet",
      "response": {
        "en": "No lending positions found for your wallet. Would you like to:\n1. Supply assets to earn yield\n2. Compare current lending rates\n3. Learn about DeFi lending",
        "es": "No se encontraron posiciones de prestamo. ¿Te gustaria:\n1. Suministrar activos para ganar rendimiento\n2. Comparar tasas actuales\n3. Aprender sobre prestamos DeFi"
      }
    },
    "vault_not_found": {
      "condition": "Requested vault does not exist",
      "response": {
        "en": "I couldn't find that vault. Here are the top vaults available:\n[list top 3 vaults]\n\nWhich one would you like to explore?"
      }
    },
    "chain_not_supported": {
      "condition": "User requests chain not supported by protocol",
      "response": {
        "en": "Morpho is currently available on Ethereum and Base. You requested {chain}.\n\nWould you like to:\n1. Switch to Base (recommended)\n2. Switch to Ethereum\n3. View Aave options on {chain}"
      }
    },
    "api_error": {
      "condition": "MCP tool returns error",
      "response": {
        "en": "I'm having trouble fetching live data right now. Based on recent data:\n\n[fallback rates]\n\nPlease try again in a few minutes for real-time rates."
      }
    }
  }
}
```

---

## 9. Risk Warning Templates

### Standard Risk Warnings

```json
{
  "risk_warnings": {
    "leverage_warning": {
      "trigger": "User requests leverage or loop strategy",
      "warning": "WARNING: Leverage amplifies both gains AND losses. Your position can be liquidated if collateral value drops. Only proceed if you understand and accept these risks.",
      "include_before_execution": true
    },
    "high_apy_warning": {
      "trigger": "APY > 15%",
      "warning": "High APY often indicates higher risk. This vault may involve: leveraged strategies, newer protocols, or higher volatility assets. Proceed with caution.",
      "include_in_comparison": true
    },
    "first_time_warning": {
      "trigger": "User's first lending transaction",
      "warning": "Before your first lending transaction:\n- Start with a small amount\n- Verify vault/pool addresses\n- Understand you can lose funds if liquidated\n- Keep some funds for gas fees",
      "include_once": true
    },
    "large_amount_warning": {
      "trigger": "Transaction > 50% of wallet balance",
      "warning": "You're about to supply more than 50% of your {asset} balance. Consider keeping reserves for gas and emergencies.",
      "include_before_confirmation": true
    }
  }
}
```

---

## 10. Agent Coordination Data Structures

### Shared Context Schema

```json
{
  "agent_context_schema": {
    "user_context": {
      "is_authenticated": "boolean",
      "wallet_address": "string | null",
      "wallet_balance": "Record<string, number>",
      "gas_balance_eth": "number",
      "risk_tolerance": "low | medium | high",
      "preferred_chain": "ethereum | base | arbitrum | polygon",
      "language": "en | es | pt | zh"
    },
    "position_context": {
      "total_collateral_usd": "number",
      "total_debt_usd": "number",
      "health_factor": "number",
      "current_ltv": "number",
      "positions": [{
        "protocol": "aave | morpho | compound",
        "chain": "string",
        "asset": "string",
        "amount": "number",
        "apy": "number",
        "type": "supply | borrow"
      }]
    },
    "market_context": {
      "current_rates": [{
        "protocol": "string",
        "asset": "string",
        "supply_apy": "number",
        "borrow_apy": "number",
        "tvl": "number"
      }],
      "best_opportunity": {
        "protocol": "string",
        "asset": "string",
        "apy": "number"
      }
    }
  }
}
```

### Inter-Agent Communication

```json
{
  "agent_outputs": {
    "market_scanner": {
      "output_type": "MarketData",
      "fields": ["top_vaults", "rate_comparison", "best_opportunity", "risk_tiers"]
    },
    "risk_guardian": {
      "output_type": "RiskReport",
      "fields": ["health_factor", "risk_level", "action_required", "recommended_repayment", "price_scenarios"]
    },
    "executor": {
      "output_type": "TxResult",
      "fields": ["tx_hash", "status", "new_position", "new_health_factor", "gas_used"]
    },
    "optimizer": {
      "output_type": "OptimizationPlan",
      "fields": ["current_apy", "optimized_apy", "steps", "gas_estimate", "risk_assessment"]
    }
  }
}
```

---

## Related Documentation

- **Agent Prompts**: `/docs/ceo/agents/lending/agent_prompts.md`
- **Shortcuts Configuration**: `/docs/ceo/agents/lending/shortcuts_update.md`
- **Lending Protocol Implementation**: `/docs/steering/lending-protocols-implementation.md`
- **Knowledge Injector**: `/src/app/application/chat/services/knowledge_injector.py`
