# Alert Monitoring Agent - Complete Index

> **Project:** Anvil DeFi Chat - Real-Time Security Alerts
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Implemented (Enhancement Planned)
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **ALERT_MONITORING** agent, Anvil's system for real-time security alerts and anomaly detection using the Forta Network.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and alert types |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Forta Network integration
- Multi-channel alert delivery
- Severity classification

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Alert summary generation

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Alert queries and configurations:

**Key Contents:**
- Alert type queries
- Configuration commands
- Channel preferences
- Historical lookups

---

## 🎯 Implementation Status

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| Forta Integration | 🔲 Mock | Real API pending |
| Alert Fetching | ✅ | Recent alerts retrieval |
| Severity Classification | ✅ | 4-level severity |
| Summary Generation | ✅ | LLM-powered summaries |
| Source Attribution | ✅ | Forta + LLM sources |

### Planned Enhancements (TODO)

| Feature | Status | Description |
|---------|--------|-------------|
| Real Forta API | 🔲 | Live security alerts |
| Twilio SMS | 🔲 | Critical alert SMS |
| Custom Rules | 🔲 | User-defined alerts |
| Slack/Discord | 🔲 | Team channel integration |

---

## 📊 Alert Reference

### Severity Levels

| Severity | Icon | Response Time |
|----------|------|---------------|
| Critical | 🔴 | < 5 seconds |
| High | 🟠 | < 1 minute |
| Medium | 🟡 | < 5 minutes |
| Low | 🟢 | Daily digest |

### Alert Types

| Type | Severity | Description |
|------|----------|-------------|
| Protocol Exploit | Critical | Active attacks |
| Large Movements | High | Whale activity |
| Contract Upgrade | High | Code changes |
| Governance | Medium | DAO proposals |

---

## 🔗 Related Specifications

### Agent Dependencies

- **LLM Client**: Vertex AI for alert analysis
- **Forta Client**: Security alert source (TODO)
- **Twilio Client**: SMS notifications (TODO)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/enterprise/alert_monitoring_agent_forta.py`
- `src/app/infrastructure/adapters/agent_squad/agents/source_helpers.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_alert_monitoring_agent)

**Domain Layer:**
- `src/app/domain/enums/agent_type.py` (AgentType.ALERT_MONITORING)

**Intent Classification:**
- `src/app/domain/services/agent_squad/intent_classifier.py`

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-29
**Review Frequency:** Monthly

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**For questions or clarifications, refer to the README.md in this directory.**
