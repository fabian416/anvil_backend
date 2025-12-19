# Master Chat System Specification
## Enterprise-Grade Conversational AI Platform

**Version**: 1.0.0
**Date**: December 15, 2025
**Status**: In Development
**Architecture**: Hexagonal (Clean Architecture) with CQRS, FastAPI, SQLAlchemy, Redis, Celery

---

## 🎯 Executive Summary

Complete specification for Anvil's Enterprise Chat & Collaboration system, covering all 30 use cases, 18 agents, API implementations, testing strategy, and agent disable/enable scenarios.

### Scope

- **Use Cases**: 30 comprehensive enterprise chat features
- **Agents**: All 18 specialized agents with enable/disable analysis
- **APIs**: 15+ REST and WebSocket endpoints
- **Testing**: Unit, integration, E2E test coverage
- **Performance**: Sub-second response times, 99.9% uptime
- **Compliance**: GDPR, CCPA, SOC2, HIPAA ready

---

## 📋 Table of Contents

1. [Use Cases Overview](#use-cases-overview)
2. [Agent Coverage Matrix](#agent-coverage-matrix)
3. [Agent Disable Impact Analysis](#agent-disable-impact)
4. [API Specification](#api-specification)
5. [Testing Strategy](#testing-strategy)
6. [Implementation Phases](#implementation-phases)
7. [Performance Requirements](#performance-requirements)
8. [Security & Compliance](#security-compliance)

---

## 1. Use Cases Overview {#use-cases-overview}

### ✅ Completed Use Cases (1-19)

| # | Use Case | Agent(s) | API | Status |
|---|----------|----------|-----|--------|
| 1 | Intelligent Query Routing | Agent Squad Router | POST /agent-squad/messages | ✅ Documented |
| 13 | WebSocket Real-Time Chat | Chat Agent | WS /chat/ws/{id} | ✅ Documented |
| 15 | Multi-Turn Persistent Context | Chat, Risk, Yield, Security | POST /conversations/{id}/messages | ✅ Documented |
| 16 | Conversation Branching | Chat, Risk, Yield, Security | POST /conversations/{id}/fork | ✅ Documented |
| 17 | Team Collaboration | All Agents | POST /conversations/shared | ✅ Documented |
| 18 | Advanced Search | All Agents | POST /conversations/search | ✅ Documented |
| 19 | AI Summarization | Summary Agent | POST /conversations/{id}/summarize | ✅ Documented |

### 🔄 Remaining Use Cases (20-30)

| # | Use Case | Primary Agent(s) | Priority | Complexity |
|---|----------|------------------|----------|------------|
| 20 | Chat Analytics Dashboard | Analytics Agent | High | Medium |
| 21 | Conversation Templates | All Agents | High | Medium |
| 22 | Multi-Language Translation | Translation Agent | Medium | High |
| 23 | Personalization | Preference Agent | High | Low |
| 24 | External Integrations (Slack/Discord) | Integration Agent | Medium | High |
| 25 | Voice Chat & Transcription | Voice Agent | Low | High |
| 26 | Export & Compliance | Compliance Agent | High | Medium |
| 27 | Intent Detection | Intent Agent | High | Medium |
| 28 | Advanced Real-Time Collaboration | Collaboration Agent | Medium | High |
| 29 | Performance Optimization | Performance Agent | Medium | Medium |
| 30 | Advanced Agent Orchestration | Supervisor Agent | High | High |

---

## 2. Agent Coverage Matrix {#agent-coverage-matrix}

### 18 Specialized Agents

| Agent | Primary Function | Use Cases Involved | Critical? |
|-------|------------------|-------------------|-----------|
| **1. Chat Agent** | Base conversational AI | All (1-30) | ✅ Yes |
| **2. Risk Analyzer** | Portfolio risk assessment | 1, 15-21, 27, 30 | ✅ Yes |
| **3. Yield Optimizer** | Find best yield opportunities | 1, 15-21, 27, 30 | ✅ Yes |
| **4. Security Auditor** | Smart contract security | 1, 15-21, 27, 30 | ✅ Yes |
| **5. Portfolio Manager** | Portfolio tracking & management | 1, 15-21, 27, 30 | ✅ Yes |
| **6. Hunter AI** | Sentiment & price predictions | 1, 15-21, 27 | No |
| **7. Transaction Executor** | Execute trades & transactions | 21, 27, 30 | ✅ Yes |
| **8. Compliance Monitor** | AML/KYC & regulatory | 17, 20, 21, 26 | ✅ Yes |
| **9. Tax Optimizer** | Tax strategy & reporting | 20, 21, 26 | No |
| **10. Gas Optimizer** | Transaction cost optimization | 21, 27, 30 | No |
| **11. Research Assistant** | Protocol/token research | 18, 20, 21, 27 | No |
| **12. Multi-Sig Coordinator** | Treasury management | 17, 21, 30 | No |
| **13. Alert & Monitoring** | Real-time anomaly detection | 20, 21, 27, 29 | No |
| **14. Crisis Manager** | Emergency response | 21, 30 | No |
| **15. Bridge & Cross-Chain** | Cross-chain operations | 21, 30 | No |
| **16. Lending & Borrowing** | Leverage optimization | 21, 27, 30 | No |
| **17. NFT & Asset Manager** | NFT portfolio management | 21, 27 | No |
| **18. DAO Governance** | Voting & proposals | 21, 27 | No |

### Additional Specialized Agents (New for Chat)

| Agent | Function | Use Cases |
|-------|----------|-----------|
| **Analytics Agent** | Conversation analytics & insights | 20 |
| **Summary Agent** | AI-powered summarization | 19 |
| **Translation Agent** | Multi-language translation | 22 |
| **Preference Agent** | User personalization | 23 |
| **Integration Agent** | External platform sync | 24 |
| **Voice Agent** | Voice chat & transcription | 25 |
| **Export Agent** | Compliance exports | 26 |
| **Intent Agent** | Intent detection & suggestions | 27 |
| **Collaboration Agent** | Real-time collaboration | 17, 28 |
| **Performance Agent** | Performance monitoring | 29 |
| **Supervisor Agent** | Multi-agent orchestration | 1, 30 |

---

## 3. Agent Disable Impact Analysis {#agent-disable-impact}

### Purpose

Demonstrate the value of each agent by showing functionality degradation when disabled.

### Format (for each agent)

```markdown
### Agent: [Agent Name]

#### When Enabled
- Feature 1: [Full functionality description]
- Feature 2: [Full functionality description]
- Feature 3: [Full functionality description]

#### When Disabled
- Feature 1: ⚠️ [Degraded functionality - what happens instead]
- Feature 2: ❌ [Feature unavailable - fallback behavior]
- Feature 3: ⚠️ [Reduced quality - manual alternative]

#### Business Impact
- Time Impact: [e.g., "Tasks take 3x longer"]
- Quality Impact: [e.g., "20% less accurate recommendations"]
- User Experience: [e.g., "Users must manually research alternatives"]
- ROI: [e.g., "$5k/month in lost productivity"]

#### Example Scenario
**User Request**: [Specific user request]

**With Agent Enabled**:
[Full response with agent's contribution highlighted]

**With Agent Disabled**:
[Degraded response showing what's missing]
```

### Agent Disable Test Matrix

| Agent | Impact if Disabled | Workaround Available? | Criticality |
|-------|-------------------|----------------------|-------------|
| Chat Agent | ❌ No conversation possible | None | CRITICAL |
| Risk Analyzer | ⚠️ No risk scores, manual research needed | Partial | HIGH |
| Yield Optimizer | ⚠️ No yield recommendations | Partial | HIGH |
| Security Auditor | ⚠️ No security validation | Partial | HIGH |
| Transaction Executor | ❌ Cannot execute trades via chat | Manual execution | MEDIUM |
| Compliance Monitor | ⚠️ No automated compliance checks | Manual review | HIGH |
| Analytics Agent | ⚠️ No insights or trends | Basic stats only | LOW |
| Summary Agent | ⚠️ Manual summarization needed | User reads all | MEDIUM |
| Intent Agent | ⚠️ No auto-suggestions | User types fully | LOW |

---

## 4. API Specification {#api-specification}

### 4.1 Completed APIs

#### Chat Conversations

```yaml
POST /api/v1/chat/conversations
  Description: Create new conversation
  Auth: Required
  Request:
    title: string (optional)
    type: "personal" | "shared"
    initial_message: string (optional)
  Response:
    conversation_id: string
    created_at: datetime
    participants: array

POST /api/v1/chat/conversations/{id}/messages
  Description: Send message to conversation
  Auth: Required
  Request:
    message: string
    context_mode: "full_history" | "recent" | "minimal"
    streaming: boolean
    agent_preferences: object
  Response:
    message_id: string
    response: object
    agents_involved: array
    metadata: object

POST /api/v1/chat/conversations/{id}/fork
  Description: Create conversation branch
  Auth: Required
  Request:
    fork_from_message_id: string
    fork_name: string
    context_override: object
    initial_message: string
  Response:
    fork_id: string
    parent_conversation_id: string
    fork_metadata: object

POST /api/v1/chat/conversations/compare
  Description: Compare conversation strategies
  Auth: Required
  Request:
    conversation_ids: array[string]
    comparison_dimensions: array[string]
    output_format: "table" | "json" | "markdown"
  Response:
    comparison_table: object
    ai_summary: object
    merge_options: object

POST /api/v1/chat/conversations/shared
  Description: Create team shared conversation
  Auth: Required
  Request:
    title: string
    participants: array[object]
    collaboration_settings: object
    notification_settings: object
  Response:
    conversation_id: string
    participants: array
    collaboration_features: object

POST /api/v1/chat/conversations/search
  Description: Semantic search across conversations
  Auth: Required
  Request:
    query: string
    search_mode: "semantic" | "keyword" | "hybrid"
    filters: object
    page: integer
    page_size: integer
  Response:
    results: array
    facets: object
    total_results: integer

POST /api/v1/chat/conversations/{id}/summarize
  Description: AI-powered conversation summary
  Auth: Required
  Request:
    summarization_type: "brief" | "medium" | "comprehensive"
    include_sections: array[string]
    time_range: object
    language: string
  Response:
    summary: object
    metadata: object
    quick_actions: array

WS /api/v1/chat/ws/{conversation_id}
  Description: WebSocket real-time chat
  Auth: Required (via query param token)
  Events:
    - user_typing
    - message
    - message_chunk
    - message_complete
    - reaction_added
    - read_receipts_update
    - presence_update
```

### 4.2 Pending APIs (Use Cases 20-30)

```yaml
GET /api/v1/chat/analytics/dashboard
  Description: Chat analytics and insights
  Auth: Required
  Query Params:
    time_range: "7d" | "30d" | "90d"
    breakdown_by: "agent" | "user" | "topic"
  Response:
    conversation_metrics: object
    agent_usage: object
    trends: object

POST /api/v1/chat/templates/{template_id}/instantiate
  Description: Create conversation from template
  Auth: Required
  Request:
    template_id: string
    parameters: object
    schedule: object (optional)
  Response:
    conversation_id: string
    template_metadata: object

POST /api/v1/chat/conversations/{id}/translate
  Description: Translate conversation messages
  Auth: Required
  Request:
    target_language: string (ISO 639-1)
    mode: "real_time" | "batch"
    preserve_technical_terms: boolean
  Response:
    translated_messages: array
    translation_quality: object

PUT /api/v1/chat/preferences
  Description: Update user chat preferences
  Auth: Required
  Request:
    response_style: "brief" | "detailed" | "technical" | "executive"
    agent_preferences: object
    notification_settings: object
    display_settings: object
  Response:
    preferences: object
    applied_at: datetime

POST /api/v1/chat/integrations/slack/sync
  Description: Sync with Slack channel
  Auth: Required
  Request:
    slack_channel_id: string
    sync_direction: "bidirectional" | "to_slack" | "from_slack"
    conversation_id: string (optional)
  Response:
    sync_status: string
    messages_synced: integer

POST /api/v1/chat/conversations/{id}/voice/start
  Description: Start voice chat session
  Auth: Required
  Request:
    audio_format: "webm" | "mp3" | "wav"
    language: string
    enable_diarization: boolean
  Response:
    session_id: string
    websocket_url: string

POST /api/v1/chat/conversations/{id}/export
  Description: Export conversation for compliance
  Auth: Required
  Request:
    format: "pdf" | "json" | "csv" | "html"
    include_metadata: boolean
    redact_pii: boolean
    legal_hold: boolean
  Response:
    export_id: string
    download_url: string
    expires_at: datetime

WS /api/v1/chat/ws/{conversation_id}/intent
  Description: Real-time intent detection
  Auth: Required
  Events:
    - intent_detected
    - suggestion_ready
    - autocomplete_options

POST /api/v1/chat/agent-squad/orchestrate
  Description: Advanced multi-agent orchestration
  Auth: Required
  Request:
    workflow: array[object]
    execution_mode: "sequential" | "parallel" | "conditional"
    fallback_strategy: object
  Response:
    execution_id: string
    results: array
    performance: object
```

---

## 5. Testing Strategy {#testing-strategy}

### 5.1 Test Coverage Requirements

- **Unit Tests**: 90%+ coverage for business logic
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical user workflows
- **Performance Tests**: Load testing for 1000+ concurrent users
- **Security Tests**: OWASP Top 10, prompt injection, XSS

### 5.2 Test Organization

```
tests/
├── unit/
│   ├── chat/
│   │   ├── test_conversation_service.py
│   │   ├── test_message_handler.py
│   │   ├── test_context_manager.py
│   │   ├── test_fork_manager.py
│   │   └── test_search_engine.py
│   ├── agents/
│   │   ├── test_chat_agent.py
│   │   ├── test_risk_analyzer.py
│   │   ├── test_yield_optimizer.py
│   │   ├── test_summary_agent.py
│   │   └── ... (all 18+ agents)
│   └── services/
│       ├── test_analytics_service.py
│       ├── test_translation_service.py
│       └── test_export_service.py
├── integration/
│   ├── chat/
│   │   ├── test_conversation_api.py
│   │   ├── test_message_api.py
│   │   ├── test_fork_api.py
│   │   ├── test_search_api.py
│   │   └── test_websocket_api.py
│   └── agents/
│       └── test_agent_disable_scenarios.py  # NEW
├── e2e/
│   ├── test_conversation_workflows.py
│   ├── test_team_collaboration.py
│   └── test_agent_orchestration.py
├── performance/
│   ├── test_message_throughput.py
│   ├── test_search_performance.py
│   └── test_concurrent_users.py
└── security/
    ├── test_prompt_injection.py
    ├── test_xss_prevention.py
    └── test_pii_redaction.py
```

### 5.3 Agent Disable Test Specification

**File**: `tests/integration/agents/test_agent_disable_scenarios.py`

```python
"""
Test suite for agent enable/disable scenarios.
Validates functionality degradation when each agent is disabled.
"""

import pytest
from fastapi.testclient import TestClient


class TestAgentDisableScenarios:
    """Test impact of disabling each of 18 agents."""

    # Test Matrix: 18 agents × 3 scenarios each = 54 tests

    @pytest.mark.parametrize("agent", [
        "chat",
        "risk_analyzer",
        "yield_optimizer",
        "security_auditor",
        "portfolio_manager",
        "hunter_ai",
        "transaction_executor",
        "compliance_monitor",
        "tax_optimizer",
        "gas_optimizer",
        "research_assistant",
        "multi_sig_coordinator",
        "alert_monitoring",
        "crisis_manager",
        "bridge_cross_chain",
        "lending_borrowing",
        "nft_asset_manager",
        "dao_governance"
    ])
    def test_agent_enabled_vs_disabled(self, agent, client):
        """
        Test same query with agent enabled vs disabled.

        Validates:
        1. Response quality difference
        2. Response time difference
        3. Feature availability difference
        """

        # Test with agent enabled
        response_enabled = client.post(
            "/api/v1/chat/conversations/conv_test/messages",
            json={
                "message": f"Test query requiring {agent}",
                "agent_preferences": {
                    "enable_agents": [agent]
                }
            }
        )

        # Test with agent disabled
        response_disabled = client.post(
            "/api/v1/chat/conversations/conv_test/messages",
            json={
                "message": f"Test query requiring {agent}",
                "agent_preferences": {
                    "disable_agents": [agent]
                }
            }
        )

        # Assertions
        assert response_enabled.status_code == 200
        assert response_disabled.status_code == 200

        # Verify degradation
        assert len(response_enabled.json()["agents_involved"]) > \
               len(response_disabled.json()["agents_involved"])

        # Verify fallback message
        assert "limited functionality" in response_disabled.json()["response"]["content"].lower() or \
               "unavailable" in response_disabled.json()["response"]["content"].lower()


    def test_critical_agent_disabled_error(self, client):
        """Test that disabling critical agents shows appropriate warnings."""

        critical_agents = ["chat", "risk_analyzer", "security_auditor"]

        for agent in critical_agents:
            response = client.post(
                "/api/v1/chat/conversations/conv_test/messages",
                json={
                    "message": "Analyze my portfolio risk",
                    "agent_preferences": {
                        "disable_agents": [agent]
                    }
                }
            )

            # Should include warning about degraded functionality
            assert "warning" in response.json().get("metadata", {})
            assert response.json()["metadata"]["warning"].get("disabled_agent") == agent


    def test_all_agents_enabled_full_functionality(self, client):
        """Baseline test: All agents enabled provides full functionality."""

        response = client.post(
            "/api/v1/chat/conversations/conv_test/messages",
            json={
                "message": "Analyze my Morpho exposure and suggest safer alternatives",
                "agent_preferences": {
                    "enable_all": True
                }
            }
        )

        assert response.status_code == 200

        # Should use multiple agents
        agents_used = response.json()["agents_involved"]
        assert len(agents_used) >= 3

        # Should include risk analysis
        assert any(agent["agent"] == "risk_analyzer" for agent in agents_used)

        # Should include recommendations
        assert any(agent["agent"] == "yield_optimizer" for agent in agents_used)

        # Should include security check
        assert any(agent["agent"] == "security_auditor" for agent in agents_used)
```

---

## 6. Implementation Phases {#implementation-phases}

### Phase 1: Core Chat Features (Weeks 1-2) ✅ COMPLETE
- [x] Use Case 15: Multi-Turn Context
- [x] Use Case 16: Conversation Branching
- [x] Use Case 17: Team Collaboration
- [x] Use Case 18: Advanced Search
- [x] Use Case 19: AI Summarization

### Phase 2: Analytics & Templates (Weeks 3-4) 🔄 IN PROGRESS
- [ ] Use Case 20: Chat Analytics Dashboard
- [ ] Use Case 21: Conversation Templates
- [ ] Use Case 27: Intent Detection
- [ ] Agent Disable Tests (all 18 agents)

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] Use Case 23: Personalization
- [ ] Use Case 26: Export & Compliance
- [ ] Use Case 29: Performance Optimization
- [ ] API Implementation (Phase 2 endpoints)

### Phase 4: Integrations (Weeks 7-8)
- [ ] Use Case 22: Multi-Language
- [ ] Use Case 24: External Integrations (Slack/Discord)
- [ ] Use Case 30: Advanced Agent Orchestration

### Phase 5: Specialized Features (Weeks 9-10)
- [ ] Use Case 25: Voice Chat
- [ ] Use Case 28: Advanced Real-Time Collaboration
- [ ] Performance Testing & Optimization
- [ ] Security Audit

---

## 7. Performance Requirements {#performance-requirements}

### 7.1 Response Time SLAs

| Operation | Target (p50) | Target (p95) | Max (p99) |
|-----------|-------------|--------------|-----------|
| Send Message | < 500ms | < 2s | < 5s |
| Search Conversations | < 200ms | < 800ms | < 2s |
| Generate Summary | < 2s | < 6s | < 10s |
| Create Fork | < 100ms | < 300ms | < 1s |
| WebSocket Message | < 100ms | < 250ms | < 500ms |

### 7.2 Throughput Requirements

- **Messages/second**: 1,000+ sustained
- **Concurrent Users**: 10,000+
- **Concurrent Conversations**: 5,000+
- **Search Queries/second**: 500+
- **WebSocket Connections**: 10,000+

### 7.3 Scalability

- Horizontal scaling (add more API servers)
- Redis cluster for caching and WebSocket state
- PostgreSQL read replicas for search
- Celery workers for async tasks
- CDN for static assets and responses

---

## 8. Security & Compliance {#security-compliance}

### 8.1 Security Features

- **Authentication**: JWT with refresh tokens
- **Authorization**: RBAC with per-conversation permissions
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **PII Redaction**: Automatic detection and redaction
- **Prompt Injection**: Guard against malicious prompts
- **XSS Prevention**: Content sanitization
- **Rate Limiting**: Per-user and per-IP limits
- **Audit Logging**: All actions logged immutably

### 8.2 Compliance

- **GDPR**: Right to erasure, data portability, consent management
- **CCPA**: California privacy rights
- **SOC 2**: Type II certification
- **HIPAA**: Healthcare data protection (optional)
- **FinCEN**: Financial compliance for DeFi operations

---

## 9. Next Steps

1. ✅ **Complete Documentation** (Use Cases 20-30)
2. ⏳ **Implement Agent Disable Tests** (54 test scenarios)
3. ⏳ **Create API Implementation** (Phase 2-5 endpoints)
4. ⏳ **Performance Testing** (Load tests for 10k users)
5. ⏳ **Security Audit** (Penetration testing)

---

## Appendix A: Agent Disable Use Case Template

### Use Case: Portfolio Risk Analysis with Risk Analyzer Agent

#### Scenario
User asks: "What's the risk of my current Morpho positions?"

#### With Risk Analyzer Enabled ✅

**Response Time**: 2.3 seconds

**Response**:
```
**Morpho Risk Analysis Complete** 🔍

**Current Exposure**: $2.1M across 3 vaults (37% of total portfolio)

**Risk Breakdown by Vault**:
1. Flagship ETH: $1.2M (Risk: 6.8/10) ⚠️
   - TVL dropped 8% (48hrs): $890M → $819M
   - Large withdrawals detected

2. Re7 WETH: $600k (Risk: 7.2/10) 🔴
   - Risk score INCREASED from 6.5 to 7.2
   - Utilization at 88% (high)

3. Steakhouse USDC: $300k (Risk: 5.1/10) ✅
   - Stable, no concerns

**Overall Portfolio Risk**: 7.1/10 (exceeds 7.5 threshold)

**Recommended Actions**:
1. Reduce Re7 WETH position by 40% ($240k)
2. Monitor Flagship ETH for further TVL drops
3. Consider reallocation to Aave v3 (risk: 5.8/10)
```

**Agents Involved**: Risk Analyzer (primary), Security Auditor (supporting)

**Data Sources**: Morpho API, DeFiLlama, Internal portfolio DB

**Confidence**: 91%

#### With Risk Analyzer Disabled ❌

**Response Time**: 0.8 seconds (faster but less useful)

**Response**:
```
I can see you have positions in Morpho Finance, but I cannot provide
detailed risk analysis without the Risk Analyzer agent enabled.

**Your Morpho Positions**:
- Flagship ETH: $1.2M
- Re7 WETH: $600k
- Steakhouse USDC: $300k
- Total: $2.1M (37% of portfolio)

**Limited Information Available**:
- Current TVL data from public APIs
- Basic position sizes
- Protocol names

**To get full risk analysis, please**:
1. Enable the Risk Analyzer agent in settings
2. Manually research each vault at morpho.org
3. Check DeFiLlama for TVL trends
4. Review audit reports for security assessment

Would you like me to help with anything else?
```

**Agents Involved**: Chat Agent only

**Data Sources**: Basic portfolio DB only

**Confidence**: N/A (no analysis performed)

#### Impact Comparison

| Metric | Enabled | Disabled | Difference |
|--------|---------|----------|------------|
| Response Time | 2.3s | 0.8s | -1.5s (but no value) |
| Data Points | 15+ | 3 | -80% |
| Actionable Recommendations | 3 | 0 | -100% |
| Risk Scores | 4 detailed | 0 | -100% |
| Time to Manual Research | 0 min | 25-40 min | +25-40 min |
| Decision Confidence | 91% | <20% | -71% |

#### Business Impact

**With Agent Enabled**:
- ✅ Immediate risk visibility
- ✅ Data-driven decision making
- ✅ Proactive risk management
- ✅ Save 25-40 minutes of manual research
- ✅ Higher confidence decisions (91% vs <20%)

**With Agent Disabled**:
- ❌ No risk scores (manual calculation needed)
- ❌ No trend analysis
- ❌ No recommendations
- ⚠️ User must visit 5+ external sites
- ⚠️ User must interpret raw data themselves
- ⚠️ 25-40 minutes lost per query
- ⚠️ Lower decision quality

**ROI Calculation**:
- Portfolio Manager salary: $150k/year = $75/hour
- Time saved per query: 30 minutes = $37.50
- Queries per week: 10
- **Weekly value: $375**
- **Monthly value: $1,625**
- **Annual value: $19,500**

**Risk Reduction Value**:
- Better decisions prevent losses
- Estimated value: $50k-200k/year (0.5-2% of $10M portfolio)

---

*End of Master Specification Document*
