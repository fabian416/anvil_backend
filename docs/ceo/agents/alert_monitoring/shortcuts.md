# Alert Monitoring Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, alert types, and example responses for the **ALERT_MONITORING** agent.

---

## Query Patterns

### View Alerts

| Query | Intent | Description |
|-------|--------|-------------|
| "Show my alerts" | setup_alerts | Display recent alerts |
| "What security alerts are there?" | setup_alerts | Security alert overview |
| "Any critical alerts?" | setup_alerts | Filter critical only |
| "Show me today's alerts" | setup_alerts | Daily alert summary |
| "Alert history for last week" | setup_alerts | Historical lookup |

### Configure Alerts

| Query | Intent | Description |
|-------|--------|-------------|
| "Set up price alert for ETH" | setup_alerts | Price threshold alert |
| "Configure alert for large transactions" | setup_alerts | Whale alert |
| "Enable SMS for critical alerts" | setup_alerts | Channel configuration |
| "Add Slack integration" | setup_alerts | Team channel setup |

### Monitor Portfolio

| Query | Intent | Description |
|-------|--------|-------------|
| "Monitor my portfolio" | monitor_portfolio | Portfolio tracking |
| "Alert me if my position changes" | monitor_portfolio | Position alerts |
| "Track my DeFi positions" | monitor_portfolio | DeFi monitoring |
| "Watch my Aave position" | monitor_portfolio | Protocol-specific |

---

## Alert Types

### Protocol Exploits

| Alert | Severity | Description |
|-------|----------|-------------|
| Flash Loan Attack | 🔴 Critical | Uncollateralized loan exploit |
| Reentrancy Attack | 🔴 Critical | Recursive call exploitation |
| Oracle Manipulation | 🔴 Critical | Price feed exploitation |
| Access Control Breach | 🔴 Critical | Unauthorized access |

### Token Activity

| Alert | Severity | Description |
|-------|----------|-------------|
| Large Withdrawal | 🟠 High | Unusual fund movement |
| Whale Transfer | 🟠 High | Large token transfer |
| Unusual Volume | 🟡 Medium | Abnormal trading activity |
| Liquidity Change | 🟡 Medium | Pool liquidity shift |

### Governance

| Alert | Severity | Description |
|-------|----------|-------------|
| Critical Proposal | 🟠 High | Parameter changes |
| Voting Started | 🟡 Medium | New proposal vote |
| Execution Pending | 🟡 Medium | Approved proposal |
| Timelock Expiry | 🟢 Low | Upcoming execution |

### Smart Contracts

| Alert | Severity | Description |
|-------|----------|-------------|
| Proxy Upgrade | 🟠 High | Contract code change |
| Admin Change | 🟠 High | Ownership transfer |
| New Deployment | 🟡 Medium | Related contract |
| Verified Source | 🟢 Low | Verification status |

---

## Example Conversations

### View Recent Alerts

```
User: "Show my alerts"

Agent:
🚨 **SECURITY ALERTS - LAST 24 HOURS**

**Alert Summary**:
  🔴 Critical: 1
  🟠 High: 1
  🟡 Medium: 0
  🟢 Low: 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 **CRITICAL** - Protocol Exploit
**Protocol**: Euler Finance
**Description**: Flash loan attack detected
**Amount**: $197,000,000 USD
**Time**: 1h ago
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟠 **HIGH** - Large Token Movement
**Protocol**: Uniswap V3
**Description**: Unusual ETH withdrawal (10k ETH)
**Amount**: $25,000,000 USD
**Time**: 2h ago
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Monitoring**: 24/7 automated surveillance
**Powered By**: Forta Network
**Response Time**: < 5 seconds (critical alerts)

**Alert Channels**:
  📱 SMS (Critical only)
  📧 Email (All alerts)
  🔔 Push Notifications
  💬 Slack/Discord

**Custom Rules**: Configure your own alert rules
**False Positives**: Auto-learning ML suppression
```

### Configure Price Alert

```
User: "Set up price alert for ETH at $5000"

Agent:
✅ **Price Alert Configured**

**Asset**: Ethereum (ETH)
**Condition**: Price reaches $5,000 USD
**Current Price**: $2,500 USD
**Distance**: +100% to target

**Alert Settings**:
- Trigger: When ETH ≥ $5,000
- Channels: Email, Push Notification
- Frequency: Once (then auto-disable)

**Notification Preview**:
```
🔔 Price Alert: ETH has reached $5,000!
Current: $5,002.35 | Change: +100.1%
```

**Additional Options**:
- "Also alert me if ETH drops below $2,000"
- "Send SMS for this alert"
- "Create recurring alert"

📌 *You'll be notified as soon as the target is reached.*
```

### Critical Alert Only

```
User: "Any critical alerts?"

Agent:
🔴 **CRITICAL ALERTS ONLY**

**Total Critical Alerts**: 1 (Last 24 hours)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 **CRITICAL** - Protocol Exploit
**Protocol**: Euler Finance
**Type**: Flash Loan Attack
**Description**: Flash loan attack detected - funds at risk
**Amount**: $197,000,000 USD
**Time**: 1h ago
**Status**: Active incident

**Recommended Actions**:
1. ⚠️ Avoid interacting with Euler Finance
2. 🔒 Check if you have positions in Euler
3. 📰 Monitor official channels for updates
4. 🛡️ Consider revoking approvals

**Official Response**: Euler team investigating
**Incident Link**: https://twitter.com/eulerfinance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Your Exposure**:
- You have no positions in Euler Finance ✅
- No action required for your portfolio

📌 *Critical alerts are also sent via SMS.*
```

