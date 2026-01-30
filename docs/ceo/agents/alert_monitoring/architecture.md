# Alert Monitoring Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **ALERT_MONITORING** agent, which provides real-time security alerts and anomaly detection using the Forta Network.

### Key Components

- **AlertMonitoringAgentForta**: Agent Squad implementation
- **Forta Client**: Security alert source
- **Twilio Client**: SMS notifications
- **LLM Client**: Vertex AI for analysis

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  ALERT MONITORING ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Supervisor             │
                    │  (Intent Routing)        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ AlertMonitoringAgent     │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       ▼                         ▼                         ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Forta Network  │   │   Vertex AI     │   │   Twilio        │
│  (Security)     │   │   (LLM)         │   │   (SMS)         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Enterprise Agents
    ALERT_MONITORING = "alert_monitoring"  # Real-time alerts
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "setup_alerts": AgentType.ALERT_MONITORING,
    "monitor_portfolio": AgentType.ALERT_MONITORING,
}
```

---

## Infrastructure Layer

### AlertMonitoringAgentForta

**File**: `src/app/infrastructure/adapters/agent_squad/agents/enterprise/alert_monitoring_agent_forta.py`
**Lines**: ~231

```python
class AlertMonitoringAgentForta:
    """
    Alert Monitoring Agent Forta implementation.
    
    Implements: AgentGateway
    
    Purpose: Real-time security alerts & anomaly detection
    
    Capabilities:
    - Real-time security monitoring (Forta network)
    - Anomaly detection (ML-powered)
    - Multi-channel alerts (SMS, email, push, Slack)
    - Custom alert rules (user-defined)
    - Alert prioritization (critical, high, medium, low)
    - Historical alert dashboard
    - False positive suppression
    
    Alert Types:
    - Protocol exploits (flash loans, reentrancy)
    - Unusual transaction patterns
    - Large token movements
    - Smart contract upgrades
    - Governance proposals
    - Price manipulations
    
    Channels:
    - SMS (Twilio) - Critical only
    - Email - All alerts
    - Push notifications (iOS, Android)
    - Slack/Discord - Team channels
    - Webhook - Custom integrations
    
    Model: gemini-2.0-flash (fast alerting)
    Temperature: 0.2 (factual)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 52-67 | Initialize with clients |
| `agent_type` | 69-72 | Return AgentType.ALERT_MONITORING |
| `execute` | 74-135 | Main entry point |
| `is_available` | 137-139 | Availability check |
| `_get_recent_alerts` | 141-165 | Fetch alerts (mock) |
| `_generate_alert_summary` | 167-219 | Format alert summary |
| `_format_time_ago` | 221-230 | Time formatting |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI
    forta_client: Any,                  # FortaClient (TODO)
    twilio_client: Any,                 # TwilioClient (TODO)
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_tokens: int = 1500,
):
```

---

## Forta Network Integration

### What is Forta?

Forta is a decentralized real-time threat detection network for blockchain activity. It consists of:

- **Detection Bots**: Community-built monitoring agents
- **Scan Nodes**: Infrastructure for running detection bots
- **Alert API**: Programmatic access to security alerts

### Detection Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Exploits** | Active attacks | Flash loans, reentrancy |
| **Token Activity** | Large movements | Whale transfers, liquidations |
| **Governance** | DAO activity | Proposals, voting |
| **Protocol Health** | Metrics changes | TVL drops, utilization spikes |
| **Smart Contracts** | Code changes | Upgrades, deployments |

### Mock Implementation

```python
async def _get_recent_alerts(self, hours: int = 24) -> list[dict]:
    """Get recent alerts from Forta."""
    # TODO: Implement real Forta API integration
    
    # Mock alerts
    return [
        {
            "id": "ALERT-001",
            "severity": "CRITICAL",
            "type": "Protocol Exploit",
            "protocol": "Euler Finance",
            "description": "Flash loan attack detected",
            "amount_usd": 197000000,
            "timestamp": time.time() - 3600,
        },
        # ... more alerts
    ]
```

---

## Alert Severity System

### Severity Levels

| Level | Icon | Response Time | Delivery |
|-------|------|---------------|----------|
| Critical | 🔴 | < 5 seconds | SMS + All channels |
| High | 🟠 | < 1 minute | Email + Push + Slack |
| Medium | 🟡 | < 5 minutes | Email + Slack |
| Low | 🟢 | Daily digest | Email only |

### Severity Classification

```python
severity_emoji = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}
```

---

## Multi-Channel Alert Delivery

### Channel Configuration

| Channel | Provider | Use Case |
|---------|----------|----------|
| **SMS** | Twilio | Critical only |
| **Email** | SendGrid | All alerts |
| **Push** | Firebase | Mobile alerts |
| **Slack** | Slack API | Team channels |
| **Discord** | Discord API | Community |
| **Webhook** | Custom | Integrations |

### Delivery Logic

```
Critical Alert:
  1. SMS → Twilio (immediate)
  2. Email → SendGrid (immediate)
  3. Push → Firebase (immediate)
  4. Slack → Webhook (immediate)

High Alert:
  1. Email → SendGrid (immediate)
  2. Push → Firebase (immediate)
  3. Slack → Webhook (immediate)

Medium Alert:
  1. Email → SendGrid (batched)
  2. Slack → Webhook (batched)

Low Alert:
  1. Email → Daily digest
```

---

## Source Attribution

### Forta Source

```python
sources.append(create_api_source(
    source_name="Forta",
    url="https://forta.org/",
    citation_text="Security alerts from Forta Network",
    fetched_at=fetched_at,
    provider="Forta API",
    data_points_used=len(alerts),
))
```

### LLM Source

```python
sources.append(create_llm_source(
    model=self._model,
    fetched_at=fetched_at,
))
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_alert_monitoring_agent(
    self, llm_client: LLMClientGateway
) -> AlertMonitoringAgentForta:
    """Provide Alert Monitoring agent."""
    from unittest.mock import MagicMock
    return AlertMonitoringAgentForta(
        llm_client=llm_client,
        forta_client=MagicMock(),   # TODO: Real client
        twilio_client=MagicMock(),  # TODO: Real client
    )
```

### Agent Registry

```python
AgentType.ALERT_MONITORING: alert_monitoring_agent,
```

---

## Alert Summary Generation

### Summary Structure

```python
async def _generate_alert_summary(
    self,
    alerts: list[dict],
    conversation_context: ConversationContext,
) -> str:
    """Generate alert summary."""
    critical_count = sum(1 for a in alerts if a["severity"] == "CRITICAL")
    high_count = sum(1 for a in alerts if a["severity"] == "HIGH")
    
    summary = f"""🚨 **SECURITY ALERTS - LAST 24 HOURS**

