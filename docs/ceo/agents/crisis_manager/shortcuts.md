# Crisis Manager Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, crisis types, and example responses for the **CRISIS_MANAGER** agent.

---

## Query Patterns

### Crisis Status

| Query | Intent | Description |
|-------|--------|-------------|
| "Am I affected by any exploits?" | crisis_response | Check personal exposure |
| "Show active crises" | crisis_response | List current crises |
| "What's my crisis status?" | crisis_response | Overall safety status |
| "Any protocol exploits today?" | crisis_response | Recent exploit check |

### Emergency Actions

| Query | Intent | Description |
|-------|--------|-------------|
| "Emergency withdraw from Aave" | emergency_withdrawal | Manual emergency exit |
| "Exit all positions now" | emergency_withdrawal | Full portfolio exit |
| "Revoke all approvals" | emergency_withdrawal | Remove token approvals |
| "Pause my strategies" | crisis_response | Stop automated actions |

### Configuration

| Query | Intent | Description |
|-------|--------|-------------|
| "Enable auto-exit for my positions" | crisis_response | Enable automated exit |
| "Set auto-exit threshold to $5000" | crisis_response | Configure threshold |
| "Disable automatic responses" | crisis_response | Manual mode only |
| "Configure emergency contacts" | crisis_response | Notification setup |

### Historical

| Query | Intent | Description |
|-------|--------|-------------|
| "Show crisis history" | crisis_response | Past crisis events |
| "What happened to Euler?" | crisis_response | Specific incident |
| "Show my saved positions" | crisis_response | Funds protected |

---

## Crisis Types

### Critical Severity

| Type | Description | Example |
|------|-------------|---------|
| **Flash Loan Attack** | Uncollateralized loan exploit | Euler ($197M) |
| **Reentrancy Attack** | Recursive call exploitation | DAO Hack ($60M) |
| **Oracle Manipulation** | Price feed exploitation | bZx ($8M) |
| **Access Control Breach** | Unauthorized function call | Parity Wallet |

### High Severity

| Type | Description | Example |
|------|-------------|---------|
| **Bridge Hack** | Cross-chain bridge exploit | Ronin ($625M) |
| **Governance Attack** | Malicious proposal execution | Beanstalk ($182M) |
| **Depeg Event** | Stablecoin loses peg | UST ($40B) |
| **Liquidity Drain** | Pool liquidity theft | Cream Finance |

### Medium Severity

| Type | Description | Example |
|------|-------------|---------|
| **Unusual Activity** | Abnormal transaction patterns | Pre-exploit signals |
| **Large Withdrawals** | Whale exits from protocol | Potential insider |
| **Governance Proposal** | Parameter change request | Risk adjustment |

---

## Example Conversations

### Crisis Status (All Clear)

```
User: "What's my crisis status?"

Agent:
🟢 **CRISIS STATUS: ALL CLEAR**

No active protocol crises detected.

**Monitoring**: 24/7 automated surveillance
**Response Time**: < 5 seconds (exploit detection)
**Auto-Exit**: Enabled (positions > $1,000)

**Last Check**: Just now
**Protocols Monitored**: All supported protocols
**User Exposure**: $0 at risk

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Crisis Management**: Active
**Circuit Breakers**: Armed
**Emergency Contacts**: Configured

Your funds are safe. We're watching 24/7.
```

### Active Crisis Alert

```
User: "Am I affected by any exploits?"

Agent:
🚨 **CRISIS ALERT - AUTOMATED RESPONSE ACTIVE**

**Crisis ID**: CRS-001
**Protocol**: Euler Finance
**Event Type**: FLASH_LOAN_ATTACK
**Severity**: 🔴 CRITICAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**IMPACT ASSESSMENT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Total Protocol Loss**: $197,000,000 USD
**Your Exposure**: $50,000 USD
**Status**: ⚠️ ACTIVE

**Detection Time**: 2500ms
**Response Time**: < 5 seconds (automated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**AUTOMATED ACTIONS TAKEN** ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Emergency Withdrawal**
  Amount: $48,000 USD
  Status: COMPLETED
  Destination: Your safe wallet

✅ **Token Approvals Revoked**
  Approvals: 3 approvals
  Status: COMPLETED
  Protection: No further exposure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**POSITIONS SAVED** 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Euler Finance - USDC
  Amount Saved: $48,000 USD

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**FINANCIAL OUTCOME**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Losses Prevented**: $48,000 USD
**Your Safety**: ✅ Funds secured
**Recovery Time**: Immediate (funds in wallet)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**CRISIS MANAGEMENT SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Response**: ✅ Automated (no user action required)
**Outcome**: ✅ Funds saved (100% recovery)
**Notification**: 📱 Sent via SMS, Email, Push

**Post-Mortem**: Available in 24-48 hours
**Compensation**: Check with protocol team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Crisis Response**: Automated 24/7
**Detection Partner**: Forta Network
**Execution**: Privy Embedded Wallet

*Your funds are now safe. Crisis management protocol executed
successfully. No further action required.*
```

