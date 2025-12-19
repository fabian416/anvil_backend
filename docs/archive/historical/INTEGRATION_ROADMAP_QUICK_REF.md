# Integration Roadmap - Quick Reference

**Total Duration:** 9-10 weeks  
**Excluding:** Privy integration (handled by separate developer)

---

## 📅 Timeline Overview

```
Phase 1: Core Agent Infrastructure (Weeks 1-3)
├─ Week 1: Agent Squad (Manager/Router)
├─ Week 2: Agno Runtime (Agent Workers)
└─ Week 3: Chat Feature Real Implementation

Phase 2: DeFi Operations & Blockchain (Weeks 4-6)
├─ Week 4: DeFi Data Providers (1inch, DefiLlama, The Graph)
├─ Week 5: Blockchain Infrastructure (Web3, RPC Providers)
└─ Week 6: DeFi Protocol SDKs (Hyperliquid, Aave)

Phase 3: Real-time & Polish (Weeks 7-9)
├─ Week 7: Real-time Communication (WebSocket/SSE)
├─ Week 8: Comprehensive Testing
└─ Week 9: Polish & Documentation

Week 10: Buffer & Launch Preparation
```

---

## 🎯 Weekly Goals

### **Week 1: Agent Squad Integration** ✨ CRITICAL
**Goal:** Get agent orchestration working

**Deliverables:**
- ✅ Agent Squad configured and initialized
- ✅ DeFi intent classifier (11 intents)
- ✅ SQLAlchemy storage adapter
- ✅ AgentGatewayImpl functional
- ✅ Unit tests passing

**Files to Create/Modify:**
- `src/app/setup/config/agent_squad.py` (NEW)
- `src/app/infrastructure/adapters/ai/agent_gateway_impl.py` (UNCOMMENT)
- `src/app/infrastructure/adapters/ai/squad_storage.py` (ENHANCE)
- `src/app/infrastructure/agents/classifiers.py` (NEW)
- `tests/unit/infrastructure/adapters/ai/test_agent_gateway_impl.py` (NEW)

**Success Metric:** Agent Squad routes a test message without errors

---

### **Week 2: Agno Runtime** ✨ CRITICAL
**Goal:** Get specialized agents working with tools

**Deliverables:**
- ✅ AnvilAgent base class functional (uncomment Agno)
- ✅ TradingAgent with HyperliquidTools
- ✅ RiskAgent with risk analysis tools
- ✅ LendingAgent with Aave tools
- ✅ All agents registered with Agent Squad

**Files to Create/Modify:**
- `src/app/infrastructure/agents/base.py` (UNCOMMENT)
- `src/app/infrastructure/agents/trading_agent.py` (IMPLEMENT)
- `src/app/infrastructure/agents/risk_agent.py` (IMPLEMENT)
- `src/app/infrastructure/agents/lending_agent.py` (NEW)
- `src/app/infrastructure/agents/tools/hyperliquid.py` (EXPAND)
- `src/app/infrastructure/agents/tools/risk_analysis.py` (NEW)
- `src/app/infrastructure/agents/tools/aave.py` (NEW)

**Success Metric:** User message → Intent classified → Agent responds with tool output

---

### **Week 3: Chat Feature Complete** ✨ CRITICAL
**Goal:** Replace all mocks with real implementations

**Deliverables:**
- ✅ CreateConversation interactor complete
- ✅ SendMessage interactor complete
- ✅ GetConversation query
- ✅ ListConversations query
- ✅ Chat router using real interactors
- ✅ Celery task processing agent messages
- ✅ End-to-end test passing

**Files to Modify:**
- `src/app/application/commands/chat/create_conversation.py` (COMPLETE)
- `src/app/application/commands/chat/send_message.py` (COMPLETE)
- `src/app/application/queries/chat/get_conversation.py` (NEW)
- `src/app/application/queries/chat/list_conversations.py` (NEW)
- `src/app/presentation/http/controllers/chat/router.py` (REPLACE MOCKS)
- `src/app/infrastructure/celery/tasks.py` (ENHANCE process_agent_response)

**Success Metric:** POST message → Celery processes → Agent responds → GET returns message

---

### **Week 4: DeFi Data Providers** 🔥 HIGH PRIORITY
**Goal:** Get real DeFi market data

**Deliverables:**
- ✅ 1inch adapter (swap quotes)
- ✅ DefiLlama adapter (yields, TVL)
- ✅ The Graph adapter (on-chain queries)
- ✅ All adapters with error handling
- ✅ Unit tests for each adapter

**Files to Create:**
- `src/app/domain/ports/defi/dex_aggregator.py` (NEW)
- `src/app/domain/ports/defi/protocol_analytics.py` (NEW)
- `src/app/infrastructure/adapters/defi/oneinch_adapter.py` (NEW)
- `src/app/infrastructure/adapters/defi/defillama_adapter.py` (NEW)
- `src/app/infrastructure/adapters/defi/thegraph_adapter.py` (NEW)