### Weekly Summary

```
User: "Alert history for last week"

Agent:
📊 **ALERT HISTORY - LAST 7 DAYS**

**Summary**:
| Severity | Count | Trend |
|----------|-------|-------|
| 🔴 Critical | 2 | ↓ (vs 5 last week) |
| 🟠 High | 8 | ↑ (vs 3 last week) |
| 🟡 Medium | 23 | → (stable) |
| 🟢 Low | 45 | → (stable) |

**Top Protocols by Alerts**:
1. Uniswap V3 - 12 alerts
2. Aave V3 - 8 alerts
3. Curve Finance - 6 alerts
4. Compound - 4 alerts
5. Others - 48 alerts

**Alert Types Distribution**:
- Token Movements: 35%
- Governance: 25%
- Protocol Updates: 20%
- Security: 10%
- Other: 10%

**Critical Incidents This Week**:
1. Day 3: Flash loan attack on Protocol X ($50M)
2. Day 5: Large withdrawal from Binance (500K ETH)

**Your Portfolio Impact**:
- No direct exposure to exploited protocols ✅
- 0 alerts directly affecting your positions

**Trend Analysis**:
The week showed increased whale activity and governance 
proposals ahead of upcoming protocol upgrades.

📌 *Weekly reports are sent every Monday at 9 AM.*
```

---

## Alert Configuration Commands

### Price Alerts

```
"Alert me when ETH reaches $5000"
"Set price alert for BTC at $100k"
"Notify me if USDC depegs below $0.99"
"Track SOL price above $200"
```

### Volume Alerts

```
"Alert on large ETH transactions over $1M"
"Notify me of whale movements"
"Track unusual trading volume"
"Watch for liquidity changes in Uniswap"
```

### Protocol Alerts

```
"Monitor Aave for governance proposals"
"Alert me of any Curve updates"
"Watch for Compound parameter changes"
"Track MakerDAO vault liquidations"
```

### Position Alerts

```
"Alert if my health factor drops below 1.5"
"Notify me of liquidation risk"
"Track my yield farming positions"
"Monitor my lending positions"
```

---

## Channel Configuration

### Enable SMS

```
User: "Enable SMS for critical alerts"

Agent:
📱 **SMS Alerts Configured**

**Phone Number**: +1 (555) ***-**42
**Status**: Verified ✅

**SMS Alert Rules**:
- 🔴 Critical alerts: Immediate SMS
- 🟠 High alerts: No SMS (email only)
- 🟡 Medium alerts: No SMS
- 🟢 Low alerts: No SMS

**Test SMS**: Sent! Check your phone.

**Note**: Standard messaging rates apply.
SMS is reserved for critical alerts only to avoid 
notification fatigue.

📌 *You can change this anytime with "Disable SMS alerts"*
```

### Add Slack Integration

```
User: "Add Slack integration"

Agent:
💬 **Slack Integration Setup**

**Step 1**: Click the link below to authorize Anvil
🔗 [Add to Slack](https://anvil.app/slack-connect)

**Step 2**: Select your workspace and channel

**Step 3**: Configure alert types:
- [ ] Critical alerts
- [ ] High alerts
- [ ] Medium alerts
- [ ] Low alerts
- [ ] Daily digest

**Webhook URL** (for advanced users):
`https://hooks.slack.com/services/YOUR/WEBHOOK/URL`

**Benefits**:
- Real-time team alerts
- Threaded discussions on incidents
- Action buttons for quick response
- Integration with Slack workflows

📌 *Need help? Say "Help with Slack setup"*
```

---

## API Response Examples

### Alert Summary Query

```json
{
  "agent_message": {
    "content": "🚨 **SECURITY ALERTS - LAST 24 HOURS**\n\n**Alert Summary**:...",
    "role": "assistant",
    "agent_type": "alert_monitoring"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "alert_monitoring", "duration_ms": 800}
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Forta",
        "url": "https://forta.org/",
        "citation_text": "Security alerts from Forta Network",
        "data_points_used": 5,
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
    "alert_count": 5,
    "critical_alerts": 1
  }
}
```

---

## Severity Reference

| Level | Icon | Response Time | Channels |
|-------|------|---------------|----------|
| Critical | 🔴 | < 5 seconds | SMS + All |
| High | 🟠 | < 1 minute | Email + Push + Slack |
| Medium | 🟡 | < 5 minutes | Email + Slack |
| Low | 🟢 | Daily digest | Email only |

---

## Forta Network Info

### What is Forta?

Forta is a decentralized detection network for real-time security monitoring:

- **24/7 Monitoring**: Continuous blockchain surveillance
- **Detection Bots**: Community-built security agents
- **Real-Time Alerts**: Sub-second detection
- **Multi-Chain**: Ethereum, Polygon, Arbitrum, etc.

### Detection Categories

| Category | Examples |
|----------|----------|
| Exploits | Flash loans, reentrancy |
| Token Activity | Whale movements, liquidations |
| Governance | Proposals, voting |
| Protocol Health | TVL changes, utilization |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Alert Monitoring Agent Shortcuts**
