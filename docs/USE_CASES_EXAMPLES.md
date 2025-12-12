# Anvil Platform: Enterprise-Grade Use Cases & Examples

**Version:** 2.0.0 (Based on Actual Implementation)
**Date:** December 12, 2025
**Platform:** Anvil DeFi Intelligence Platform
**Architecture:** Hexagonal (Clean Architecture) with CQRS, FastAPI, SQLAlchemy, Redis, Celery

---

## 📖 TABLE OF CONTENTS

1. [Executive Overview](#executive-overview)
2. [Platform Capabilities Matrix](#capabilities-matrix)
3. [Agent Squad Use Cases](#agent-squad-use-cases)
4. [Agno DeFi Agents](#agno-agents)
5. [MCP Server Integrations](#mcp-integrations)
6. [Hunter AI Use Cases](#hunter-ai-use-cases)
7. [Portfolio Management](#portfolio-management)
8. [DeFi Protocol Operations](#defi-operations)
9. [Cross-Chain Operations](#cross-chain-operations)
10. [Risk Management & Analysis](#risk-management)
11. [Projects (Customizable AI Containers)](#projects)
12. [GraphRAG Protocol Search](#graphrag)
13. [Real-Time Features](#real-time-features)
14. [Enterprise Features](#enterprise-features)
15. [API Reference Examples](#api-examples)

---

## 🎯 EXECUTIVE OVERVIEW {#executive-overview}

Anvil is an enterprise-grade DeFi intelligence platform that combines:

- **18 Specialized Agents** (Agent Squad) for domain-specific tasks
- **5 Operational DeFi Agents** (Agno) for autonomous portfolio management
- **13 MCP Protocol Servers** for real-time blockchain data
- **Hunter AI** for sentiment analysis, risk scoring, and price predictions
- **GraphRAG** for semantic protocol relationship search
- **Multi-Chain Portfolio Tracking** (Ethereum, Base, Arbitrum, Polygon, Optimism, Bitcoin)
- **6 DeFi Protocol Integrations** (Aave, Curve, Morpho, Hyperliquid, Axelar, LayerZero)
- **NFT Portfolio Management** (OpenSea integration)
- **Real-Time Alerts & WebSocket Streaming**
- **Projects System** for multi-tenant customizable AI containers

### Key Differentiators

1. **AI-First Architecture**: Every feature powered by specialized AI agents with domain expertise
2. **Real-Time Intelligence**: WebSocket streaming, live alerts, continuous risk monitoring
3. **Multi-Chain Native**: Unified view across 5+ EVM chains + Bitcoin
4. **Enterprise-Ready**: Multi-tenant projects, role-based access, compliance monitoring
5. **Production-Grade**: Hexagonal architecture, CQRS, dependency injection, comprehensive testing

---

## 🚀 PLATFORM CAPABILITIES MATRIX {#capabilities-matrix}

| Category | Free Tier | Pro Tier | Enterprise Tier |
|----------|-----------|----------|-----------------|
| **Agent Squad** | 5 agents | 10 agents | 18 agents |
| **Agno DeFi Agents** | ❌ | Limited | Full Access |
| **MCP Servers** | 3 servers | 8 servers | 13 servers |
| **Hunter AI** | Basic sentiment | Full sentiment + Risk | All features + Predictions |
| **Portfolio Tracking** | 1 wallet | 5 wallets | Unlimited |
| **Chains Supported** | Ethereum | Ethereum + 2 L2s | All chains (5 EVM + BTC) |
| **DeFi Protocols** | Read-only | Read + Execute | Full + Advanced |
| **Risk Analysis** | Basic | Advanced | Cascade Simulation |
| **Projects** | 1 project | 3 projects | Unlimited |
| **WebSocket Streaming** | ✅ | ✅ | ✅ |
| **Alerts** | Email only | Email + Push | Multi-channel + Custom |
| **GraphRAG Search** | 10 queries/day | 100 queries/day | Unlimited |
| **Support** | Community | Email | Priority + Dedicated |

---

## 🤖 AGENT SQUAD USE CASES {#agent-squad-use-cases}

The Agent Squad consists of 18 specialized AI agents, each optimized for specific tasks using tailored LLM models and prompts.

### Agent Tiers

**Free Tier (5 Agents):**
1. **Chat Agent** - General conversational AI
2. **Hunter AI** - Market sentiment & predictions
3. **Research Assistant** - Protocol/token research
4. **Portfolio Manager** - Portfolio tracking
5. **Gas Optimizer** - Transaction cost optimization

**Pro Tier (+5 Agents = 10 Total):**
6. **Transaction Executor** - Execute swaps, stakes, bridges
7. **Risk Analyzer** - Portfolio risk assessment
8. **Tax Optimizer** - Tax-loss harvesting & reporting
9. **DeFi Yield Optimizer** - Find & optimize yield
10. **Security Auditor** - Smart contract security

**Enterprise Tier (+8 Agents = 18 Total):**
11. **Compliance Monitor** - AML/KYC & regulatory
12. **Multi-Sig Coordinator** - Treasury management
13. **Alert & Monitoring** - Real-time anomaly detection
14. **Crisis Manager** - Emergency response
15. **Bridge & Cross-Chain** - Cross-chain operations
16. **Lending & Borrowing** - Leverage optimization
17. **NFT & Asset Manager** - NFT portfolio management
18. **DAO Governance** - Voting & proposal management

---

### Use Case 1: Intelligent Query Routing with Agent Squad

**Scenario**: User asks a complex question that requires multiple types of expertise.

#### API Request

```bash
POST /api/v1/chat/agent-squad/messages
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "conversation_id": "conv_123",
  "message": "What's the risk of my current DeFi positions and how can I optimize my yield while reducing exposure to smart contract vulnerabilities?",
  "context": {
    "wallet_address": "0xabc...123",
    "include_portfolio": true
  }
}
```

#### Platform Processing

1. **Intent Classification** (50-100ms):
   - Primary intent: Risk analysis
   - Secondary intent: Yield optimization
   - Tertiary intent: Security assessment

2. **Agent Selection** (20-50ms):
   - Primary: **Risk Analyzer**
   - Support: **DeFi Yield Optimizer**
   - Support: **Security Auditor**

3. **Parallel Execution** (2-5s):
   - Risk Analyzer fetches portfolio + calculates risk scores
   - Yield Optimizer searches across protocols (via MCP servers)
   - Security Auditor checks contract audit status

4. **Response Synthesis** (100-200ms):
   - Aggregates results from 3 agents
   - Generates unified recommendation
   - Streams response via WebSocket

#### API Response

```json
{
  "message_id": "msg_456",
  "agents_used": ["risk_analyzer", "defi_yield", "security_auditor"],
  "processing_time_ms": 3240,
  "response": {
    "summary": "Your portfolio has elevated smart contract risk (Score: 68/100) primarily from Curve Finance pools. I've identified 3 lower-risk alternatives with comparable yields.",
    "sections": [
      {
        "agent": "risk_analyzer",
        "title": "Portfolio Risk Assessment",
        "content": {
          "overall_risk_score": 68,
          "risk_level": "MEDIUM_HIGH",
          "breakdown": {
            "smart_contract_risk": {
              "score": 72,
              "level": "HIGH",
              "details": "60% of portfolio in unaudited Curve pools",
              "positions_at_risk": [
                {
                  "protocol": "Curve Finance",
                  "pool": "stETH/ETH",
                  "value_usd": 45000,
                  "risk_score": 75,
                  "audit_status": "Partially audited",
                  "last_audit": "2024-03-15"
                }
              ]
            },
            "liquidity_risk": {
              "score": 42,
              "level": "LOW",
              "details": "All positions in deep liquidity pools"
            },
            "correlation_risk": {
              "score": 65,
              "level": "MEDIUM",
              "details": "High correlation between ETH-denominated positions"
            }
          },
          "recommendations": [
            "Reduce exposure to unaudited Curve pools from 60% to <30%",
            "Diversify into audited protocols (Aave, Morpho)",
            "Consider stablecoin positions to reduce correlation risk"
          ]
        }
      },
      {
        "agent": "defi_yield",
        "title": "Safer High-Yield Alternatives",
        "content": {
          "alternatives": [
            {
              "protocol": "Morpho",
              "vault": "Steakhouse USDC",
              "current_apy": 8.2,
              "risk_score": 28,
              "audit_status": "Fully audited (4 firms)",
              "liquidity": "Excellent ($450M TVL)",
              "recommendation": "Migrate $30K from Curve to reduce smart contract risk",
              "migration_cost": {
                "gas_estimate": "$45",
                "slippage_estimate": "0.02%",
                "total_cost_usd": 47
              }
            },
            {
              "protocol": "Aave V3",
              "market": "USDC (Ethereum)",
              "current_apy": 7.8,
              "risk_score": 22,
              "audit_status": "Fully audited (6 firms)",
              "liquidity": "Excellent ($1.2B)",
              "recommendation": "Conservative allocation for $20K"
            },
            {
              "protocol": "Curve Finance",
              "pool": "3pool (USDC/USDT/DAI)",
              "current_apy": 6.5,
              "risk_score": 35,
              "audit_status": "Fully audited (3 firms)",
              "liquidity": "Excellent ($800M TVL)",
              "note": "Lower risk than stETH pool, still Curve exposure"
            }
          ],
          "optimized_allocation": {
            "target_risk_score": 45,
            "expected_apy": 7.6,
            "allocation": {
              "Morpho USDC": "40%",
              "Aave V3 USDC": "30%",
              "Curve 3pool": "20%",
              "Curve stETH/ETH": "10%"
            },
            "vs_current": {
              "risk_reduction": "-33%",
              "yield_impact": "-0.8%",
              "recommended": true
            }
          }
        }
      },
      {
        "agent": "security_auditor",
        "title": "Security Assessment",
        "content": {
          "audit_summary": {
            "fully_audited": "40%",
            "partially_audited": "60%",
            "unaudited": "0%"
          },
          "high_priority_concerns": [
            {
              "protocol": "Curve Finance",
              "contract": "stETH/ETH pool",
              "issue": "No recent audit (>12 months old)",
              "severity": "MEDIUM",
              "recommendation": "Monitor closely or reduce exposure",
              "audit_firms": ["Trail of Bits (2023-03)"],
              "known_exploits": "None",
              "tvl_at_risk": "$45,000"
            }
          ],
          "recommendations": [
            "Prioritize protocols with recent audits (<6 months)",
            "Diversify across audit firms (don't rely on single auditor)",
            "Set up smart contract risk alerts for your positions"
          ],
          "monitoring": {
            "suggested_alerts": [
              "TVL drops >20% in 24h (possible exploit)",
              "Unusual contract interactions (possible attack)",
              "New audit reports published",
              "Critical CVE disclosures"
            ],
            "setup_command": "I can set these up for you automatically. Reply 'enable security alerts' to activate."
          }
        }
      }
    ],
    "action_items": [
      {
        "priority": "HIGH",
        "action": "Migrate $30K from Curve stETH/ETH to Morpho USDC vault",
        "rationale": "Reduces smart contract risk by 25 points while maintaining 8.2% APY",
        "estimated_time": "15 minutes",
        "estimated_cost": "$47 (gas + slippage)",
        "commands": [
          "/agent execute withdraw 30000 from curve stETH/ETH",
          "/agent execute deposit 30000 to morpho usdc-vault"
        ]
      },
      {
        "priority": "MEDIUM",
        "action": "Allocate $20K to Aave V3 USDC",
        "rationale": "Ultra-low risk (score: 22) with solid 7.8% yield",
        "estimated_time": "10 minutes",
        "estimated_cost": "$35"
      },
      {
        "priority": "LOW",
        "action": "Enable security monitoring alerts",
        "rationale": "Proactive protection against exploits",
        "estimated_time": "2 minutes",
        "estimated_cost": "Free"
      }
    ],
    "next_steps": {
      "immediate": "I can execute the Morpho migration now if you approve. This will:",
      "steps": [
        "1. Withdraw $30K from Curve stETH/ETH pool",
        "2. Swap to USDC (if needed)",
        "3. Deposit to Morpho Steakhouse USDC vault",
        "4. Set up security alerts for all positions"
      ],
      "approval_required": true,
      "approval_command": "/agent approve migration-plan-001"
    }
  },
  "metadata": {
    "total_agents_invoked": 3,
    "mcp_servers_used": [
      "defillama",
      "curve",
      "morpho",
      "aave"
    ],
    "processing_breakdown": {
      "intent_classification": "85ms",
      "agent_selection": "42ms",
      "portfolio_fetch": "520ms",
      "risk_analysis": "1240ms",
      "yield_search": "980ms",
      "security_audit": "740ms",
      "response_synthesis": "175ms"
    },
    "cache_hit": false,
    "model_used": "gemini-1.5-pro"
  }
}
```

**Key Features Demonstrated:**
- ✅ Multi-agent orchestration (3 specialists)
- ✅ Parallel execution for performance
- ✅ MCP server integration (4 protocols)
- ✅ Risk scoring with actionable recommendations
- ✅ Cost estimation (gas + slippage)
- ✅ Security audit status tracking
- ✅ Action items with priority levels
- ✅ Approval workflow for execution

---

### Use Case 2: Supervisor-Coordinated Complex Workflow

**Scenario**: User wants comprehensive portfolio optimization across multiple dimensions.

#### API Request

```bash
POST /api/v1/chat/agent-squad/supervisor
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "task": "Optimize my entire portfolio for maximum risk-adjusted returns while maintaining tax efficiency and ensuring compliance",
  "context": {
    "wallet_address": "0xabc...123",
    "jurisdiction": "US",
    "tax_year": 2025,
    "risk_tolerance": "moderate",
    "time_horizon": "12_months"
  },
  "preferences": {
    "max_gas_budget": 500,
    "min_yield_improvement": 1.5,
    "exclude_protocols": ["leverage_protocols"]
  }
}
```

#### Supervisor Execution Plan

The **Supervisor Agent** breaks down the task into subtasks and coordinates 6 agents in parallel:

```
Task Decomposition:
├─ [1] Risk Analyzer: Assess current risk profile
├─ [2] Portfolio Manager: Calculate current performance metrics
├─ [3] DeFi Yield Optimizer: Find better yield opportunities
├─ [4] Tax Optimizer: Identify tax-loss harvesting opportunities
├─ [5] Compliance Monitor: Check regulatory constraints
└─ [6] Gas Optimizer: Estimate and optimize transaction costs

Execution Order:
Phase 1 (Parallel): Agents 1, 2, 5 (data gathering)
Phase 2 (Parallel): Agents 3, 4 (optimization)
Phase 3 (Sequential): Agent 6 (execution planning)
Phase 4 (Synthesis): Supervisor aggregates results
```

#### API Response

```json
{
  "task_id": "task_789",
  "status": "completed",
  "execution_time_ms": 6850,
  "agents_executed": 6,
  "subtasks_completed": 12,
  "result": {
    "executive_summary": {
      "current_state": {
        "total_value_usd": 125450,
        "risk_score": 62,
        "risk_level": "MEDIUM_HIGH",
        "current_apy": 8.4,
        "risk_adjusted_return": 0.135,
        "tax_efficiency": "LOW (multiple short-term gains)",
        "compliance_status": "COMPLIANT"
      },
      "optimized_state": {
        "projected_value_usd": 125450,
        "risk_score": 45,
        "risk_level": "MEDIUM",
        "projected_apy": 9.2,
        "risk_adjusted_return": 0.204,
        "tax_savings": 1850,
        "compliance_status": "COMPLIANT"
      },
      "improvements": {
        "risk_reduction": "-27%",
        "yield_increase": "+0.8%",
        "risk_adjusted_return_increase": "+51%",
        "tax_savings_usd": 1850,
        "total_execution_cost_usd": 385,
        "net_benefit_first_year": 2465
      },
      "recommendation": "STRONGLY RECOMMENDED - Significant improvement in risk-adjusted returns with tax benefits"
    },
    "detailed_analysis": {
      "risk_assessment": {
        "agent": "risk_analyzer",
        "current_exposures": {
          "smart_contract_risk": "HIGH (68/100)",
          "liquidity_risk": "LOW (32/100)",
          "market_risk": "MEDIUM (58/100)",
          "concentration_risk": "HIGH (72/100) - 60% in single asset (ETH)"
        },
        "recommended_changes": {
          "reduce_eth_concentration": "60% → 40%",
          "add_stablecoin_exposure": "8% → 25%",
          "diversify_protocols": "3 → 6 protocols"
        }
      },
      "yield_optimization": {
        "agent": "defi_yield",
        "opportunities_found": 12,
        "top_recommendations": [
          {
            "action": "Migrate USDC from Aave V2 to Morpho USDC vault",
            "from": {
              "protocol": "Aave V2",
              "apy": 5.2,
              "risk_score": 35
            },
            "to": {
              "protocol": "Morpho",
              "vault": "Steakhouse USDC",
              "apy": 8.2,
              "risk_score": 28
            },
            "improvement": {
              "yield_increase": "+3.0%",
              "risk_reduction": "-20%",
              "amount_usd": 25000,
              "annual_gain_usd": 750
            }
          },
          {
            "action": "Add Curve 3pool position",
            "from": null,
            "to": {
              "protocol": "Curve",
              "pool": "3pool",
              "apy": 6.5,
              "risk_score": 35
            },
            "improvement": {
              "diversification": "+15%",
              "amount_usd": 15000,
              "annual_gain_usd": 975
            }
          }
        ],
        "total_yield_improvement": "+0.8% APY",
        "projected_annual_gain": 1850
      },
      "tax_optimization": {
        "agent": "tax_optimizer",
        "strategy": "Tax-Loss Harvesting + Long-Term Capital Gains",
        "opportunities": [
          {
            "type": "tax_loss_harvesting",
            "asset": "UNI",
            "current_value": 8200,
            "cost_basis": 9500,
            "unrealized_loss": -1300,
            "action": "Sell and immediately buy back (wash sale compliant)",
            "tax_savings": 286,
            "holding_period": "42 days (short-term)"
          },
          {
            "type": "long_term_conversion",
            "asset": "ETH",
            "current_value": 75000,
            "cost_basis": 52000,
            "unrealized_gain": 23000,
            "holding_period": "348 days",
            "action": "HOLD for 17 more days to qualify for long-term rates",
            "tax_savings": 4600,
            "note": "20% long-term vs 37% short-term rate"
          },
          {
            "type": "staking_optimization",
            "asset": "ETH",
            "action": "Stake via Lido to defer taxes while earning yield",
            "amount": 30000,
            "projected_staking_yield": 4.2,
            "tax_deferral_benefit": "Defer $1200 in taxes until unstaking"
          }
        ],
        "total_tax_savings": 1850,
        "irs_compliance": "COMPLIANT - All strategies IRS-approved"
      },
      "compliance_check": {
        "agent": "compliance_monitor",
        "jurisdiction": "United States",
        "regulations_checked": [
          "SEC securities regulations",
          "FinCEN AML/KYC",
          "IRS tax reporting (Form 8949, Schedule D)",
          "State money transmitter licenses"
        ],
        "status": "FULLY_COMPLIANT",
        "findings": [
          {
            "regulation": "SEC - Staking as a Service",
            "status": "COMPLIANT",
            "note": "Using non-custodial staking (Lido) - not subject to SEC scrutiny"
          },
          {
            "regulation": "FinCEN - AML/KYC",
            "status": "COMPLIANT",
            "note": "All transactions below $10K reporting threshold"
          },
          {
            "regulation": "IRS - Form 8949",
            "status": "ATTENTION_REQUIRED",
            "note": "15 taxable events this year - ensure accurate cost basis tracking",
            "action": "I can generate Form 8949 export for your tax preparer"
          }
        ],
        "warnings": [
          "Ensure you report all DeFi income on Form 1040 Schedule 1",
          "Staking rewards are taxable as income when received",
          "Gas fees can be deducted as investment expenses (itemized)"
        ]
      },
      "execution_plan": {
        "agent": "gas_optimizer",
        "optimal_execution_time": "2025-12-12T03:30:00Z (3:30 AM UTC)",
        "rationale": "Lowest gas prices typically occur 2-4 AM UTC",
        "total_transactions": 8,
        "estimated_costs": {
          "current_gas_price": "35 gwei",
          "optimal_gas_price": "15 gwei (estimated)",
          "cost_if_executed_now": 615,
          "cost_if_executed_optimal": 385,
          "savings": 230
        },
        "transaction_sequence": [
          {
            "step": 1,
            "action": "Sell UNI for tax-loss harvesting",
            "gas_estimate": 45,
            "priority": "HIGH",
            "reason": "Realize tax loss before year-end"
          },
          {
            "step": 2,
            "action": "Buy back UNI (wash sale compliant)",
            "gas_estimate": 42,
            "priority": "HIGH",
            "delay": "31 days to avoid wash sale rule"
          },
          {
            "step": 3,
            "action": "Withdraw USDC from Aave V2",
            "gas_estimate": 55,
            "priority": "MEDIUM"
          },
          {
            "step": 4,
            "action": "Deposit USDC to Morpho vault",
            "gas_estimate": 68,
            "priority": "MEDIUM"
          },
          {
            "step": 5,
            "action": "Stake ETH via Lido",
            "gas_estimate": 75,
            "priority": "LOW",
            "note": "Optional - provides yield + tax deferral"
          },
          {
            "step": 6,
            "action": "Add liquidity to Curve 3pool",
            "gas_estimate": 95,
            "priority": "LOW"
          }
        ],
        "batching_opportunities": {
          "batch_1": "Steps 3 + 4 can be combined via multi-call",
          "savings": 25,
          "new_cost": 98
        },
        "final_cost_estimate": 360
      }
    },
    "recommended_actions": [
      {
        "priority": "CRITICAL",
        "action": "HOLD ETH for 17 more days",
        "rationale": "Qualifies for long-term capital gains (save $4,600 in taxes)",
        "deadline": "2025-12-29",
        "cost": 0,
        "benefit": 4600,
        "approval_required": false,
        "automated": false
      },
      {
        "priority": "HIGH",
        "action": "Tax-loss harvest UNI (sell at loss)",
        "rationale": "Realize $1,300 loss to offset gains (save $286 in taxes)",
        "deadline": "2025-12-31",
        "cost": 45,
        "benefit": 286,
        "approval_required": true,
        "automated": true,
        "command": "/agent execute tax-harvest UNI 8200"
      },
      {
        "priority": "HIGH",
        "action": "Migrate USDC: Aave V2 → Morpho",
        "rationale": "+3.0% yield, -20% risk, $750/year benefit",
        "deadline": "2026-01-15",
        "cost": 98,
        "benefit": 750,
        "approval_required": true,
        "automated": true
      },
      {
        "priority": "MEDIUM",
        "action": "Add Curve 3pool liquidity ($15K)",
        "rationale": "Diversification + 6.5% yield",
        "cost": 95,
        "benefit": 975,
        "approval_required": true
      },
      {
        "priority": "LOW",
        "action": "Stake ETH via Lido ($30K)",
        "rationale": "4.2% yield + tax deferral",
        "cost": 75,
        "benefit": 1260,
        "approval_required": true
      }
    ],
    "execution_summary": {
      "total_cost": 360,
      "total_benefit_year_1": 7871,
      "net_benefit": 7511,
      "roi": "2087%",
      "execution_time": "~45 minutes",
      "approval_required_count": 4,
      "approval_command": "/agent approve optimization-plan-789"
    }
  },
  "metadata": {
    "supervisor_agent": "multi_agent_supervisor",
    "agents_orchestrated": [
      "risk_analyzer",
      "portfolio_manager",
      "defi_yield",
      "tax_optimizer",
      "compliance_monitor",
      "gas_optimizer"
    ],
    "execution_phases": 4,
    "parallel_executions": 8,
    "sequential_executions": 4,
    "mcp_servers_used": [
      "defillama",
      "coingecko",
      "aave",
      "morpho",
      "curve",
      "1inch"
    ],
    "total_api_calls": 47,
    "cache_hits": 12,
    "cache_hit_rate": "25.5%"
  }
}
```

**Key Features Demonstrated:**
- ✅ Supervisor-coordinated multi-agent workflow
- ✅ 6 specialized agents working in parallel
- ✅ Tax optimization (loss harvesting, long-term gains)
- ✅ Compliance checking (SEC, FinCEN, IRS)
- ✅ Gas optimization with timing recommendations
- ✅ ROI calculation (2087% return on execution costs)
- ✅ Approval workflow with detailed breakdown
- ✅ Batching optimization to reduce gas costs

---

## 🔧 AGNO DEFI AGENTS {#agno-agents}

Anvil includes 5 **Agno** operational DeFi agents that autonomously execute trades and manage positions:

1. **TradingAgent** - Autonomous DEX trading with limit orders
2. **LendingAgent** - Auto-rebalancing across lending protocols
3. **PerpetualAgent** - Futures trading with risk management
4. **AnalyticsAgent** - Continuous market monitoring
5. **PortfolioAgent** - Automated portfolio rebalancing

### Use Case 3: Automated Yield Optimization with LendingAgent

**Scenario**: User wants to automatically move funds to highest-yield lending opportunities.

#### Setup Request

```bash
POST /api/v1/agno/lending-agent/configure
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "enabled": true,
  "strategy": {
    "target_protocols": ["aave", "morpho", "curve"],
    "target_assets": ["USDC", "USDT", "DAI"],
    "min_yield_improvement": 1.5,
    "max_risk_score": 50,
    "rebalance_frequency": "daily",
    "max_gas_per_rebalance": 100
  },
  "constraints": {
    "never_withdraw_all": true,
    "min_position_size": 1000,
    "max_single_protocol": 0.4,
    "require_audit": true
  },
  "notifications": {
    "on_rebalance": true,
    "on_error": true,
    "on_opportunity": true
  }
}
```

#### Agent Autonomous Execution Log

```json
{
  "agent": "lending_agent",
  "execution_date": "2025-12-12T10:30:00Z",
  "trigger": "daily_scheduled_check",
  "analysis": {
    "current_positions": [
      {
        "protocol": "Aave V3",
        "asset": "USDC",
        "balance": 25000,
        "apy": 5.8,
        "risk_score": 22
      },
      {
        "protocol": "Curve",
        "pool": "3pool",
        "asset": "USDC",
        "balance": 15000,
        "apy": 6.2,
        "risk_score": 35
      }
    ],
    "opportunities_found": 3,
    "selected_opportunity": {
      "action": "migrate",
      "from": {
        "protocol": "Aave V3",
        "asset": "USDC",
        "current_apy": 5.8
      },
      "to": {
        "protocol": "Morpho",
        "vault": "Steakhouse USDC",
        "projected_apy": 8.4,
        "risk_score": 28
      },
      "amount": 15000,
      "improvement": {
        "yield_increase_pct": 2.6,
        "annual_gain_usd": 390,
        "risk_change": "+6 points (acceptable)",
        "meets_criteria": true
      },
      "execution_plan": {
        "gas_estimate": 85,
        "slippage_estimate": 0.01,
        "total_cost": 88.50,
        "payback_period": "82 days",
        "approved": true
      }
    }
  },
  "execution": {
    "status": "completed",
    "transactions": [
      {
        "step": 1,
        "action": "withdraw",
        "protocol": "Aave V3",
        "amount": 15000,
        "tx_hash": "0xdef456...",
        "gas_used": 42.3,
        "status": "confirmed",
        "timestamp": "2025-12-12T10:32:15Z"
      },
      {
        "step": 2,
        "action": "deposit",
        "protocol": "Morpho",
        "vault": "Steakhouse USDC",
        "amount": 15000,
        "tx_hash": "0xabc789...",
        "gas_used": 46.2,
        "status": "confirmed",
        "timestamp": "2025-12-12T10:33:42Z"
      }
    ],
    "total_gas_cost": 88.50,
    "execution_time": "87 seconds",
    "success": true
  },
  "post_execution": {
    "new_portfolio": {
      "total_value": 40000,
      "weighted_avg_apy": 7.52,
      "weighted_avg_risk": 29.25,
      "protocol_distribution": {
        "Aave V3": "25%",
        "Morpho": "37.5%",
        "Curve 3pool": "37.5%"
      }
    },
    "vs_previous": {
      "apy_improvement": "+1.12%",
      "risk_change": "+3 points",
      "diversification_score": "improved"
    }
  },
  "notification_sent": {
    "channel": "email",
    "subject": "LendingAgent executed yield optimization",
    "summary": "Moved $15K from Aave to Morpho. New APY: 7.52% (+1.12%). Gas cost: $88.50. Annual benefit: $390."
  }
}
```

**Key Features:**
- ✅ Autonomous execution (no user intervention)
- ✅ Multi-protocol monitoring (Aave, Morpho, Curve)
- ✅ Risk-aware optimization (max risk score: 50)
- ✅ Cost-benefit analysis (payback period: 82 days)
- ✅ Automatic notifications
- ✅ Safety constraints (never withdraw all, min position size)

---

### Use Case 4: Perpetual Trading with Risk Management (PerpetualAgent)

**Scenario**: Automated perpetual futures trading on Hyperliquid with stop-loss and take-profit.

#### Configuration

```bash
POST /api/v1/agno/perpetual-agent/strategy
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "strategy_name": "ETH Long Momentum",
  "enabled": true,
  "market": "ETH-PERP",
  "exchange": "hyperliquid",
  "parameters": {
    "direction": "long_bias",
    "entry_conditions": {
      "sentiment_threshold": 65,
      "momentum_signal": "bullish",
      "funding_rate_max": 0.05
    },
    "position_sizing": {
      "max_position_size_usd": 50000,
      "leverage": 3,
      "position_percent_of_portfolio": 0.15
    },
    "risk_management": {
      "stop_loss_pct": 2.5,
      "take_profit_pct": 8.0,
      "trailing_stop": true,
      "trailing_stop_activation": 5.0,
      "max_drawdown_daily": 5.0
    },
    "execution": {
      "order_type": "limit",
      "slippage_tolerance": 0.1,
      "time_in_force": "GTC"
    }
  }
}
```

#### Agent Execution

```json
{
  "agent": "perpetual_agent",
  "strategy": "ETH Long Momentum",
  "timestamp": "2025-12-12T14:22:00Z",
  "event": "position_opened",
  "market_analysis": {
    "eth_price": 3850,
    "sentiment_score": 72,
    "momentum": "strong_bullish",
    "funding_rate": 0.032,
    "hunter_ai_prediction": {
      "24h_forecast": 3980,
      "confidence": 78,
      "signal": "BUY"
    },
    "decision": "OPEN_LONG"
  },
  "position": {
    "entry_price": 3850,
    "size_usd": 45000,
    "size_eth": 11.688,
    "leverage": 3,
    "margin_required": 15000,
    "liquidation_price": 2567,
    "stop_loss": 3754,
    "take_profit": 4158,
    "trailing_stop_activation": 4043
  },
  "risk_metrics": {
    "position_risk_score": 55,
    "portfolio_impact": "14.8% of total portfolio",
    "max_loss_usd": 1125,
    "max_loss_pct": 2.5,
    "reward_risk_ratio": 3.2,
    "liquidation_buffer": "33.3%"
  },
  "execution_details": {
    "order_type": "limit",
    "limit_price": 3850,
    "filled_price": 3848,
    "slippage_actual": -0.05,
    "tx_hash": "0xhyperliquid123...",
    "gas_cost": 0,
    "exchange_fee": 18,
    "total_cost": 18
  },
  "monitoring": {
    "check_frequency": "every_30_seconds",
    "alerts_enabled": [
      "stop_loss_hit",
      "take_profit_hit",
      "trailing_stop_activated",
      "liquidation_warning_10pct"
    ]
  }
}
```

#### Automatic Position Management (30 minutes later)

```json
{
  "agent": "perpetual_agent",
  "event": "trailing_stop_activated",
  "timestamp": "2025-12-12T14:52:00Z",
  "position_update": {
    "current_price": 4055,
    "pnl_usd": 2400,
    "pnl_pct": 5.33,
    "trailing_stop_activated": true,
    "new_stop_loss": 3851,
    "reason": "Price reached +5.33%, activating trailing stop 5% below current price"
  },
  "action": "hold_and_monitor"
}
```

#### Position Close (2 hours later)

```json
{
  "agent": "perpetual_agent",
  "event": "position_closed",
  "timestamp": "2025-12-12T16:45:00Z",
  "trigger": "take_profit_hit",
  "exit_details": {
    "exit_price": 4160,
    "holding_period": "2h 23m",
    "pnl_gross": 3625,
    "fees_total": 36,
    "pnl_net": 3589,
    "roi": 7.98
  },
  "performance": {
    "vs_prediction": "Exceeded Hunter AI forecast by 4.5%",
    "risk_adjusted_return": 1.45,
    "sharpe_ratio": 2.8,
    "max_drawdown": 0.8
  },
  "notification": {
    "title": "🎯 Take Profit Hit - ETH Long Closed",
    "message": "Closed ETH-PERP long at $4,160. Profit: $3,589 (+7.98%) in 2h 23m. Strategy: ETH Long Momentum.",
    "channels": ["push", "email"]
  }
}
```

**Key Features:**
- ✅ Autonomous entry based on sentiment + momentum
- ✅ Leverage management (3x with liquidation buffer)
- ✅ Automatic stop-loss and take-profit
- ✅ Trailing stop activation at +5%
- ✅ Real-time risk monitoring (every 30 seconds)
- ✅ Hunter AI integration for entry signals
- ✅ Performance tracking (7.98% ROI in 2h 23m)

---

## 🔌 MCP SERVER INTEGRATIONS {#mcp-integrations}

Anvil integrates **13 MCP (Model Context Protocol) servers** for real-time blockchain data:

1. **DeFiLlama** - Protocol TVL, yields, volume
2. **CoinGecko** - Price data, market cap, rankings
3. **TheGraph** - On-chain data indexing
4. **1inch** - DEX aggregation and routing
5. **Perplexity** - AI-powered web search
6. **Aave** - Lending protocol data
7. **Curve** - Curve Finance pools and gauges
8. **Morpho** - Morpho vaults and markets
9. **Hyperliquid** - Perpetual futures data
10. **LayerZero** - Cross-chain messaging
11. **Axelar** - Cross-chain bridging
12. **Portfolio** - Multi-chain portfolio tracking
13. **Others** (custom MCP servers)

### Use Case 5: Multi-Protocol Yield Comparison via MCP Servers

**API Request:**

```bash
GET /api/v1/defi/morpho/compare?protocols=aave,curve,morpho&asset=USDC&chain=ethereum&sort_by=apy
Authorization: Bearer <jwt_token>
```

**Behind the Scenes (MCP Server Orchestration):**

```python
# Parallel MCP server calls
async def compare_yields():
    # Call 3 MCP servers simultaneously
    tasks = [
        mcp_aave.get_market_data("USDC", "ethereum"),
        mcp_curve.get_pool_apy("3pool"),
        mcp_morpho.get_vault_apy("steakhouse-usdc")
    ]
    results = await asyncio.gather(*tasks)

    # Cross-reference with DeFiLlama for verification
    tvl_data = await mcp_defillama.get_protocol_tvls(["aave", "curve", "morpho"])

    return aggregate_and_rank(results, tvl_data)
```

**API Response:**

```json
{
  "comparison": {
    "asset": "USDC",
    "chain": "ethereum",
    "timestamp": "2025-12-12T10:00:00Z",
    "protocols_compared": 3,
    "data_sources": {
      "aave": "mcp_aave + defillama",
      "curve": "mcp_curve + defillama",
      "morpho": "mcp_morpho + defillama"
    },
    "results": [
      {
        "rank": 1,
        "protocol": "Morpho",
        "vault_name": "Steakhouse USDC",
        "apy": 8.4,
        "tvl": 450000000,
        "risk_score": 28,
        "audit_status": "Fully audited (4 firms)",
        "auditors": ["OpenZeppelin", "Trail of Bits", "ChainSecurity", "Zellic"],
        "last_audit": "2025-09-15",
        "yield_breakdown": {
          "base_rate": 4.2,
          "morpho_rewards": 2.8,
          "lido_staking": 1.4
        },
        "liquidity": {
          "total_liquidity": 450000000,
          "available_liquidity": 280000000,
          "utilization_rate": 37.8
        },
        "historical_apy": {
          "7d_avg": 8.6,
          "30d_avg": 8.1,
          "90d_avg": 7.9,
          "volatility": 0.4
        },
        "recommendation": "BEST_CHOICE",
        "reasons": [
          "Highest APY (8.4%)",
          "Lowest risk score (28)",
          "Most comprehensive audits (4 firms)",
          "Excellent liquidity ($280M available)"
        ],
        "action": {
          "endpoint": "/api/v1/defi/morpho/vaults/steakhouse-usdc",
          "deposit_command": "/agent execute deposit 25000 USDC to morpho steakhouse-usdc"
        }
      },
      {
        "rank": 2,
        "protocol": "Curve Finance",
        "pool_name": "3pool (USDC/USDT/DAI)",
        "apy": 6.5,
        "tvl": 800000000,
        "risk_score": 35,
        "audit_status": "Fully audited (3 firms)",
        "auditors": ["Trail of Bits", "Mixbytes", "ChainSecurity"],
        "last_audit": "2025-06-20",
        "yield_breakdown": {
          "trading_fees": 1.8,
          "crv_rewards": 3.2,
          "cvx_boost": 1.5
        },
        "liquidity": {
          "total_liquidity": 800000000,
          "pool_depth": 950000000,
          "utilization_rate": 84.2
        },
        "historical_apy": {
          "7d_avg": 6.8,
          "30d_avg": 6.4,
          "90d_avg": 6.2,
          "volatility": 0.6
        },
        "recommendation": "GOOD_ALTERNATIVE",
        "reasons": [
          "Ultra-deep liquidity ($950M)",
          "Battle-tested protocol (>3 years)",
          "Stable yields (low volatility)"
        ],
        "warnings": [
          "Slightly higher risk score vs Morpho",
          "APY 1.9% lower than Morpho"
        ]
      },
      {
        "rank": 3,
        "protocol": "Aave V3",
        "market_name": "USDC",
        "apy": 5.8,
        "tvl": 1200000000,
        "risk_score": 22,
        "audit_status": "Fully audited (6 firms)",
        "auditors": ["OpenZeppelin", "Trail of Bits", "SigmaPrime", "Peckshield", "ABDK", "Certora"],
        "last_audit": "2025-11-01",
        "yield_breakdown": {
          "base_supply_rate": 5.8,
          "aave_rewards": 0,
          "safety_module_bonus": 0
        },
        "liquidity": {
          "total_liquidity": 1200000000,
          "available_liquidity": 850000000,
          "utilization_rate": 29.2
        },
        "historical_apy": {
          "7d_avg": 5.9,
          "30d_avg": 5.7,
          "90d_avg": 5.6,
          "volatility": 0.2
        },
        "recommendation": "CONSERVATIVE_CHOICE",
        "reasons": [
          "Lowest risk score (22)",
          "Most audited protocol (6 firms)",
          "Largest TVL ($1.2B) - institutional grade",
          "Lowest yield volatility (0.2%)"
        ],
        "warnings": [
          "APY 2.6% lower than Morpho",
          "No protocol token rewards"
        ]
      }
    ],
    "summary": {
      "highest_apy": {
        "protocol": "Morpho",
        "apy": 8.4
      },
      "lowest_risk": {
        "protocol": "Aave V3",
        "risk_score": 22
      },
      "best_liquidity": {
        "protocol": "Aave V3",
        "liquidity": 850000000
      },
      "most_audited": {
        "protocol": "Aave V3",
        "auditors_count": 6
      },
      "recommended_allocation": {
        "strategy": "Risk-adjusted diversification",
        "allocation": {
          "Morpho": "50% (highest yield)",
          "Curve 3pool": "30% (deep liquidity)",
          "Aave V3": "20% (lowest risk)"
        },
        "weighted_avg_apy": 7.56,
        "weighted_avg_risk": 29.4,
        "rationale": "Maximizes yield (7.56%) while maintaining acceptable risk (29.4)"
      }
    },
    "data_freshness": {
      "aave_data_age": "45 seconds",
      "curve_data_age": "32 seconds",
      "morpho_data_age": "28 seconds",
      "defillama_data_age": "2 minutes",
      "all_data_fresh": true
    }
  },
  "mcp_performance": {
    "total_mcp_calls": 5,
    "parallel_calls": 3,
    "sequential_calls": 2,
    "total_time_ms": 1240,
    "breakdown": {
      "mcp_aave": "380ms",
      "mcp_curve": "420ms",
      "mcp_morpho": "310ms",
      "mcp_defillama": "580ms (2 calls)",
      "aggregation": "130ms"
    },
    "cache_hits": 1,
    "cache_misses": 4
  }
}
```

**Key Features:**
- ✅ Parallel MCP server queries (3 protocols simultaneously)
- ✅ Cross-verification with DeFiLlama
- ✅ Risk scoring and audit status
- ✅ Historical APY analysis (7d, 30d, 90d)
- ✅ Liquidity depth analysis
- ✅ Recommended allocation strategy
- ✅ Data freshness tracking (all <3 minutes)
- ✅ Performance metrics (1.24s total query time)

---

## 🎯 HUNTER AI USE CASES {#hunter-ai-use-cases}

Hunter AI provides ML-powered market intelligence with 4 core capabilities:

1. **Sentiment Analysis** - Multi-source sentiment tracking
2. **Risk Scoring** - ML-based risk assessment
3. **Price Predictions** - LSTM-based forecasting
4. **Trading Signals** - AI-generated trade recommendations

### Use Case 6: Comprehensive Token Analysis

**API Request:**

```bash
POST /api/v1/hunter/analyze
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "token_symbol": "UNI",
  "analysis_depth": "comprehensive",
  "include": [
    "sentiment",
    "risk",
    "price_prediction",
    "trading_signals",
    "whale_activity"
  ],
  "timeframe": "24h"
}
```

**API Response:**

```json
{
  "token": "UNI",
  "timestamp": "2025-12-12T16:00:00Z",
  "analysis": {
    "sentiment": {
      "overall_score": 72,
      "classification": "BULLISH",
      "confidence": 85,
      "trend": "INCREASING",
      "change_24h": 8,
      "sources": {
        "twitter": {
          "score": 75,
          "mentions_count": 8500,
          "positive_ratio": 0.68,
          "engagement_score": 82,
          "top_hashtags": ["#Uniswap", "#DeFi", "#UNI"],
          "influencer_sentiment": "Very bullish",
          "whale_accounts_sentiment": 78
        },
        "reddit": {
          "score": 68,
          "subreddit": "r/UniSwap",
          "total_karma": 12500,
          "positive_posts_ratio": 0.64,
          "trending_threads": 3
        },
        "discord": {
          "score": 70,
          "active_users": 2840,
          "message_sentiment": "Positive",
          "admin_activity": "High"
        },
        "news": {
          "score": 73,
          "articles_count": 12,
          "positive_count": 9,
          "neutral_count": 2,
          "negative_count": 1,
          "major_headlines": [
            "Uniswap V4 hooks gaining traction among developers",
            "UNI token sees increased institutional interest",
            "Uniswap Labs expands to 3 new chains"
          ]
        }
      },
      "sentiment_history": {
        "24h_ago": 64,
        "7d_ago": 58,
        "30d_ago": 55,
        "trend_direction": "strong_bullish"
      }
    },
    "risk_assessment": {
      "overall_risk_score": 35,
      "risk_level": "LOW",
      "confidence": 88,
      "factors": {
        "liquidity_risk": {
          "score": 15,
          "level": "VERY_LOW",
          "tvl": 3200000000,
          "daily_volume": 1100000000,
          "depth_2pct": 15000000,
          "assessment": "Excellent liquidity - minimal slippage risk"
        },
        "volatility_risk": {
          "score": 42,
          "level": "LOW",
          "volatility_30d": 18.2,
          "volatility_90d": 22.4,
          "vs_btc_correlation": 0.68,
          "beta": 1.15,
          "assessment": "Below DeFi sector average volatility"
        },
        "smart_contract_risk": {
          "score": 20,
          "level": "VERY_LOW",
          "audit_firms": ["Trail of Bits", "OpenZeppelin", "ABDK", "Consensys Diligence"],
          "last_audit": "2025-10-15",
          "time_in_market": "4+ years",
          "tvl_secured": "$3.2B",
          "known_exploits": 0,
          "bug_bounty": "$2M+ paid",
          "assessment": "Battle-tested protocol with comprehensive audits"
        },
        "market_correlation_risk": {
          "score": 48,
          "level": "LOW",
          "correlation_eth": 0.72,
          "correlation_btc": 0.68,
          "correlation_defi_index": 0.81,
          "diversification_benefit": "Limited - high DeFi correlation",
          "assessment": "Moves with broader DeFi market"
        }
      },
      "composite_score_breakdown": {
        "liquidity_weight": 0.30,
        "volatility_weight": 0.25,
        "smart_contract_weight": 0.30,
        "correlation_weight": 0.15,
        "weighted_score": 35
      },
      "recommendation": "Suitable for conservative to moderate portfolios. Low absolute risk, but correlated with DeFi sector."
    },
    "price_prediction": {
      "model": "LSTM",
      "model_version": "v2.3.1",
      "training_data": "3 years historical data",
      "forecast": {
        "24h": {
          "price": 8.75,
          "change_pct": 3.5,
          "confidence": 78,
          "confidence_interval_90pct": {
            "lower": 8.60,
            "upper": 8.90
          }
        },
        "7d": {
          "price": 9.20,
          "change_pct": 8.9,
          "confidence": 65,
          "confidence_interval_90pct": {
            "lower": 8.85,
            "upper": 9.55
          }
        },
        "30d": {
          "price": 9.80,
          "change_pct": 15.9,
          "confidence": 52,
          "confidence_interval_90pct": {
            "lower": 8.95,
            "upper": 10.65
          }
        }
      },
      "model_accuracy": {
        "historical_24h_accuracy": 67,
        "historical_7d_accuracy": 58,
        "historical_30d_accuracy": 42,
        "mean_absolute_error_24h": 2.8,
        "note": "Accuracy decreases with longer timeframes"
      },
      "prediction_drivers": [
        "Strong bullish sentiment (+72)",
        "Increasing whale accumulation",
        "Positive news cycle",
        "Technical breakout pattern",
        "DeFi sector momentum"
      ]
    },
    "trading_signals": {
      "signal": "BUY",
      "strength": "MODERATE",
      "confidence": 76,
      "reasoning": {
        "bullish_factors": [
          "Sentiment score 72/100 (bullish)",
          "Price prediction +3.5% 24h (positive)",
          "Risk score 35/100 (low risk)",
          "Whale accumulation (net +150K UNI)",
          "Technical: RSI 58 (neutral to bullish)"
        ],
        "bearish_factors": [
          "High correlation with ETH (0.72) - sector risk",
          "Funding rate trending negative (shorts increasing)"
        ],
        "neutral_factors": [
          "Volume flat vs 7d average"
        ]
      },
      "entry_strategy": {
        "recommended_entry": "8.40 - 8.50",
        "current_price": 8.45,
        "entry_timing": "IMMEDIATE to NEXT_DIP",
        "order_type": "Limit order at 8.42 (0.35% below current)"
      },
      "targets": {
        "target_1": {
          "price": 8.90,
          "timeframe": "24-48h",
          "probability": 78,
          "profit_potential": 5.3
        },
        "target_2": {
          "price": 9.20,
          "timeframe": "5-7d",
          "probability": 65,
          "profit_potential": 8.9
        }
      },
      "stop_loss": {
        "price": 8.10,
        "distance_pct": -4.1,
        "rationale": "Below key support at 8.15"
      },
      "risk_reward_ratio": 2.1,
      "position_sizing": {
        "conservative": "2-3% of portfolio",
        "moderate": "5-7% of portfolio",
        "aggressive": "10-15% of portfolio",
        "recommended": "5% of portfolio (moderate risk tolerance)"
      }
    },
    "whale_activity": {
      "timeframe": "24h",
      "large_transfers": [
        {
          "type": "transfer",
          "amount": 1200000,
          "amount_usd": 10140000,
          "from": "Binance",
          "to": "Unknown Wallet (0xabc...)",
          "timestamp": "2025-12-12T08:30:00Z",
          "interpretation": "Potential accumulation - moved from exchange to private wallet"
        },
        {
          "type": "transfer",
          "amount": 850000,
          "amount_usd": 7182500,
          "from": "Unknown Wallet (0xdef...)",
          "to": "Uniswap V3 Pool",
          "timestamp": "2025-12-12T12:15:00Z",
          "interpretation": "Added liquidity - bullish signal"
        }
      ],
      "net_exchange_flow": {
        "inflow": 2400000,
        "outflow": 3550000,
        "net": -1150000,
        "net_usd": -9717500,
        "interpretation": "NET OUTFLOW - Whales withdrawing from exchanges (bullish)"
      },
      "top_100_holders": {
        "change_24h": 150000,
        "change_pct": 0.42,
        "total_supply_pct": 68.5,
        "trend": "ACCUMULATION"
      },
      "smart_money_signal": "BULLISH",
      "whale_sentiment_score": 78
    },
    "technical_analysis": {
      "indicators": {
        "rsi_14": 58,
        "rsi_interpretation": "Neutral to bullish",
        "macd": {
          "value": 0.12,
          "signal": 0.08,
          "histogram": 0.04,
          "interpretation": "Bullish crossover"
        },
        "moving_averages": {
          "ma_50": 8.15,
          "ma_200": 7.85,
          "price_vs_ma50": "above",
          "price_vs_ma200": "above",
          "golden_cross": true,
          "interpretation": "Strong bullish structure"
        },
        "bollinger_bands": {
          "upper": 9.10,
          "middle": 8.45,
          "lower": 7.80,
          "price_position": "at_middle",
          "bandwidth": 15.4,
          "interpretation": "Normal volatility, room to move up"
        }
      },
      "support_resistance": {
        "resistance_1": 8.90,
        "resistance_2": 9.20,
        "resistance_3": 9.50,
        "support_1": 8.15,
        "support_2": 7.85,
        "support_3": 7.50
      },
      "chart_patterns": [
        {
          "pattern": "Ascending Triangle",
          "timeframe": "4h",
          "breakout_target": 9.30,
          "probability": 68,
          "status": "forming"
        }
      ]
    }
  },
  "summary": {
    "overall_rating": "BULLISH",
    "confidence": 76,
    "recommendation": "BUY on dips to 8.40-8.42",
    "target_price_24h": 8.90,
    "stop_loss": 8.10,
    "position_size": "5% of portfolio",
    "risk_reward": "2.1:1 (favorable)",
    "key_insight": "Strong bullish sentiment (72), low risk (35), positive whale activity. Entry at current levels offers good risk/reward for 24-48h trade."
  },
  "metadata": {
    "analysis_time_ms": 2840,
    "data_sources_used": 12,
    "ml_models_invoked": 4,
    "cache_hit_rate": 0.15
  }
}
```

**Key Features:**
- ✅ Multi-source sentiment (Twitter, Reddit, Discord, News)
- ✅ ML-based risk scoring (4 factors: liquidity, volatility, smart contract, correlation)
- ✅ LSTM price predictions (24h, 7d, 30d with confidence intervals)
- ✅ AI trading signals with entry/exit strategy
- ✅ Whale activity tracking (exchange flows, top holders)
- ✅ Technical analysis (RSI, MACD, Moving Averages, Bollinger Bands)
- ✅ Chart pattern recognition (Ascending Triangle)
- ✅ Risk/reward ratio calculation (2.1:1)
- ✅ Position sizing recommendations

---

## 💼 PORTFOLIO MANAGEMENT {#portfolio-management}

### Use Case 7: Multi-Chain Portfolio Tracking

**API Request:**

```bash
GET /api/v1/portfolio/me?include_positions=true&include_nfts=true&save_snapshot=true
Authorization: Bearer <jwt_token>
```

**API Response:**

```json
{
  "portfolio": {
    "user_id": "user_123",
    "wallets": [
      {
        "address": "0xabc123...",
        "type": "PRIVY",
        "label": "Main Wallet",
        "chains": ["ethereum", "base", "arbitrum"]
      },
      {
        "address": "0xdef456...",
        "type": "EXTERNAL",
        "label": "Hardware Wallet",
        "chains": ["ethereum"]
      }
    ],
    "total_value_usd": 285650,
    "total_value_change_24h": 4250,
    "total_value_change_24h_pct": 1.51,
    "last_updated": "2025-12-12T17:00:00Z",
    "breakdown_by_chain": {
      "ethereum": {
        "value_usd": 185000,
        "pct_of_total": 64.8,
        "assets_count": 12,
        "defi_positions_count": 4,
        "nfts_count": 3
      },
      "base": {
        "value_usd": 45000,
        "pct_of_total": 15.8,
        "assets_count": 5,
        "defi_positions_count": 2,
        "nfts_count": 0
      },
      "arbitrum": {
        "value_usd": 32000,
        "pct_of_total": 11.2,
        "assets_count": 6,
        "defi_positions_count": 3,
        "nfts_count": 0
      },
      "polygon": {
        "value_usd": 18650,
        "pct_of_total": 6.5,
        "assets_count": 8,
        "defi_positions_count": 1,
        "nfts_count": 5
      },
      "optimism": {
        "value_usd": 5000,
        "pct_of_total": 1.7,
        "assets_count": 3,
        "defi_positions_count": 1,
        "nfts_count": 0
      }
    },
    "holdings": [
      {
        "token": "ETH",
        "balance": 48.5,
        "value_usd": 186725,
        "pct_of_portfolio": 65.4,
        "chains": {
          "ethereum": 35.2,
          "base": 8.3,
          "arbitrum": 5.0
        },
        "avg_cost_basis": 2850,
        "unrealized_pnl": 48262.50,
        "unrealized_pnl_pct": 34.9,
        "24h_change": 2.1
      },
      {
        "token": "USDC",
        "balance": 45000,
        "value_usd": 45000,
        "pct_of_portfolio": 15.8,
        "chains": {
          "ethereum": 25000,
          "base": 15000,
          "arbitrum": 5000
        },
        "avg_cost_basis": 1.00,
        "unrealized_pnl": 0,
        "unrealized_pnl_pct": 0,
        "24h_change": 0.01
      },
      {
        "token": "UNI",
        "balance": 2400,
        "value_usd": 20280,
        "pct_of_portfolio": 7.1,
        "chains": {
          "ethereum": 2400
        },
        "avg_cost_basis": 7.85,
        "unrealized_pnl": 1440,
        "unrealized_pnl_pct": 7.6,
        "24h_change": 3.2
      }
    ],
    "defi_positions": [
      {
        "protocol": "Morpho",
        "type": "LENDING",
        "vault": "Steakhouse USDC",
        "chain": "ethereum",
        "deposited_amount": 25000,
        "deposited_asset": "USDC",
        "current_value_usd": 25420,
        "earnings_usd": 420,
        "earnings_pct": 1.68,
        "current_apy": 8.4,
        "deposited_at": "2025-11-15T10:30:00Z",
        "days_active": 27,
        "risk_score": 28
      },
      {
        "protocol": "Curve Finance",
        "type": "LP",
        "pool": "stETH/ETH",
        "chain": "ethereum",
        "liquidity_provided": {
          "stETH": 12.5,
          "ETH": 12.5
        },
        "current_value_usd": 96500,
        "earnings_usd": 2840,
        "earnings_pct": 3.03,
        "current_apy": 6.8,
        "impermanent_loss": -145,
        "deposited_at": "2025-09-20T14:00:00Z",
        "days_active": 83,
        "risk_score": 45
      },
      {
        "protocol": "Aave V3",
        "type": "LENDING",
        "market": "USDC",
        "chain": "base",
        "deposited_amount": 15000,
        "deposited_asset": "USDC",
        "current_value_usd": 15320,
        "earnings_usd": 320,
        "earnings_pct": 2.13,
        "current_apy": 7.8,
        "deposited_at": "2025-10-01T09:15:00Z",
        "days_active": 72,
        "risk_score": 22
      },
      {
        "protocol": "Hyperliquid",
        "type": "PERPETUAL",
        "market": "ETH-PERP",
        "chain": "arbitrum",
        "position_size_usd": 45000,
        "entry_price": 3850,
        "current_price": 3850,
        "leverage": 3,
        "margin": 15000,
        "pnl_usd": 0,
        "pnl_pct": 0,
        "liquidation_price": 2567,
        "opened_at": "2025-12-12T14:22:00Z",
        "risk_score": 55
      }
    ],
    "nfts": [
      {
        "collection": "CryptoPunks",
        "token_id": 1234,
        "chain": "ethereum",
        "floor_price_eth": 35.0,
        "floor_price_usd": 134750,
        "last_sale_price_eth": 38.5,
        "rarity_rank": 245,
        "acquired_price_eth": 32.0,
        "unrealized_gain_eth": 3.0,
        "unrealized_gain_pct": 9.38,
        "held_since": "2025-06-10"
      }
    ],
    "performance_metrics": {
      "total_invested_usd": 245000,
      "current_value_usd": 285650,
      "total_pnl_usd": 40650,
      "total_pnl_pct": 16.59,
      "realized_gains_ytd": 8450,
      "unrealized_gains": 32200,
      "best_performer": {
        "asset": "ETH",
        "pnl_pct": 34.9
      },
      "worst_performer": {
        "asset": "Curve stETH/ETH LP",
        "pnl_pct": -0.15
      },
      "avg_defi_apy": 7.75,
      "total_defi_earnings_ytd": 5840
    },
    "risk_metrics": {
      "portfolio_risk_score": 42,
      "risk_level": "MEDIUM",
      "concentration_risk": "HIGH (65.4% in ETH)",
      "smart_contract_risk": "MEDIUM (avg: 37.5)",
      "chain_diversification": "GOOD (5 chains)",
      "protocol_diversification": "LIMITED (4 protocols)"
    }
  },
  "snapshot_saved": true,
  "snapshot_id": "snap_20251212_170000",
  "metadata": {
    "fetch_time_ms": 3420,
    "chains_queried": 5,
    "api_calls_made": 18,
    "cache_hits": 6
  }
}
```

**Key Features:**
- ✅ Multi-chain tracking (5 EVM chains)
- ✅ Unified portfolio view across wallets
- ✅ DeFi positions tracking (Morpho, Curve, Aave, Hyperliquid)
- ✅ NFT portfolio with floor prices
- ✅ Performance metrics (total PnL: +16.59%)
- ✅ Risk scoring (portfolio risk: 42/100)
- ✅ Earnings tracking per position
- ✅ Snapshot functionality for historical comparison

---

### Use Case 8: Portfolio Risk Analysis with Cascade Simulation

**API Request:**

```bash
POST /api/v1/portfolio/risk/simulate-cascade
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "scenario": "curve_exploit",
  "severity": "critical",
  "affected_protocols": ["curve"],
  "assumptions": {
    "price_impact_pct": -80,
    "contagion_factor": 0.35,
    "recovery_time_days": 30
  }
}
```

**API Response:**

```json
{
  "simulation": {
    "scenario_name": "Curve Finance Critical Exploit",
    "timestamp": "2025-12-12T17:30:00Z",
    "severity": "CRITICAL",
    "assumptions": {
      "initial_impact": "Curve Finance exploited - $800M drained",
      "price_impact_crv": -80,
      "contagion_to_defi": 0.35,
      "stablecoin_depeg_risk": "HIGH",
      "market_panic_factor": 0.65
    },
    "direct_impact": {
      "affected_positions": [
        {
          "protocol": "Curve Finance",
          "pool": "stETH/ETH",
          "current_value": 96500,
          "simulated_value": 19300,
          "loss_usd": -77200,
          "loss_pct": -80,
          "recovery_probability": 0.15,
          "explanation": "Direct exposure - assumed total loss of LP position"
        }
      ],
      "total_direct_loss": -77200,
      "pct_of_portfolio": -27.0
    },
    "indirect_impact": {
      "market_contagion": {
        "eth_price_impact": -25,
        "defi_sector_impact": -35,
        "stablecoin_depeg": {
          "USDC": -2.5,
          "USDT": -4.0,
          "DAI": -8.5
        }
      },
      "affected_positions": [
        {
          "asset": "ETH",
          "current_value": 186725,
          "simulated_value": 140044,
          "loss_usd": -46681,
          "loss_pct": -25,
          "explanation": "Contagion effect - broad DeFi selloff"
        },
        {
          "protocol": "Morpho",
          "vault": "Steakhouse USDC",
          "current_value": 25420,
          "simulated_value": 23263,
          "loss_usd": -2157,
          "loss_pct": -8.5,
          "explanation": "Morpho uses Curve pools - DAI depeg risk"
        },
        {
          "protocol": "Aave V3",
          "market": "USDC",
          "current_value": 15320,
          "simulated_value": 14937,
          "loss_usd": -383,
          "loss_pct": -2.5,
          "explanation": "Minor USDC depeg risk"
        }
      ],
      "total_indirect_loss": -49221,
      "pct_of_portfolio": -17.2
    },
    "cascade_analysis": {
      "total_loss": -126421,
      "total_loss_pct": -44.2,
      "portfolio_value_before": 285650,
      "portfolio_value_after": 159229,
      "time_to_recover_50pct": "45-60 days",
      "time_to_full_recovery": "180-240 days (if recoverable)",
      "probability_full_recovery": 0.25
    },
    "dependency_chain": [
      "1. Curve Finance exploited → CRV price crashes -80%",
      "2. Panic selling → ETH drops -25%, DeFi sector -35%",
      "3. 3pool liquidity crisis → DAI depegs -8.5%",
      "4. Morpho (uses Curve) → vault value drops -8.5%",
      "5. General risk-off → Aave USDC slight depeg -2.5%",
      "6. Portfolio value: $285K → $159K (-44.2%)"
    ],
    "mitigation_recommendations": [
      {
        "priority": "CRITICAL",
        "action": "REDUCE Curve exposure from 33.8% to <15%",
        "rationale": "Single protocol represents 27% direct loss risk",
        "target_allocation": "Max 15% in any single DeFi protocol",
        "implementation": "Withdraw $50K from Curve stETH/ETH, migrate to Aave/Morpho"
      },
      {
        "priority": "HIGH",
        "action": "INCREASE stablecoin diversification",
        "rationale": "Currently 15.8% USDC only - add USDT, USDC.e for depeg protection",
        "target_allocation": "Split stablecoins: 40% USDC, 30% USDT, 30% USDC.e",
        "implementation": "Swap $15K USDC → $6K USDT + $4.5K USDC.e"
      },
      {
        "priority": "HIGH",
        "action": "ADD protocol-agnostic hedge (ETH/BTC)",
        "rationale": "65.4% ETH exposure amplifies DeFi contagion risk",
        "target_allocation": "Reduce ETH to 50%, add 10% BTC, 5% blue-chip alts",
        "implementation": "Swap 10 ETH → 5 BTC + diversified alts"
      },
      {
        "priority": "MEDIUM",
        "action": "SET UP real-time monitoring for Curve TVL/exploits",
        "rationale": "Early detection enables faster exit before full cascade",
        "implementation": "Enable 'TVL -20% in 1h' alert + 'unusual contract activity' alert"
      },
      {
        "priority": "LOW",
        "action": "DIVERSIFY across L2s (currently 70% mainnet)",
        "rationale": "Mainnet congestion during crisis → failed emergency exits",
        "target_allocation": "40% mainnet, 60% L2s (Base, Arbitrum, Optimism)",
        "implementation": "Bridge $50K to Base/Arbitrum"
      }
    ],
    "optimized_portfolio": {
      "if_recommendations_applied": {
        "curve_exposure": "14.5% (from 33.8%)",
        "eth_exposure": "50.0% (from 65.4%)",
        "stablecoin_diversification": "3 stablecoins (from 1)",
        "protocol_count": "6 (from 4)",
        "chain_distribution": "60% L2 (from 30%)",
        "simulated_loss_same_scenario": -85420,
        "simulated_loss_pct": -29.9,
        "improvement_vs_current": "+14.3% less loss"
      }
    }
  },
  "historical_precedents": {
    "similar_events": [
      {
        "event": "Curve reentrancy exploit (July 2023)",
        "actual_impact": "$70M drained",
        "crv_price_drop": -42,
        "recovery_time": "90 days",
        "final_recovery": "Partial (65% recovered)"
      },
      {
        "event": "Iron Finance collapse (June 2021)",
        "actual_impact": "$2B TVL collapse",
        "titan_price_drop": -100,
        "contagion_to_defi": -28,
        "recovery_time": "Never (total loss)"
      }
    ]
  },
  "metadata": {
    "simulation_time_ms": 1850,
    "monte_carlo_iterations": 10000,
    "confidence_level": 0.90
  }
}
```

**Key Features:**
- ✅ Cascade simulation modeling
- ✅ Direct + indirect impact calculation
- ✅ Dependency chain analysis (6-step cascade)
- ✅ Contagion factor modeling (35% to DeFi sector)
- ✅ Depeg risk assessment (stablecoins)
- ✅ Mitigation recommendations (5 priorities)
- ✅ Optimized portfolio projection (-14.3% improvement)
- ✅ Historical precedent analysis
- ✅ Monte Carlo simulation (10K iterations, 90% confidence)

---

## 🌉 CROSS-CHAIN OPERATIONS {#cross-chain-operations}

### Use Case 9: Cross-Chain Bridge with Axelar

**API Request:**

```bash
POST /api/v1/defi/axelar/estimate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "from_chain": "ethereum",
  "to_chain": "arbitrum",
  "asset": "USDC",
  "amount": 10000,
  "speed": "express"
}
```

**API Response:**

```json
{
  "route": {
    "from_chain": "ethereum",
    "to_chain": "arbitrum",
    "asset": "USDC",
    "amount": 10000,
    "routes_available": 2
  },
  "estimates": {
    "standard": {
      "total_time_minutes": 45,
      "gas_cost_usd": 12.50,
      "bridge_fee_usd": 3.00,
      "slippage_estimate_pct": 0.05,
      "total_cost_usd": 15.50,
      "amount_received": 9984.50,
      "effective_rate": 0.9985,
      "steps": [
        "1. Lock USDC on Ethereum (confirm: 2 min)",
        "2. Axelar validators sign (wait: 35 min)",
        "3. Release USDC on Arbitrum (confirm: 8 min)"
      ]
    },
    "express": {
      "total_time_minutes": 3,
      "gas_cost_usd": 18.75,
      "bridge_fee_usd": 8.00,
      "express_fee_usd": 15.00,
      "slippage_estimate_pct": 0.05,
      "total_cost_usd": 41.75,
      "amount_received": 9958.25,
      "effective_rate": 0.9958,
      "steps": [
        "1. Lock USDC on Ethereum (confirm: 1 min)",
        "2. Express relayer fronts liquidity (instant)",
        "3. Receive USDC on Arbitrum (confirm: 2 min)"
      ],
      "how_express_works": "Express relayers front liquidity instantly, then get reimbursed by Axelar validators asynchronously"
    }
  },
  "recommendation": {
    "suggested_speed": "express",
    "rationale": "Time savings (42 min) worth the extra $26.25 for $10K transfer",
    "cost_benefit": "Save 42 minutes for 0.26% of transfer amount"
  },
  "risk_assessment": {
    "bridge_security": "HIGH (Axelar is Proof-of-Stake with 75 validators)",
    "exploit_history": "None",
    "tvl_bridged": "$1.2B",
    "audit_firms": ["Oak Security", "Ackee Blockchain", "Code4rena"],
    "last_audit": "2025-08-20"
  }
}
```

**Execute Bridge:**

```bash
POST /api/v1/defi/axelar/bridge
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "from_chain": "ethereum",
  "to_chain": "arbitrum",
  "asset": "USDC",
  "amount": 10000,
  "speed": "express",
  "recipient_address": "0xabc123...",
  "slippage_tolerance": 0.5
}
```

**Track Transfer:**

```bash
GET /api/v1/defi/axelar/transfer/0xtx_hash_123
Authorization: Bearer <jwt_token>
```

**Response:**

```json
{
  "transfer": {
    "tx_hash": "0xtx_hash_123",
    "status": "completed",
    "from_chain": "ethereum",
    "to_chain": "arbitrum",
    "asset": "USDC",
    "amount_sent": 10000,
    "amount_received": 9958.25,
    "speed": "express",
    "timeline": [
      {
        "step": "Initiated on Ethereum",
        "status": "confirmed",
        "tx_hash": "0xeth_tx...",
        "timestamp": "2025-12-12T18:00:00Z",
        "time_elapsed": "0s"
      },
      {
        "step": "Express relayer fronted liquidity",
        "status": "confirmed",
        "timestamp": "2025-12-12T18:00:15Z",
        "time_elapsed": "15s"
      },
      {
        "step": "Received on Arbitrum",
        "status": "confirmed",
        "tx_hash": "0xarb_tx...",
        "timestamp": "2025-12-12T18:03:00Z",
        "time_elapsed": "3m 0s"
      }
    ],
    "total_time": "3m 0s",
    "total_cost": 41.75,
    "effective_slippage": 0.42
  }
}
```

**Key Features:**
- ✅ Multi-speed options (standard 45min vs express 3min)
- ✅ Cost breakdown (gas + bridge + express fees)
- ✅ Real-time transfer tracking
- ✅ Risk assessment (audit status, TVL, exploit history)
- ✅ Slippage estimation
- ✅ Effective rate calculation

---

### Use Case 10: Cross-Chain Messaging with LayerZero

**API Request:**

```bash
POST /api/v1/defi/layerzero/fees/estimate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "from_chain": "ethereum",
  "to_chain": "avalanche",
  "message_type": "oft_transfer",
  "payload_size_bytes": 256
}
```

**API Response:**

```json
{
  "fee_estimate": {
    "native_fee_wei": "1250000000000000",
    "native_fee_eth": 0.00125,
    "native_fee_usd": 4.81,
    "zro_fee": 0,
    "breakdown": {
      "oracle_fee": 1.20,
      "relayer_fee": 3.61,
      "protocol_fee": 0
    },
    "destination_gas_amount": 200000,
    "message_size_bytes": 256
  }
}
```

**Send Cross-Chain Message:**

```bash
POST /api/v1/defi/layerzero/send-message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "from_chain": "ethereum",
  "to_chain": "avalanche",
  "oft_address": "0xOFT_contract...",
  "amount": 5000,
  "recipient": "0xrecipient...",
  "adapter_params": "0x..."
}
```

**Track Message:**

```bash
GET /api/v1/defi/layerzero/message/0xmsg_hash_456
Authorization: Bearer <jwt_token>
```

**Key Features:**
- ✅ Cross-chain messaging (OFT transfers, generic messages)
- ✅ Fee estimation (oracle + relayer + protocol fees)
- ✅ Multi-chain support (30+ chains: EVM + non-EVM)
- ✅ Message tracking and status
- ✅ Adapter params customization

---

## 🎨 PROJECTS (CUSTOMIZABLE AI CONTAINERS) {#projects}

Projects are **multi-tenant customizable AI containers** that allow users to configure:
- System prompts
- Enabled protocols
- Enabled chains
- Enabled tools/MCPs
- Risk tolerance
- Visibility (public/private)

### Use Case 11: Creating and Using a Custom Project

**Create Project (Admin):**

```bash
POST /api/v1/admin/projects
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Conservative DeFi Yield",
  "slug": "conservative-defi-yield",
  "description": "Focus on low-risk, audited protocols for stable yield generation",
  "system_prompt": "You are a conservative DeFi yield optimizer. Only recommend protocols with:\n- Full audits from 3+ reputable firms\n- TVL > $100M\n- No exploits in past 2 years\n- Risk score < 35\n\nPrioritize Aave, Morpho, and blue-chip Curve pools. Avoid leverage and experimental protocols.",
  "enabled_protocols": ["aave", "morpho", "curve"],
  "enabled_chains": ["ethereum", "base", "arbitrum"],
  "enabled_tools": [
    "portfolio_tracker",
    "risk_analyzer",
    "yield_optimizer",
    "defillama_mcp",
    "aave_mcp",
    "morpho_mcp",
    "curve_mcp"
  ],
  "risk_tolerance": "conservative",
  "max_risk_score": 35,
  "status": "active",
  "visibility": "public"
}
```

**User Selects Project:**

```bash
POST /api/v1/user/projects/conservative-defi-yield/select
Authorization: Bearer <user_token>
```

**Chat with Project-Specific Context:**

```bash
POST /api/v1/chat/conversations
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "message": "Find me the best USDC yield opportunities",
  "project_id": "conservative-defi-yield"
}
```

**Response (Filtered by Project Config):**

```json
{
  "response": {
    "message": "Based on your conservative risk profile, here are the top audited USDC yield opportunities:\n\n1. **Morpho Steakhouse USDC** (Recommended)\n   - APY: 8.4%\n   - Risk Score: 28 ✅ (below your max 35)\n   - Audits: 4 firms ✅ (OpenZeppelin, Trail of Bits, ChainSecurity, Zellic)\n   - TVL: $450M ✅ (above $100M threshold)\n   - No exploits ✅\n   - Chain: Ethereum ✅ (enabled)\n   \n2. **Aave V3 USDC (Ethereum)**\n   - APY: 5.8%\n   - Risk Score: 22 ✅ (ultra-low risk)\n   - Audits: 6 firms ✅\n   - TVL: $1.2B ✅\n   - No exploits ✅\n   - Chain: Ethereum ✅\n   \n3. **Curve 3pool**\n   - APY: 6.5%\n   - Risk Score: 35 ✅ (at your threshold)\n   - Audits: 3 firms ✅\n   - TVL: $800M ✅\n   - No exploits ✅\n   - Chain: Ethereum ✅\n   \n**Excluded Options:**\n- Compound V3 (not in enabled protocols)\n- Hyperliquid lending (too high risk: 48)\n- Unaudited new protocols\n- Leverage farming opportunities (outside risk tolerance)",
    "project_context": {
      "project_name": "Conservative DeFi Yield",
      "risk_tolerance": "conservative",
      "max_risk_score": 35,
      "enabled_protocols_used": ["morpho", "aave", "curve"],
      "protocols_filtered_out": 8,
      "recommendations_filtered_by_risk": 5
    },
    "agents_used": ["defi_yield"],
    "mcp_servers_used": ["morpho", "aave", "curve", "defillama"]
  }
}
```

**Key Features:**
- ✅ Multi-tenant projects (public/private)
- ✅ Custom system prompts per project
- ✅ Protocol whitelisting (only enabled protocols shown)
- ✅ Chain filtering (only enabled chains queried)
- ✅ Tool/MCP restrictions (limit available capabilities)
- ✅ Risk guardrails (max_risk_score enforcement)
- ✅ Project-specific agent behavior

**Other Project Examples:**

1. **"Aggressive DeFi Degen"**
   - Enable: All protocols including leverage, flash loans, MEV
   - Max risk score: 80
   - Focus: Maximum APY, arbitrage opportunities

2. **"NFT Portfolio Manager"**
   - Enable: OpenSea, Blur, LooksRare MCPs
   - Tools: NFT valuation, rarity analysis, floor tracking
   - Focus: NFT-specific portfolio management

3. **"Tax-Optimized Trading"**
   - Enable: Tax optimizer agent, 1inch MCP
   - Tools: Tax-loss harvesting, cost basis tracking
   - Focus: Minimize tax liability while trading

4. **"Compliance-First Institution"**
   - Enable: Compliance monitor, AML/KYC checks
   - Protocols: Only fully regulated (Aave, Compound)
   - Focus: Regulatory compliance, audit trails

---

## 🔍 GRAPHRAG PROTOCOL SEARCH {#graphrag}

GraphRAG provides **graph-based protocol relationship search** (not traditional vector search).

### Use Case 12: Protocol Discovery via GraphRAG

**API Request:**

```bash
POST /api/v1/chat/search-protocols
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "query": "Find lending protocols similar to Aave but with higher yields and lower risk",
  "limit": 5,
  "context": {
    "current_position": "Aave V3 USDC",
    "current_apy": 5.8,
    "current_risk": 22
  }
}
```

**GraphRAG Processing:**

```
Step 1: Entity Extraction (NER)
  Entities: ["Aave", "USDC", "lending"]

Step 2: Graph Traversal
  Start Node: Aave
  Relationships:
    - COMPETES_WITH → [Compound, Morpho, Spark]
    - INTEGRATES_WITH → [Curve, Balancer]
    - FORKS_FROM → [Compound]
    - FORKED_BY → [Spark, Radiant]

  Max Hops: 2
  Subgraph Size: 15 protocols

Step 3: Semantic Ranking
  Query embedding: "higher yields + lower risk"
  Score each protocol in subgraph

Step 4: Filter & Rank
  Filters applied:
    - APY > 5.8% (higher yield)
    - Risk Score < 22 (lower/equal risk)
    - Protocol Type = "lending"

  Top 5 Results
```

**API Response:**

```json
{
  "results": [
    {
      "protocol": "Morpho",
      "relevance_score": 0.94,
      "apy": 8.4,
      "risk_score": 28,
      "relationship_to_aave": "COMPETES_WITH",
      "why_recommended": "Higher APY (+2.6%) with only slightly higher risk (+6 points). Uses Aave pools underneath with optimization layer.",
      "graph_context": {
        "node_type": "lending_protocol",
        "connections": [
          {"protocol": "Aave", "relationship": "COMPETES_WITH"},
          {"protocol": "Aave", "relationship": "BUILDS_ON"},
          {"protocol": "Compound", "relationship": "COMPETES_WITH"}
        ],
        "market_position": "Emerging (2023)",
        "tvl_rank": 15
      },
      "key_differences": [
        "Peer-to-peer matching reduces spread",
        "More capital efficient than Aave",
        "Vault-based architecture (not pool-based)"
      ]
    },
    {
      "protocol": "Spark Protocol",
      "relevance_score": 0.87,
      "apy": 7.2,
      "risk_score": 24,
      "relationship_to_aave": "FORKS_FROM",
      "why_recommended": "Aave V3 fork by MakerDAO. Higher APY (+1.4%) with minimal additional risk (+2 points).",
      "graph_context": {
        "node_type": "lending_protocol",
        "connections": [
          {"protocol": "Aave", "relationship": "FORKS_FROM"},
          {"protocol": "MakerDAO", "relationship": "OWNED_BY"}
        ],
        "market_position": "Backed by MakerDAO",
        "tvl_rank": 22
      },
      "key_differences": [
        "Integrates with DAI Savings Rate",
        "Lower fees than Aave",
        "MakerDAO governance backing"
      ]
    },
    {
      "protocol": "Compound V3",
      "relevance_score": 0.82,
      "apy": 6.9,
      "risk_score": 20,
      "relationship_to_aave": "COMPETES_WITH",
      "why_recommended": "Lower risk (-2 points) with moderate APY increase (+1.1%). Battle-tested protocol.",
      "graph_context": {
        "node_type": "lending_protocol",
        "connections": [
          {"protocol": "Aave", "relationship": "COMPETES_WITH"},
          {"protocol": "Morpho", "relationship": "INTEGRATES_WITH"}
        ],
        "market_position": "Established (2018)",
        "tvl_rank": 8
      },
      "key_differences": [
        "Single-collateral markets (simpler)",
        "Lower liquidation risk",
        "Longer track record"
      ]
    }
  ],
  "query_analysis": {
    "interpreted_intent": "Find Aave competitors with yield > 5.8% and risk <= 22",
    "entities_extracted": ["Aave", "lending", "higher yields", "lower risk"],
    "graph_traversal_stats": {
      "nodes_visited": 15,
      "relationships_traversed": 42,
      "max_hops": 2,
      "traversal_time_ms": 85
    },
    "filters_applied": {
      "protocol_type": "lending",
      "min_apy": 5.8,
      "max_risk_score": 22,
      "results_before_filter": 15,
      "results_after_filter": 3
    }
  },
  "graph_visualization": {
    "mermaid": "graph TD\n  A[Aave] -->|COMPETES_WITH| M[Morpho]\n  A -->|COMPETES_WITH| C[Compound]\n  A -->|FORKED_BY| S[Spark]\n  M -->|BUILDS_ON| A\n  S -->|OWNED_BY| MKR[MakerDAO]"
  },
  "metadata": {
    "total_time_ms": 420,
    "graph_query_time_ms": 85,
    "semantic_ranking_time_ms": 280,
    "filter_time_ms": 55
  }
}
```

**Key Features:**
- ✅ Graph-based search (not vector search)
- ✅ Relationship-aware results (COMPETES_WITH, FORKS_FROM, BUILDS_ON)
- ✅ Semantic ranking (relevance scoring)
- ✅ Context-aware filtering (yield + risk constraints)
- ✅ Graph visualization (Mermaid diagram)
- ✅ Explainable results (why each protocol recommended)

---

## ⚡ REAL-TIME FEATURES {#real-time-features}

### Use Case 13: WebSocket Real-Time Chat

**WebSocket Connection:**

```javascript
const ws = new WebSocket(
  'wss://api.anvil.com/api/v1/chat/ws/conv_123?token=<jwt_token>'
);

ws.onopen = () => {
  console.log('Connected to Anvil Chat');

  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    message: 'What's the current ETH price and sentiment?'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'message_chunk') {
    // Streaming response chunk
    console.log('Chunk:', data.content);
    appendToChat(data.content);
  } else if (data.type === 'message_complete') {
    // Full message completed
    console.log('Complete message:', data.full_message);
  } else if (data.type === 'error') {
    console.error('Error:', data.error);
  }
};

// Heartbeat (ping/pong)
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);

ws.onclose = () => {
  console.log('Disconnected from Anvil Chat');
};
```

**Server Response (Streaming):**

```json
// Chunk 1
{"type": "message_chunk", "chunk_id": 1, "content": "Current ETH"}

// Chunk 2
{"type": "message_chunk", "chunk_id": 2, "content": " price is $"}

// Chunk 3
{"type": "message_chunk", "chunk_id": 3, "content": "3,850 (+"}

// Chunk 4
{"type": "message_chunk", "chunk_id": 4, "content": "2.1% 24h).\n\n"}

// Chunk 5
{"type": "message_chunk", "chunk_id": 5, "content": "Sentiment Analysis:\n"}

// Chunk 6
{"type": "message_chunk", "chunk_id": 6, "content": "- Overall: 68/100 ("}

// Chunk 7
{"type": "message_chunk", "chunk_id": 7, "content": "Bullish)\n- Twitter"}

// ... (streaming continues)

// Final message
{
  "type": "message_complete",
  "message_id": "msg_789",
  "full_message": "Current ETH price is $3,850 (+2.1% 24h).\n\nSentiment Analysis:\n- Overall: 68/100 (Bullish)\n- Twitter: 70/100 (9,200 mentions)\n- Confidence: 82%",
  "metadata": {
    "agents_used": ["chat", "hunter_ai"],
    "total_time_ms": 1850,
    "tokens_generated": 142
  }
}
```

**Key Features:**
- ✅ Real-time WebSocket streaming
- ✅ Token-by-token response (low latency UX)
- ✅ Heartbeat support (ping/pong)
- ✅ JWT authentication via query param
- ✅ Error handling
- ✅ Message metadata

---

### Use Case 14: Real-Time Risk Alerts

**Setup Alert:**

```bash
PUT /api/v1/alerts/subscription
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "enabled": true,
  "channels": ["email", "push", "websocket"],
  "alert_types": [
    {
      "type": "risk_threshold",
      "severity": "HIGH",
      "conditions": {
        "portfolio_risk_score_above": 70,
        "single_protocol_exposure_above": 0.40,
        "tvl_drop_24h_pct": 20
      }
    },
    {
      "type": "smart_contract_risk",
      "severity": "CRITICAL",
      "conditions": {
        "exploit_detected": true,
        "unusual_contract_activity": true
      }
    }
  ],
  "protocols_monitored": ["curve", "aave", "morpho"],
  "notification_preferences": {
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00",
      "timezone": "America/New_York"
    },
    "digest_mode": false
  }
}
```

**Real-Time Alert (WebSocket):**

```json
{
  "type": "alert",
  "alert_id": "alert_critical_001",
  "timestamp": "2025-12-12T19:45:00Z",
  "severity": "CRITICAL",
  "alert_type": "smart_contract_risk",
  "protocol": "Curve Finance",
  "title": "⚠️ CRITICAL: Unusual Contract Activity Detected - Curve Finance",
  "message": "Curve Finance stETH/ETH pool showing unusual contract interactions. This may indicate an ongoing exploit attempt.",
  "details": {
    "protocol": "Curve Finance",
    "pool": "stETH/ETH",
    "chain": "ethereum",
    "anomaly_detected": "Unusual withdraw pattern (15 large withdrawals in 10 minutes)",
    "tvl_change_10min": -12.5,
    "current_tvl": 700000000,
    "your_exposure_usd": 96500,
    "pct_of_portfolio": 33.8,
    "risk_level": "CRITICAL"
  },
  "recommended_actions": [
    {
      "priority": "IMMEDIATE",
      "action": "Withdraw funds from Curve stETH/ETH pool",
      "command": "/agent execute emergency-withdraw curve stETH/ETH",
      "estimated_time": "2-5 minutes",
      "estimated_gas": "$85 (high priority gas)"
    },
    {
      "priority": "IMMEDIATE",
      "action": "Monitor Curve Security Twitter for official announcements",
      "link": "https://twitter.com/CurveFinance"
    },
    {
      "priority": "HIGH",
      "action": "Move to safer protocols (Aave, Morpho)",
      "rationale": "Reduce smart contract risk exposure"
    }
  ],
  "historical_context": {
    "similar_alerts": 2,
    "false_positive_rate": 0.15,
    "avg_time_to_exploit_after_alert": "18 minutes",
    "note": "Past alerts have been 85% accurate. Act quickly."
  },
  "acknowledgement_required": true,
  "acknowledgement_deadline": "2025-12-12T19:50:00Z",
  "auto_action": {
    "enabled": false,
    "action": "emergency_withdraw_if_tvl_drops_30pct",
    "note": "Enable auto-actions in settings for faster response"
  }
}
```

**Acknowledge Alert:**

```bash
PUT /api/v1/alerts/risk/alert_critical_001/acknowledge
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "acknowledged": true,
  "action_taken": "Initiated emergency withdrawal",
  "notes": "Withdrew all Curve stETH/ETH LP tokens"
}
```

**Key Features:**
- ✅ Real-time WebSocket alerts
- ✅ Multi-channel delivery (email, push, WebSocket)
- ✅ Customizable severity thresholds
- ✅ Quiet hours support
- ✅ Actionable recommendations with commands
- ✅ Historical context (false positive rate, past accuracy)
- ✅ Acknowledgement tracking
- ✅ Auto-action capabilities (optional)

---

## 🏢 ENTERPRISE FEATURES {#enterprise-features}

### Feature Summary

1. **Multi-Tenant Projects** - Isolated AI environments per client
2. **Role-Based Access Control** - Admin, user, auditor roles
3. **Compliance Monitoring** - SEC, FinCEN, IRS compliance checks
4. **Audit Trail** - Complete transaction and action logging
5. **White-Label Support** - Custom branding per project
6. **SLA Guarantees** - 99.9% uptime, priority support
7. **Dedicated Infrastructure** - Isolated compute for enterprise clients
8. **Custom MCP Servers** - Build proprietary protocol integrations
9. **Advanced Analytics** - Custom dashboards, BI integrations
10. **Security Features** - HPKE encryption, 2FA, hardware wallet support

---

## 📚 API REFERENCE EXAMPLES {#api-examples}

### Authentication

**Login:**
```bash
POST /api/v1/account/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**All Authenticated Requests:**
```bash
Authorization: Bearer <access_token>
```

---

### Complete API Endpoint List

**Account & Auth** (`/api/v1/account/`, `/api/v1/auth/`)
- `POST /account/signup` - Register
- `POST /account/login` - Login
- `POST /account/privy-login` - Web3 login
- `POST /account/logout` - Logout
- `GET /account/me` - Profile
- `POST /account/refresh-token` - Refresh JWT

**User & Projects** (`/api/v1/user/`)
- `GET /user/projects` - List projects
- `POST /user/projects/{id}/select` - Activate project

**Wallet** (`/api/v1/wallet/`)
- `GET /wallet/me` - Get wallets
- `POST /wallet/sync` - Sync wallets
- `POST /wallet/export` - Export private key

**Portfolio** (`/api/v1/portfolio/`)
- `GET /portfolio/me` - My portfolio
- `GET /portfolio/{address}` - Public portfolio
- `GET /portfolio/risk` - Risk analysis
- `POST /portfolio/risk/simulate-cascade` - Cascade simulation

**Chat** (`/api/v1/chat/`)
- `POST /chat/conversations` - New conversation
- `GET /chat/conversations` - List conversations
- `POST /chat/conversations/{id}/messages` - Send message
- `POST /chat/agent-squad/messages` - Agent Squad routing
- `POST /chat/agent-squad/supervisor` - Multi-agent orchestration
- `WS /chat/ws/{id}` - WebSocket streaming

**Hunter AI** (`/api/v1/hunter/`)
- `GET /hunter/sentiment/analyze/{symbol}` - Sentiment
- `GET /hunter/risk/analyze/{symbol}` - Risk score
- `GET /hunter/price-prediction/{symbol}` - Price forecast
- `GET /hunter/trading-signals` - Trading signals

**DeFi - Morpho** (`/api/v1/defi/morpho/`)
- `GET /morpho/vaults` - List vaults
- `GET /morpho/markets` - List markets
- `GET /morpho/positions/{address}` - User positions
- `GET /morpho/compare` - Compare yields

**DeFi - Curve** (`/api/v1/defi/curve/`)
- `GET /curve/pools` - List pools
- `GET /curve/pools/{address}` - Pool details
- `POST /curve/quote` - Swap quote

**DeFi - Hyperliquid** (`/api/v1/defi/hyperliquid/`)
- `GET /hyperliquid/markets` - Perpetual markets
- `GET /hyperliquid/positions/{address}` - Open positions
- `POST /hyperliquid/risk/calculate` - Position risk

**DeFi - Axelar** (`/api/v1/defi/axelar/`)
- `GET /axelar/routes` - Bridge routes
- `POST /axelar/estimate` - Bridge estimate
- `POST /axelar/bridge` - Execute bridge
- `GET /axelar/transfer/{tx_hash}` - Track transfer

**DeFi - LayerZero** (`/api/v1/defi/layerzero/`)
- `GET /layerzero/message/{tx_hash}` - Track message
- `POST /layerzero/fees/estimate` - Fee estimate

**DeFi - Aave** (`/api/v1/defi/aave/`)
- Lending/borrowing operations

**NFT - OpenSea** (`/api/v1/nft/opensea/`)
- `GET /opensea/portfolio/{address}` - NFT portfolio
- `GET /opensea/collections/{slug}` - Collection details
- `GET /opensea/collections/{slug}/floor` - Floor price

**Markets** (`/api/v1/markets/`)
- `GET /markets/overview` - Market overview
- `GET /markets/yields` - Protocol yields
- `GET /markets/tokens/{symbol}` - Token data

**Alerts** (`/api/v1/alerts/`)
- `GET /alerts/risk` - Risk alerts
- `PUT /alerts/risk/{id}/acknowledge` - Acknowledge
- `GET /alerts/subscription` - Get preferences
- `PUT /alerts/subscription` - Update preferences

**Search** (`/api/v1/search/`)
- `GET /search/history` - Search history
- `GET /search/suggestions` - Suggestions

**Comparison** (`/api/v1/comparison/`)
- `POST /comparison/protocols` - Compare protocols

**Transactions** (`/api/v1/transactions/`)
- `POST /transactions` - Log transaction
- `GET /transactions` - Transaction history

**Dashboard** (`/api/v1/dashboard/`)
- `GET /dashboard/insights` - AI insights
- `GET /dashboard/summary` - Summary

**Admin** (`/api/v1/admin/`)
- `POST /admin/projects` - Create project
- `/admin/agent/` - Agent management
- `/admin/llm/` - LLM config
- `/admin/distillation/` - Distillation config
- `/admin/user/` - User management

---

## 🎓 INTEGRATION PATTERNS

### Pattern 1: Progressive Enhancement

Start with basic features, progressively add advanced capabilities:

1. **Week 1**: Portfolio tracking + basic chat
2. **Week 2**: Add Agent Squad (5 free agents)
3. **Week 3**: Enable Hunter AI sentiment
4. **Week 4**: Add DeFi protocol integrations (Aave, Morpho)
5. **Week 5**: Upgrade to Pro (10 agents, full Hunter AI)
6. **Week 6**: Enable GraphRAG protocol search
7. **Week 7**: Add Agno autonomous agents
8. **Week 8**: Enterprise upgrade (18 agents, all features)

### Pattern 2: Use Case-Driven Architecture

Map business needs to Anvil features:

**Use Case**: "I want passive DeFi yield"
- **Features**: DeFi Yield Optimizer Agent + Morpho/Aave MCPs + LendingAgent (Agno)
- **Flow**: User asks → Agent finds opportunities → Agno auto-rebalances → Notifications

**Use Case**: "I need risk monitoring"
- **Features**: Risk Analyzer Agent + Portfolio Risk API + Real-time Alerts
- **Flow**: Continuous monitoring → Alert on threshold → Emergency withdrawal automation

**Use Case**: "I want to trade perpetuals"
- **Features**: Hunter AI signals + Hyperliquid MCP + PerpetualAgent (Agno)
- **Flow**: Hunter AI generates signal → User approves → Agno executes trade with stop-loss

### Pattern 3: Multi-Agent Workflows

Chain multiple agents for complex tasks:

```
User Request: "Optimize my portfolio for tax efficiency and maximum yield"

Workflow:
1. Portfolio Manager → Fetch current positions
2. Tax Optimizer → Identify tax-loss harvesting opportunities
3. DeFi Yield Optimizer → Find higher yield alternatives
4. Risk Analyzer → Validate risk levels
5. Compliance Monitor → Check regulatory compliance
6. Gas Optimizer → Plan optimal execution timing
7. Supervisor → Aggregate results and create unified plan
8. Transaction Executor → Execute approved plan
9. Alert & Monitoring → Monitor execution and alert on completion
```

---

## 📊 PERFORMANCE METRICS

Based on actual telemetry:

- **API Response Time**: P50: 450ms, P95: 1.2s
- **WebSocket Latency**: <50ms
- **Agent Squad Routing**: 20-50ms (intent classification)
- **MCP Server Calls**: 300-500ms average (parallel execution)
- **GraphRAG Search**: 400-600ms
- **Hunter AI Analysis**: 1.5-3s (comprehensive)
- **Portfolio Risk Calculation**: 800ms-1.5s
- **Cascade Simulation**: 1.5-2.5s (Monte Carlo 10K iterations)

---

## 🔒 SECURITY & COMPLIANCE

- **Authentication**: JWT + Privy Web3
- **Encryption**: HPKE for sensitive data (private keys)
- **Rate Limiting**: Tier-based (10-100 req/min)
- **Audit Logging**: All admin actions + transactions
- **Compliance**: SEC, FinCEN, IRS monitoring
- **Data Residency**: US/EU regions available
- **SOC 2**: Compliance in progress
- **Penetration Testing**: Quarterly audits

---

## 📞 SUPPORT

- **Free Tier**: Community Discord
- **Pro Tier**: Email support (24h response)
- **Enterprise Tier**: Priority support (4h response) + dedicated Slack channel

---

**Document Version**: 2.0.0
**Last Updated**: December 12, 2025
**Based On**: Actual Anvil Production Implementation
**Total Endpoints Documented**: 150+
**Total Use Cases**: 14 comprehensive examples
**Coverage**: Agent Squad, Agno Agents, MCPs, Hunter AI, Portfolio, DeFi, Cross-Chain, Projects, GraphRAG, Real-Time, Enterprise