**Alert Summary**:
  🔴 Critical: {critical_count}
  🟠 High: {high_count}
  🟡 Medium: 0
  🟢 Low: 0
"""
    # ... format individual alerts
    return summary
```

---

## Response Structure

```python
return AgentResponse(
    content=summary,
    agent_type=self.agent_type,
    tools_used=["forta_api", "openai_api"],
    sources=sources,
    metadata={
        "latency_ms": latency_ms,
        "alert_count": len(alerts),
        "critical_alerts": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
    },
)
```

---

## Future Enhancements

### TODO Items

```python
# TODO: Implement real Forta API integration
# TODO: Implement Twilio SMS for critical alerts
# TODO: Implement custom alert rules
# TODO: Implement Slack/Discord webhooks
```

### Planned Features

1. **Real Forta API**
   - Live security alerts
   - User-specific monitoring
   - Protocol filtering

2. **SMS Notifications**
   - Twilio integration
   - Critical alerts only
   - User phone verification

3. **Custom Rules**
   - Price thresholds
   - Volume alerts
   - Protocol-specific rules

4. **Team Integrations**
   - Slack webhooks
   - Discord bots
   - Custom webhooks

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Alert fetching | < 500ms | Forta API |
| Summary generation | < 1s | Vertex AI |
| Total | < 1.5s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added mock alert data |
| 2026-01-29 | Added source attribution |