**Success Metric:** Agent can fetch real swap quote from 1inch

---

### **Week 5: Blockchain Infrastructure** 🔥 HIGH PRIORITY
**Goal:** Connect to blockchain networks

**Deliverables:**
- ✅ Infura/Alchemy RPC configuration
- ✅ Web3.py integration (all chains)
- ✅ Get wallet balances (native + ERC20)
- ✅ Query transactions
- ✅ Estimate gas fees
- ✅ Automatic failover between providers

**Files to Create:**
- `src/app/setup/config/blockchain.py` (NEW)
- `src/app/domain/ports/blockchain/web3_provider.py` (NEW)
- `src/app/infrastructure/adapters/blockchain/web3_adapter.py` (NEW)

**Success Metric:** Query wallet balance on Ethereum, Arbitrum, Polygon, Base

---

### **Week 6: DeFi Protocol SDKs** 🔥 HIGH PRIORITY
**Goal:** Integrate with Hyperliquid and Aave

**Deliverables:**
- ✅ Complete Hyperliquid SDK integration
- ✅ Query open positions
- ✅ Get funding rates
- ✅ Create unsigned order payloads
- ✅ Complete Aave V3 integration
- ✅ Query user health factor
- ✅ Get supply/borrow APYs
- ✅ Create unsigned transaction payloads

**Files to Enhance:**
- `src/app/infrastructure/agents/tools/hyperliquid.py` (EXPAND)
- `src/app/infrastructure/agents/tools/aave.py` (CREATE)

**Success Metric:** Agent queries real Hyperliquid position and Aave health factor

---

### **Week 7: Real-time Communication** 🟡 MEDIUM PRIORITY
**Goal:** Add WebSocket for live updates

**Deliverables:**
- ✅ WebSocket endpoint
- ✅ Connection management
- ✅ Broadcast agent responses
- ✅ SSE fallback
- ✅ Reconnection logic

**Files to Create:**
- `src/app/presentation/http/controllers/websocket/router.py` (NEW)

**Success Metric:** Agent response appears in chat instantly via WebSocket

---

### **Week 8: Comprehensive Testing** 🟢 ESSENTIAL
**Goal:** Ensure quality and stability

**Deliverables:**
- ✅ Unit tests (>80% coverage)
- ✅ Integration tests (all flows)
- ✅ Performance tests (1000+ users)
- ✅ Load testing results

**Focus Areas:**
- Agent processing under load
- Database query performance
- API response times
- Error handling

---

### **Week 9: Polish & Documentation** 🟢 ESSENTIAL
**Goal:** Production readiness

**Deliverables:**
- ✅ Error handling comprehensive
- ✅ API documentation complete
- ✅ Integration guides written
- ✅ Security audit passed
- ✅ Deployment guide ready

---

### **Week 10: Buffer & Launch Prep** 🔵 BUFFER
**Purpose:** Handle unexpected issues

**Allocation:**
- 3 days: Address gaps from Weeks 1-9
- 2 days: Final polish and launch preparation

---

## 🚨 Critical Path

**These must complete on time (no delays allowed):**

1. **Week 1:** Agent Squad ← Blocks everything
2. **Week 2:** Agno Runtime ← Blocks agent functionality
3. **Week 3:** Chat Feature ← Blocks MVP
4. **Week 4:** DeFi Data ← Blocks real data
5. **Week 5:** Blockchain ← Blocks wallet operations

**Weeks 6-9 have some flexibility but should stay on track**

---

## 📊 Progress Tracking

### Phase 1 Checklist (Weeks 1-3)
- [ ] Agent Squad integrated and tested
- [ ] 3+ specialized agents working (Trading, Risk, Lending)
- [ ] Chat endpoints returning real data
- [ ] Celery processing messages
- [ ] End-to-end test: User → Agent → Response

### Phase 2 Checklist (Weeks 4-6)
- [ ] 1inch providing swap quotes
- [ ] DefiLlama providing yield data
- [ ] Web3.py querying all 4 chains
- [ ] Hyperliquid SDK operational
- [ ] Aave SDK operational

### Phase 3 Checklist (Weeks 7-9)
- [ ] WebSocket delivering real-time updates
- [ ] Test coverage >80%
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Security audit passed

---

## 🔗 Dependencies

### Agent Squad (Week 1)
- **Blocks:** Agno (Week 2), Chat Feature (Week 3)
- **Requires:** None
- **Risk:** HIGH (new library integration)

### Agno Runtime (Week 2)
- **Blocks:** Chat Feature (Week 3)
- **Requires:** Agent Squad (Week 1)
- **Risk:** HIGH (new library integration)

### Chat Feature (Week 3)
- **Blocks:** Nothing (but critical for MVP)
- **Requires:** Agent Squad (Week 1), Agno (Week 2)
- **Risk:** MEDIUM (implementation complexity)

