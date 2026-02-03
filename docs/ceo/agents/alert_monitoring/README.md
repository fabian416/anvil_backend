# Alert Monitoring Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Implemented (Enhancement Planned)
**Agent Type**: Enterprise Agent
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **ALERT_MONITORING** agent provides real-time security alerts and anomaly detection using the Forta Network. It monitors DeFi protocols for exploits, unusual activity, and security threats, delivering alerts through multiple channels.

### Key Differentiators

- **Real-Time Monitoring**: 24/7 automated surveillance
- **Multi-Channel Alerts**: SMS, email, push, Slack/Discord
- **Forta Network**: Decentralized security monitoring
- **ML-Powered Detection**: Anomaly detection with false positive suppression
- **Custom Rules**: User-defined alert configurations

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and alert types |

---

## Quick Start

### For Users

**Alert Queries:**
```
• "Show my alerts"
• "What security alerts are there today?"
• "Set up price alert for ETH at $5000"
• "Configure alert for large transactions"
• "Show me critical alerts only"
• "Alert history for last week"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for alert types and channels

---

## Key Features

### 1. Alert Types

| Type | Severity | Description |
|------|----------|-------------|
| **Protocol Exploit** | Critical | Flash loans, reentrancy attacks |
| **Large Token Movement** | High | Unusual withdrawals, whale activity |
| **Smart Contract Upgrade** | High | Proxy upgrades, code changes |
| **Price Manipulation** | Critical | Oracle attacks, MEV |
| **Governance Proposal** | Medium | DAO votes, parameter changes |
| **Unusual Patterns** | Medium | ML-detected anomalies |

### 2. Alert Channels

| Channel | Use Case | Severity Threshold |
|---------|----------|-------------------|
| **SMS (Twilio)** | Critical alerts | Critical only |
| **Email** | All notifications | All severities |
| **Push Notifications** | Mobile alerts | High+ |
| **Slack/Discord** | Team channels | All severities |
| **Webhook** | Custom integrations | All severities |

### 3. Severity Levels

| Severity | Icon | Response Time | Action Required |
|----------|------|---------------|-----------------|
| 🔴 Critical | Immediate | < 5 seconds | Immediate action |
| 🟠 High | Fast | < 1 minute | Review soon |
| 🟡 Medium | Normal | < 5 minutes | Monitor |
| 🟢 Low | Batched | Daily digest | Informational |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Routing)
Infrastructure Layer → AlertMonitoringAgentForta
    ↓
External Systems
    - Forta Network (Security alerts)
    - Twilio (SMS notifications)
    - Vertex AI (LLM analysis)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 ALERT MONITORING FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Show my alerts"                                     │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │   Supervisor            │                               │
│  │   Detects: alert query  │                               │
│  │   → routes to alert     │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   AlertMonitoringAgent  │                               │
│  │                         │                               │
│  │  1. Fetch recent alerts │ → Forta API                   │
│  │  2. Generate summary    │ → LLM analysis                │
│  │  3. Format response     │ → Severity grouping           │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  Response: Alert summary with severity breakdown             │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Detection

```python
# From intent_classifier.py
intent_to_agent = {
    "setup_alerts": AgentType.ALERT_MONITORING,
    "monitor_portfolio": AgentType.ALERT_MONITORING,
}
```

### Agent Classification

```
- alert_monitoring: Real-time alerts (enterprise)
```

---

## Forta Network Integration

### What is Forta?

Forta is a decentralized detection network for real-time security monitoring of blockchain activity. It uses community-built detection bots to identify threats, exploits, and anomalies.

### Detection Capabilities

| Category | Examples |
|----------|----------|
| **Exploits** | Flash loan attacks, reentrancy |
| **Token Activity** | Large transfers, whale movements |
| **Governance** | Proposal submissions, voting |
| **Protocol Health** | TVL changes, utilization spikes |
| **Smart Contracts** | Upgrades, suspicious deployments |

---

## Configuration

### Default Parameters

```python
# From alert_monitoring_agent_forta.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.2           # Factual
max_tokens = 1500           # Detailed summaries
```

### Response Structure

```python
AgentResponse(
    content="Alert summary with severity breakdown...",
    agent_type=AgentType.ALERT_MONITORING,
    tools_used=["forta_api", "openai_api"],
    sources=[
        SourceInfo(source_type="api", source_name="Forta",
                   url="https://forta.org/",
                   citation_text="Security alerts from Forta Network"),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated by gemini-2.0-flash"),
    ],
    metadata={
        "latency_ms": 500,
        "alert_count": 5,
        "critical_alerts": 1,
    },
)
```

---

## Alert Response Example

```
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

---

## Future Enhancements (TODO)

### 1. Real Forta API Integration

```python
# TODO: Implement real Forta API integration
async def _get_recent_alerts(self, hours: int = 24) -> list[dict]:
    # Query Forta Network API
    # Filter by user's monitored protocols
    # Return structured alerts
    pass
```

### 2. Custom Alert Rules

- User-defined price thresholds
- Protocol-specific monitoring
- Custom severity mappings

### 3. Multi-Channel Delivery

- SMS integration via Twilio
- Email notifications
- Slack/Discord webhooks
- Mobile push notifications

---

## Testing Checklist

### Unit Tests
- [ ] Alert fetching logic
- [ ] Severity classification
- [ ] Summary generation
- [ ] Time formatting

### Integration Tests
- [ ] Forta API integration
- [ ] LLM response generation
- [ ] Source attribution

### E2E Tests
- [ ] Complete alert flow
- [ ] Multi-channel delivery
- [ ] Custom rule triggering

---

## Related Documentation

- **Risk Analyzer Agent**: `/docs/ceo/agents/risk_analyzer/` (protocol risk)
- **Security Auditor Agent**: `/docs/ceo/agents/security_auditor/` (contract security)
- **Crisis Manager Agent**: `/docs/ceo/agents/crisis_manager/` (emergency response)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Alert Monitoring Agent Specification**
