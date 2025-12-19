# UC-AGENTS: Agent System

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 9

---

## 📊 **OVERVIEW**

Multi-agent orchestration system powered by Agent Squad framework, enabling coordinated AI agents for research, trading, and risk analysis.

### **Business Value**
- AI-powered agent interactions
- Multi-agent orchestration
- Agent memory and context
- Agent routing
- Performance tracking

### **Technical Stack**
- **Framework:** Agent Squad (AWS SDK for multi-agent systems)
- **LLM Providers:** OpenAI (GPT-4), AWS Bedrock
- **Agent Types:** Research, Trading, Risk, Portfolio
- **Storage:** Database-backed agent sessions
- **Context:** Conversation history with memory

---

## 🎯 **USE CASES**

### **UC-AGENT-1: Multi-Agent Orchestration**
- **Status:** ✅ LIVE
- **Implementation:** `AgentSquad` from `agent_squad.orchestrator`
- **Capabilities:** Coordinate multiple agents, route queries, manage context

### **UC-AGENT-2: Research Agent**
- **Status:** ✅ LIVE
- **Agent Type:** `ResearchAgent`
- **Capabilities:** DeFi research, protocol analysis, market intelligence

### **UC-AGENT-3: Trading Agent**
- **Status:** ✅ LIVE (Basic)
- **Agent Type:** `TradingAgent`
- **Capabilities:** Basic trading signals, market analysis

### **UC-AGENT-4: Risk Agent**
- **Status:** ✅ LIVE (Basic)
- **Agent Type:** `RiskAgent`
- **Capabilities:** Basic risk assessment, portfolio risk

### **UC-AGENT-5: DeFi Analysis**
- **Status:** ✅ LIVE
- **Capabilities:** Protocol research, yield opportunities, market trends

### **UC-AGENT-6: Agent Context Management**
- **Status:** ✅ LIVE
- **Storage:** `AgentContext` database table
- **Capabilities:** Persist conversation history, maintain context

### **UC-AGENT-7: Agent Memory**
- **Status:** ✅ LIVE
- **Implementation:** Session-based memory
- **Capabilities:** Short-term memory across conversation

### **UC-AGENT-8: Agent Routing**
- **Status:** ✅ LIVE
- **Interactor:** `RouteToAgent`
- **Capabilities:** Intelligent agent selection based on query

### **UC-AGENT-9: Agent Performance Tracking**
- **Status:** ✅ LIVE
- **Metrics:** Response time, success rate, user satisfaction
- **Storage:** Metrics collection via `UserMetricsRepository`

---

## 🏗️ **ARCHITECTURE**

```
Domain Layer:
  ├─ entities/
  │  ├─ agent.py
  │  ├─ agent_session.py
  │  └─ conversation.py
  └─ value_objects/
     └─ agent_type.py (Enum)

Application Layer:
  ├─ commands/
  │  ├─ create_conversation.py
  │  ├─ send_message.py
  │  └─ route_to_agent.py
  └─ services/
     └─ agent_orchestrator.py

Infrastructure Layer:
  └─ adapters/ai/
     └─ agent_squad_gateway.py

Presentation Layer:
  └─ controllers/chat/
     └─ router.py
```

---

## 📚 **RELATED DOCUMENTATION**

- [Agent Squad Integration](../../LIBS_IMPLEMENTATION_DETAILS.md#agent-squad)
- [AgentSquadGateway](../../../src/app/infrastructure/adapters/ai/agent_squad_gateway.py)
- [Agent Domain](../../../src/app/domain/entities/agent.py)

---

**Status:** ✅ 100% Complete (9/9 use cases live)  
**Last Updated:** December 2, 2025