### DeFi Data Providers (Week 4)
- **Blocks:** Nothing (parallel with agents)
- **Requires:** None
- **Risk:** LOW (standard API integrations)

### Blockchain Infrastructure (Week 5)
- **Blocks:** DeFi Protocol SDKs (Week 6)
- **Requires:** None (can parallel with Week 4)
- **Risk:** MEDIUM (RPC reliability)

### DeFi Protocol SDKs (Week 6)
- **Blocks:** Nothing
- **Requires:** Blockchain Infrastructure (Week 5)
- **Risk:** MEDIUM (SDK integration)

### Real-time Communication (Week 7)
- **Blocks:** Nothing
- **Requires:** Chat Feature (Week 3)
- **Risk:** LOW (standard WebSocket)

---

## 🤝 Coordination Points with Privy Developer

### Week 1-2: Authentication Contract
- **Your Action:** Implement `get_current_user_id()` helper
- **Privy Action:** Provide JWT validation middleware
- **Deliverable:** Shared authentication interface

### Week 3: Dual Auth System
- **Your Action:** Support both admin JWT and Privy JWT in chat endpoints
- **Privy Action:** Provide user authentication flow
- **Deliverable:** Chat works for both admin and mobile users

### Week 5: Wallet Integration
- **Your Action:** Blockchain adapter ready to query addresses
- **Privy Action:** Provide MPC wallet addresses
- **Deliverable:** Agents can query user wallet balances

### Week 7: End-to-End Testing
- **Your Action:** Chat + agents + DeFi operations
- **Privy Action:** Mobile auth flow
- **Deliverable:** Joint testing session

---

## 📈 Success Metrics

### Technical Metrics
- **Agent Response Time:** < 5 seconds (p95)
- **API Response Time:** < 200ms (p95)
- **Test Coverage:** > 80%
- **Uptime:** 99.9% availability

### Functional Metrics
- **Intents Classified:** 11 types working
- **Agents Operational:** 3+ specialized agents
- **Chains Supported:** 4 (Ethereum, Arbitrum, Polygon, Base)
- **DeFi Protocols:** 2+ integrated (Hyperliquid, Aave)

### Load Metrics
- **Concurrent Users:** 1000+ supported
- **Messages/Second:** 100+ processed
- **WebSocket Connections:** 1000+ simultaneous

---

## 🆘 Escalation Plan

### If Week 1 (Agent Squad) Fails
**Fallback:** Direct LLM calls with keyword-based routing
- **Impact:** Less intelligent routing
- **Timeline:** Saves 3-4 days
- **Decision Point:** End of Day 3

### If Week 2 (Agno) Fails
**Fallback:** Simple function-based tools without Agno framework
- **Impact:** Less sophisticated agent capabilities
- **Timeline:** Saves 2-3 days
- **Decision Point:** End of Day 3

### If Week 5 (Blockchain) Fails
**Fallback:** Mock blockchain data for MVP, real integration post-launch
- **Impact:** Can't show real wallet balances
- **Timeline:** Saves 5 days
- **Decision Point:** End of Day 2

---

## 📝 Daily Checklist Template

**Morning:**
- [ ] Review today's tasks from integration plan
- [ ] Check for blockers from yesterday
- [ ] Sync with Privy developer if needed

**During Work:**
- [ ] Follow implementation steps from plan
- [ ] Write tests as you go (TDD)
- [ ] Document any deviations from plan

**End of Day:**
- [ ] Update progress (checkboxes in plan)
- [ ] Commit code with clear messages
- [ ] Note any blockers for tomorrow
- [ ] Update this quick reference if timeline shifts

---

## 🎯 Week-by-Week Focus

| Week | Focus | Risk | Priority |
|------|-------|------|----------|
| 1 | Agent Squad | HIGH | CRITICAL |
| 2 | Agno Runtime | HIGH | CRITICAL |
| 3 | Chat Feature | MED | CRITICAL |
| 4 | DeFi Data | LOW | HIGH |
| 5 | Blockchain | MED | HIGH |
| 6 | Protocol SDKs | MED | HIGH |
| 7 | Real-time | LOW | MEDIUM |
| 8 | Testing | LOW | ESSENTIAL |
| 9 | Polish | LOW | ESSENTIAL |
| 10 | Buffer | - | BUFFER |

---

## 📞 Quick Links

**Full Integration Plan:** [INTEGRATION_PLAN.md](./INTEGRATION_PLAN.md)  
**Implementation Status:** [IMPLEMENTATION_STATUS_ANALYSIS.md](./IMPLEMENTATION_STATUS_ANALYSIS.md)  
**MVP Requirements:** [../anvil_mvp_requirements_v2.md](../anvil_mvp_requirements_v2.md)  
**Chat Spec:** [../specs/chat_feature_full_spec.md](../specs/chat_feature_full_spec.md)

---

**Last Updated:** December 1, 2025  
**Status:** Active  
**Next Review:** End of Week 3