### Manual Emergency Withdrawal

```
User: "Emergency withdraw from Aave"

Agent:
🚨 **EMERGENCY WITHDRAWAL REQUEST**

**Protocol**: Aave V3
**Your Positions**:
| Asset | Amount | Value USD |
|-------|--------|-----------|
| USDC | 10,000 | $10,000 |
| ETH | 2.5 | $6,250 |
| **Total** | | **$16,250** |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ CONFIRMATION REQUIRED**

This action will:
1. Withdraw all assets from Aave V3
2. Transfer $16,250 to your wallet
3. Revoke Aave token approvals

**Estimated Gas**: ~$5.50
**Execution Time**: ~30 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reply "CONFIRM EMERGENCY EXIT" to proceed.

**Note**: This amount exceeds your auto-exit threshold ($1,000).
User confirmation is required for safety.
```

### Configure Auto-Exit

```
User: "Set auto-exit threshold to $5000"

Agent:
⚙️ **AUTO-EXIT CONFIGURATION UPDATED**

**Previous Threshold**: $1,000 USD
**New Threshold**: $5,000 USD

**What This Means**:
- Positions ≤ $5,000: Auto-exit without confirmation
- Positions > $5,000: Requires your confirmation

**Auto-Exit Status**: ✅ Enabled

**Current Protection**:
| Protocol | Position | Auto-Exit? |
|----------|----------|------------|
| Aave V3 | $16,250 | ❌ Needs confirmation |
| Compound | $2,500 | ✅ Auto-exit enabled |
| Uniswap LP | $8,000 | ❌ Needs confirmation |

**Response Time**: < 5 seconds (exploit detection)
**Execution Time**: < 30 seconds (withdrawal)

📌 *You can change this anytime with "Set auto-exit threshold to $X"*
```

### Crisis History

```
User: "Show crisis history"

Agent:
📜 **CRISIS HISTORY - LAST 30 DAYS**

**Summary**:
| Metric | Value |
|--------|-------|
| Crises Detected | 3 |
| Your Exposure Events | 1 |
| Funds Saved | $48,000 |
| Response Success Rate | 100% |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CRS-001** | 🔴 CRITICAL | Jan 25, 2026
**Protocol**: Euler Finance
**Event**: Flash Loan Attack
**Total Loss**: $197,000,000
**Your Outcome**: ✅ $48,000 saved (auto-exit)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CRS-002** | 🟠 HIGH | Jan 20, 2026
**Protocol**: Curve Finance
**Event**: Pool Imbalance
**Total Loss**: $0 (averted)
**Your Outcome**: ✅ Not affected (no position)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CRS-003** | 🟡 MEDIUM | Jan 15, 2026
**Protocol**: Compound
**Event**: Governance Proposal
**Total Loss**: $0 (monitoring)
**Your Outcome**: ℹ️ Notified only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Lifetime Stats**:
- Total crises detected: 15
- Funds saved: $48,000
- False positives: 0
- Response time avg: 3.2 seconds

📌 *Crisis protection is always active.*
```

---

## API Response Examples

### Crisis Status Query

```json
{
  "agent_message": {
    "content": "🚨 **CRISIS ALERT - AUTOMATED RESPONSE ACTIVE**\n\n**Crisis ID**: CRS-001...",
    "role": "assistant",
    "agent_type": "crisis_manager"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "crisis_manager", "duration_ms": 1200}
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Forta",
        "url": "https://forta.org/",
        "citation_text": "Crisis detection from Forta Network",
        "data_points_used": 1,
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "Privy",
        "url": "https://privy.io/",
        "citation_text": "Wallet operations via Privy",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  },
  "metadata": {
    "active_crises": 1,
    "user_affected": true
  }
}
```

---

## Automated Actions Reference

### Action Types

| Action | Description | Trigger |
|--------|-------------|---------|
| **WITHDRAW_ALL** | Emergency withdrawal | Exploit detected |
| **REVOKE_APPROVALS** | Remove token approvals | Any crisis |
| **EXIT_LIQUIDITY** | Remove LP positions | Pool exploit |
| **PAUSE_STRATEGIES** | Stop automated farming | Critical crisis |
| **NOTIFY_USER** | Multi-channel alert | All crises |

### Response Timeline

| Phase | Time | Action |
|-------|------|--------|
| Detection | 0-5s | Forta identifies exploit |
| Evaluation | 5-10s | Check user exposure |
| Execution | 10-30s | Auto-exit (if enabled) |
| Notification | 30-60s | Multi-channel alert |
| Report | 60-120s | Full crisis report |

---

## Safety Thresholds

| Amount | Behavior |
|--------|----------|
| ≤ $1,000 (default) | Auto-exit without confirmation |
| > $1,000 | Requires user confirmation |
| Configurable | User can adjust threshold |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Crisis Manager Agent Shortcuts**
