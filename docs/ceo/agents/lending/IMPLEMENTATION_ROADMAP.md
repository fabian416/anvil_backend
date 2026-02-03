# Lending Workflow Implementation Roadmap - Revised Based on Gap Analysis

> **Status:** Gap Analysis Complete - Ready for Implementation
> **Methodology:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis
> **Agents:** @backend-engineer + @prompt-engineer + @code-review-waltz + @context-manager
> **Date:** 2026-01-27
> **Original Estimate:** 7 weeks | **Revised Estimate:** 4-5 weeks (30% reduction due to existing code)

---

## Executive Summary

### Gap Analysis Results

**Total Specifications Analyzed:** 11 documents (8,732 lines)
**Gap Analysis Documents Created:** 4 comprehensive assessments (110K total)

**Implementation Status:**
- ✅ **60% Complete** - Core infrastructure exists (MCP servers, domain entities, handlers)
- ⚠️ **40% Critical Gaps** - Balance validation, real execution, database, agents

**Key Finding:** The existing codebase has solid foundations that can be extended rather than rebuilt from scratch, reducing implementation time from 7 weeks to 4-5 weeks.

---

## 🎯 Critical Discoveries

### ✅ What Already Exists (Excellent Foundation)

1. **Domain Entities (100% Complete)**
   - ✅ `AavePosition` - Complete with all fields
   - ✅ `MorphoPosition` - Complete with vault tracking
   - ✅ `MorphoVault` - Complete with APY data
   - ✅ `HealthFactor` - Value object with validation
   - ✅ All entity relationships properly mapped

2. **MCP Server Integration (95% Complete)**
   - ✅ Aave MCP: All 9 tools implemented (port 8085)
   - ✅ Morpho MCP: All 6 tools implemented (port 8088)
   - ⚠️ **Issue:** Aave tools return mock data (not real blockchain calls)

3. **Lending Handler (70% Complete)**
   - ✅ `LendingHandler` exists with Morpho integration
   - ✅ Multi-language support (en, es, pt, zh)
   - ✅ User context awareness (guest vs authenticated)
   - ✅ Correct `execute_data` generation pattern (follows SwapHandlerV2)
   - ❌ **Missing:** Aave integration (Morpho-only)
   - ❌ **Missing:** Balance validation before execution

4. **User Approval Flow (80% Complete)**
   - ✅ Two-step approval pattern (simulate → confirm → sign)
   - ✅ Privy integration correctly implemented
   - ✅ NO batch processing (verified safe)
   - ✅ Transaction preview before approval
   - ❌ **Missing:** Health factor validation before borrow
   - ❌ **Missing:** Leverage loop multi-step approval

5. **Context Management (60% Complete)**
   - ✅ `UserContextService` exists with good architecture
   - ✅ `UserContextAware` entity with portfolio state
   - ✅ Redis-backed state storage (24h TTL)
   - ❌ **Missing:** Risk profile calculation
   - ❌ **Missing:** Per-token balance tracking
   - ❌ **Missing:** Health factor in context

### 🔴 Critical Gaps Requiring Immediate Action

1. **Balance Validation (P0 - CRITICAL)**
   - **Issue:** Can generate execute_data for transactions user can't afford
   - **Impact:** Poor UX, user confusion, failed transactions
   - **Fix Required:** `BalanceChecker` adapter before execute_data generation
   - **Timeline:** 2-3 days

2. **Aave Real Execution (P0 - CRITICAL)**
   - **Issue:** All Aave MCP tools return mock data
   - **Impact:** Aave integration non-functional
   - **Fix Required:** Replace mocks with real Web3 calls
   - **Timeline:** 3-5 days

3. **Health Factor Validation (P0 - CRITICAL)**
   - **Issue:** Users could approve unsafe borrows (immediate liquidation risk)
   - **Impact:** User funds at risk, reputation damage
   - **Fix Required:** `HealthFactorValidator` before borrow approval
   - **Timeline:** 2-3 days

4. **Database Tables (P1 - HIGH)**
   - **Issue:** All 8 specified lending tables missing
   - **Impact:** No position tracking, no transaction history
   - **Fix Required:** Alembic migrations for all tables
   - **Timeline:** 3-4 days

5. **Agent Prompts (P1 - HIGH)**
   - **Issue:** 4 specialized agents not configured
   - **Impact:** Suboptimal responses, no cross-protocol optimization
   - **Fix Required:** Configure Market Scanner, Risk Guardian, Executor, Optimizer
   - **Timeline:** 2-3 days

6. **Shortcuts (P1 - HIGH)**
   - **Issue:** 6 lending shortcuts missing from shortcuts.json
   - **Impact:** Poor discoverability, reduced engagement
   - **Fix Required:** Add LENDING_HEALTH_CHECK, LENDING_SUPPLY, etc.
   - **Timeline:** 1-2 days

---

## 📊 Comprehensive Gap Matrix

### Component Status Overview

| Component | Specified | Current Status | Gap | Priority | Effort |
|-----------|-----------|----------------|-----|----------|--------|
| **Domain Layer** |
| LendingPosition entity | ✅ | ✅ Complete | None | - | 0 days |
| HealthFactor value object | ✅ | ✅ Complete | None | - | 0 days |
| CollateralAsset value object | ✅ | ✅ Complete | None | - | 0 days |
| LendingService | ✅ | ❌ Missing | Need implementation | P1 | 2 days |
| **Application Layer** |
| SupplyCommand/Interactor | ✅ | ❌ Missing | Need CQRS pattern | P0 | 3 days |
| BorrowCommand/Interactor | ✅ | ❌ Missing | Need CQRS pattern | P1 | 3 days |
| LeverageLoopCommand | ✅ | ❌ Missing | Need multi-step state | P2 | 4 days |
| HealthCheckQuery | ✅ | ⚠️ Partial | Need optimization | P1 | 1 day |
| **Infrastructure Layer** |
| AaveMcpAdapter | ✅ | ⚠️ Mock data | **Remove mocks** | **P0** | **4 days** |
| MorphoMcpAdapter | ✅ | ✅ Complete | None | - | 0 days |
| BalanceChecker adapter | ✅ | ❌ Missing | **Critical for UX** | **P0** | **2 days** |
| HealthFactorValidator | ✅ | ❌ Missing | **Critical for safety** | **P0** | **2 days** |
| TransactionMonitor | ✅ | ❌ Missing | Need Celery task | P1 | 2 days |
| **Presentation Layer** |
| Unified LendingHandler | ✅ | ⚠️ Morpho-only | Add Aave support | P0 | 3 days |
| Shortcuts (6) | ✅ | ❌ Missing | Add to shortcuts.json | P1 | 1 day |
| **Database** |
| lending_positions table | ✅ | ❌ Missing | Alembic migration | P1 | 1 day |
| lending_supplies table | ✅ | ❌ Missing | Alembic migration | P1 | 1 day |
| lending_borrows table | ✅ | ❌ Missing | Alembic migration | P1 | 1 day |
| lending_transactions table | ✅ | ❌ Missing | Alembic migration | P1 | 1 day |
| user_lending_preferences | ✅ | ❌ Missing | Alembic migration | P2 | 1 day |
| lending_health_checks | ✅ | ❌ Missing | Alembic migration | P2 | 1 day |
| leverage_loop_executions | ✅ | ❌ Missing | Alembic migration | P2 | 1 day |
| lending_alerts table | ✅ | ❌ Missing | Alembic migration | P2 | 1 day |
| **Agent Configuration** |
| Market Scanner Agent | ✅ | ❌ Missing | Create agent config | P1 | 1 day |
| Risk Guardian Agent | ✅ | ❌ Missing | Create agent config | P1 | 1 day |
| Executor Agent (tuned) | ✅ | ⚠️ Exists | Tune temp to 0.1 | P1 | 0.5 days |
| Optimizer Agent | ✅ | ❌ Missing | Create agent config | P1 | 1 day |
| **Knowledge Base** |
| Protocol comparison | ✅ | ❌ Missing | Add to knowledge base | P1 | 0.5 days |
| Risk classification | ✅ | ❌ Missing | Add to knowledge base | P1 | 0.5 days |
| Health factor guide | ✅ | ❌ Missing | Add to knowledge base | P1 | 0.5 days |
| Multi-language terms | ✅ | ⚠️ Partial | Add lending terms | P1 | 0.5 days |

**Total Effort:**
- P0 (Critical): 11 days
- P1 (High): 17 days
- P2 (Medium): 7 days
- **Overall: ~35 days = 5 weeks** (with parallel work: **4 weeks**)

---

## 🚀 Revised Implementation Plan (4-5 Weeks)

### Week 1: Critical Safety & Infrastructure (P0 Items)

**Goal:** Make lending transactions safe and functional

#### Days 1-2: Balance Validation
- [ ] **Task 1.1:** Create `IBalanceChecker` port in domain layer
  - Location: `src/app/domain/ports/balance_checker.py`
  - Interface: `async def check_balance(wallet: str, token: str, amount: Decimal) -> bool`

- [ ] **Task 1.2:** Implement `Web3BalanceChecker` adapter
  - Location: `src/app/infrastructure/adapters/web3/balance_checker.py`
  - Use Portfolio MCP or direct Web3 calls
  - Support ERC20 and native tokens

- [ ] **Task 1.3:** Integrate balance validation into `LendingHandler`
  - Check balance BEFORE generating execute_data
  - Return clear error: "Insufficient balance. You have X, need Y"

#### Days 3-5: Remove Aave Mocks
- [ ] **Task 1.4:** Replace mock responses in `aave_mcp.py`
  - Tools: get_market_data, get_user_positions, calculate_health_factor
  - Use real Aave V3 subgraph queries
  - Add error handling for RPC failures

- [ ] **Task 1.5:** Implement real transaction execution
  - Tools: supply_asset, borrow_asset, repay_loan, withdraw_supply
  - Generate real calldata for Aave V3 Pool contract
  - Test on testnet first

- [ ] **Task 1.6:** Add Aave support to `LendingHandler`
  - Extend handler to choose Aave OR Morpho based on user request
  - Cross-protocol comparison logic

#### Days 6-7: Health Factor Validation
- [ ] **Task 1.7:** Create `HealthFactorValidator` service
  - Location: `src/app/application/lending/services/health_factor_validator.py`
  - Method: `validate_borrow(collateral, debt, new_borrow) -> ValidationResult`
  - Block borrows that would result in HF < 1.2

- [ ] **Task 1.8:** Integrate into borrow workflow
  - Check HF BEFORE showing approval UI
  - Show clear warning: "⚠️ UNSAFE - Health Factor would be 1.15 (minimum recommended: 1.5)"

**Week 1 Deliverables:**
- ✅ All transactions require sufficient balance
- ✅ Aave MCP executes real transactions
- ✅ Unsafe borrows are blocked with clear messaging
- ✅ Both Morpho and Aave supported

---

### Week 2: Commands, Queries & Database (P1 Items - Part 1)

**Goal:** Implement CQRS pattern and persistent storage

#### Days 8-10: CQRS Implementation
- [ ] **Task 2.1:** Create `SupplyCommand` and `SupplyInteractor`
  - Location: `src/app/application/lending/commands/supply.py`
  - Input: wallet, protocol, asset, amount
  - Output: execute_data with transaction calldata
  - Validation: balance check, protocol availability

- [ ] **Task 2.2:** Create `BorrowCommand` and `BorrowInteractor`
  - Location: `src/app/application/lending/commands/borrow.py`
  - Input: wallet, protocol, asset, amount, collateral
  - Output: execute_data with health factor validation
  - Validation: collateral sufficiency, HF safety

- [ ] **Task 2.3:** Create `HealthCheckQuery` and `HealthCheckQueryHandler`
  - Location: `src/app/application/lending/queries/health_check.py`
  - Optimized for read-only health factor queries
  - Return: current positions, HF, liquidation threshold

#### Days 11-14: Database Schema
- [ ] **Task 2.4:** Create Alembic migration for core tables
  - Tables: lending_positions, lending_supplies, lending_borrows, lending_transactions
  - Foreign keys to users, wallets tables
  - Indexes for performance (user_id, protocol, status)

- [ ] **Task 2.5:** Create SQLAlchemy mappings
  - Location: `src/app/infrastructure/persistence_sqla/mappings/lending.py`
  - Explicit mappings for all 4 core tables
  - Relationship configurations

- [ ] **Task 2.6:** Implement repository adapters
  - `LendingPositionRepository` - CRUD for positions
  - `LendingTransactionRepository` - Track tx history
  - Follow port-adapter pattern

- [ ] **Task 2.7:** Integrate repositories with handlers
  - Save position after successful deposit
  - Update position after borrow/repay
  - Track transaction status

**Week 2 Deliverables:**
- ✅ CQRS commands for supply and borrow
- ✅ 4 core database tables operational
- ✅ Position tracking across transactions
- ✅ Transaction history persisted

---

### Week 3: Agent Configuration & Knowledge Base (P1 Items - Part 2)

**Goal:** Optimize agent responses and add lending shortcuts

#### Days 15-16: Agent Prompts
- [ ] **Task 3.1:** Create Market Scanner Agent
  - Location: `anvil_knowledge/agents/market_scanner_agent.json`
  - Temperature: 0.3
  - Tools: aave_get_market_data, morpho_get_vaults, morpho_compare_yields
  - Prompt: Include 2-3 few-shot examples for rate queries

- [ ] **Task 3.2:** Create Risk Guardian Agent
  - Location: `anvil_knowledge/agents/risk_guardian_agent.json`
  - Temperature: 0.2 (safety-critical)
  - Tools: aave_calculate_health_factor, aave_get_liquidation_risk
  - Prompt: Embed health factor classification rules

- [ ] **Task 3.3:** Tune Executor Agent
  - Update temperature to 0.1 (precision)
  - Add explicit user approval language
  - Include health factor validation checks

- [ ] **Task 3.4:** Create Optimizer Agent
  - Location: `anvil_knowledge/agents/optimizer_agent.json`
  - Temperature: 0.4 (creative optimization)
  - Tools: morpho_compare_yields, aave_get_available_to_borrow
  - Prompt: Include yield farming, loop protocol strategies

#### Days 17-18: Knowledge Base Updates
- [ ] **Task 3.5:** Add protocol comparison knowledge
  - File: `anvil_knowledge/features/lending_protocols.json`
  - Content: Aave vs Morpho characteristics, when to use each
  - Multi-language support

- [ ] **Task 3.6:** Add risk classification knowledge
  - File: `anvil_knowledge/features/lending_risks.json`
  - Content: LTV levels, health factor interpretation, safety thresholds
  - Color-coded risk levels

- [ ] **Task 3.7:** Add lending terminology
  - Update: `anvil_knowledge/features/glossary.json`
  - Terms: Supply, collateral, health factor, liquidation
  - Languages: en, es, pt, zh

#### Days 19-21: Shortcuts Configuration
- [ ] **Task 3.8:** Add 6 lending shortcuts to shortcuts.json
  - LENDING_HEALTH_CHECK: "Check my lending position"
  - LENDING_SUPPLY: "Supply ETH to earn yield"
  - LENDING_BORROW: "Borrow USDC"
  - LENDING_LOOP: "Loop ETH for leverage"
  - LENDING_COMPARE: "What's the best yield?"
  - LENDING_POSITION: "Show my lending positions"

- [ ] **Task 3.9:** Configure agent routing for shortcuts
  - Health check → Risk Guardian Agent
  - Supply → Market Scanner → Executor
  - Borrow → Risk Guardian → Executor
  - Loop → Optimizer → Risk Guardian → Executor (3 steps)
  - Compare → Market Scanner
  - Position → Risk Guardian

- [ ] **Task 3.10:** Add multi-language support for shortcuts
  - Spanish: "Suministrar ETH", "Pedir prestado USDC"
  - Portuguese: "Fornecer ETH", "Pedir emprestado USDC"
  - Chinese: "供应 ETH", "借用 USDC"

**Week 3 Deliverables:**
- ✅ 4 lending agents configured with optimized prompts
- ✅ Knowledge base updated with lending content
- ✅ 6 lending shortcuts operational
- ✅ Multi-language support for all shortcuts

---

### Week 4: Advanced Features & Testing (P2 Items)

**Goal:** Implement advanced features and comprehensive testing

#### Days 22-24: Leverage Loop Implementation
- [ ] **Task 4.1:** Create `LeverageLoopCommand`
  - Multi-step state machine: SUPPLY → BORROW → SWAP → REPEAT
  - Each step generates ONE execute_data (3 separate user approvals)
  - State persistence in Redis

- [ ] **Task 4.2:** Implement leverage loop workflow
  - Step 1: Supply collateral (user approval #1)
  - Step 2: Borrow same asset (user approval #2)
  - Step 3: Swap to collateral (user approval #3)
  - Repeat until target leverage reached

- [ ] **Task 4.3:** Add health factor monitoring
  - Check HF after each step
  - Stop loop if HF drops below 1.5
  - Clear error messaging

#### Days 25-26: Additional Database Tables
- [ ] **Task 4.4:** Create remaining tables
  - user_lending_preferences (risk_tolerance, auto_repay_threshold)
  - lending_health_checks (monitoring history)
  - leverage_loop_executions (multi-step tracking)
  - lending_alerts (user notifications)

- [ ] **Task 4.5:** Create database views
  - user_lending_summary (aggregated positions)
  - protocol_comparison (APY comparison)

#### Days 27-28: Comprehensive Testing
- [ ] **Task 4.6:** Unit tests (90% domain coverage)
  - Test: HealthFactor value object validation
  - Test: LendingService business logic
  - Test: Command validators

- [ ] **Task 4.7:** Integration tests (70% adapter coverage)
  - Test: AaveMcpAdapter real execution
  - Test: MorphoMcpAdapter vault discovery
  - Test: BalanceChecker with various tokens

- [ ] **Task 4.8:** E2E tests (lending flows)
  - Test: Supply flow (guest blocked, authenticated succeeds)
  - Test: Borrow flow (HF validation, insufficient collateral)
  - Test: Leverage loop (3-step approval process)
  - Test: Health check query

**Week 4 Deliverables:**
- ✅ Leverage loop operational (3 separate approvals)
- ✅ All 8 database tables complete
- ✅ 90% domain test coverage
- ✅ E2E tests for all core flows

---

### Week 5 (Optional): Polish & Documentation

**Goal:** Production readiness and documentation

#### Days 29-30: Documentation
- [ ] **Task 5.1:** Update API documentation
  - Document lending endpoints
  - Add request/response examples
  - Update OpenAPI schema

- [ ] **Task 5.2:** Create user guides
  - How to supply assets
  - How to borrow safely
  - Understanding health factor
  - Leverage loop tutorial

#### Days 31-32: Performance Optimization
- [ ] **Task 5.3:** Add Redis caching
  - Market data: 60s TTL
  - User positions: 30s TTL
  - Health factors: 10s TTL (safety-critical)

- [ ] **Task 5.4:** Database query optimization
  - Add indexes for frequent queries
  - Optimize joins for position summaries
  - Add partitioning for large tables

#### Days 33-35: Production Deployment
- [ ] **Task 5.5:** Staging deployment
  - Deploy to testnet
  - Run smoke tests
  - Monitor error rates

- [ ] **Task 5.6:** Production deployment
  - Gradual rollout (10% → 50% → 100%)
  - Monitor health factor calculations
  - Track transaction success rates

**Week 5 Deliverables:**
- ✅ Complete documentation
- ✅ Performance optimizations
- ✅ Production deployment

---

## 📋 Critical User Approval Requirements

### NO BATCH PROCESSING RULE

**✅ VERIFIED:** The codebase has NO automatic batch processing. Every transaction requires explicit user approval.

### User Approval Flow for Each Transaction Type

#### 1. Supply (Deposit) Transaction
```
User: "deposit 1000 USDC to Morpho"
  ↓
Backend: Check balance (1000 USDC available?)
  ↓ YES
Backend: Fetch Morpho vault data (APY, safety)
  ↓
Backend → User: "📊 Preview:
  - Vault: Steakhouse USDC
  - Amount: 1,000 USDC
  - APY: 12.5%
  - Your balance after: 4,500 USDC

  Confirm deposit?"
  ↓
User: "yes"
  ↓
Backend → Frontend: [execute_data with ERC-4626 deposit calldata]
  ↓
Frontend: Opens Privy modal
  ↓
User: Signs transaction (or cancels)
  ↓ SIGNED
Transaction submitted to blockchain
  ↓
Backend: Save to lending_supplies table
Backend: Update lending_positions table
```

#### 2. Borrow Transaction (with Health Factor Validation)
```
User: "borrow 2000 USDC"
  ↓
Backend: Check collateral (user has X ETH supplied)
  ↓
Backend: Calculate health factor impact
  - Current HF: 2.5
  - After borrow HF: 1.45
  ↓
Backend: Validate safety (HF >= 1.2?)
  ↓ SAFE
Backend → User: "📊 Preview:
  - Borrow: 2,000 USDC
  - Collateral: 1.5 ETH ($5,000)
  - Health Factor: 2.5 → 1.45 ✅ SAFE
  - Liquidation at: $3,333/ETH (current: $3,700)

  Confirm borrow?"
  ↓
User: "yes"
  ↓
Backend → Frontend: [execute_data with Aave borrow calldata]
  ↓
Frontend: Privy signature modal
  ↓
User: Signs (or cancels)
  ↓ SIGNED
Transaction submitted
  ↓
Backend: Save to lending_borrows table
Backend: Update lending_positions table
Backend: Create lending_health_checks entry
```

#### 3. Leverage Loop (3 SEPARATE Approvals - NO Batch)
```
User: "loop ETH for 3x leverage"
  ↓
Backend: Calculate steps needed (supply → borrow → swap, repeat 2x)
  ↓
Backend: Save workflow state in Redis
  ↓
Backend → User: "📊 Leverage Loop Preview:
  - Starting: 1 ETH
  - Target: 3x leverage
  - Steps: 3 separate transactions
  - Final position: ~3 ETH collateral
  - Health Factor: ~1.42

  ⚠️ You will need to sign 3 separate transactions.

  Start leverage loop?"
  ↓
User: "yes"
  ↓
Backend: Generate STEP 1 execute_data (supply 1 ETH)
  ↓
Backend → User: "Step 1/3: Supply 1 ETH as collateral"
  ↓
User: Signs with Privy
  ↓ STEP 1 COMPLETE
Backend: Wait for confirmation, update state
  ↓
Backend: Generate STEP 2 execute_data (borrow 0.75 ETH)
  ↓
Backend → User: "Step 2/3: Borrow 0.75 ETH"
  ↓
User: Signs with Privy
  ↓ STEP 2 COMPLETE
Backend: Wait for confirmation
  ↓
Backend: Generate STEP 3 execute_data (swap to ETH, supply again)
  ↓
Backend → User: "Step 3/3: Swap and re-supply"
  ↓
User: Signs with Privy
  ↓ STEP 3 COMPLETE
Backend: Save to leverage_loop_executions table
Backend: Update final position
  ↓
Backend → User: "✅ Leverage loop complete!
  - Final collateral: 3.2 ETH
  - Total debt: 2.2 ETH
  - Health Factor: 1.45
  - Effective leverage: 3.2x"
```

### Key User Approval Principles

1. **NEVER automatic execution** - Every transaction requires user signature
2. **Clear preview BEFORE approval** - Show amounts, APY, health factor impact
3. **Balance validation FIRST** - Don't show approval UI if insufficient balance
4. **Health factor validation** - Block unsafe borrows with clear warning
5. **Multi-step transparency** - For leverage loops, show "Step 1/3" progress
6. **Cancellation support** - User can cancel at any step
7. **Timeout handling** - Pending approvals expire after 5 minutes

---

## 🎯 Success Criteria

### Technical Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Balance validation | 100% of transactions | No execute_data generated for insufficient balance |
| Health factor validation | 100% of borrows | No approvals for HF < 1.2 |
| Aave real execution | 100% of Aave calls | No mock responses in production |
| Test coverage (domain) | >90% | Pytest coverage report |
| Test coverage (integration) | >70% | Pytest coverage report |
| E2E test success | 100% pass rate | All lending flows tested |
| Database persistence | 100% of transactions | All positions tracked in DB |
| Agent response quality | >4.5/5.0 user rating | User feedback |

### User Experience Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Insufficient balance prevention | 100% | Error before approval UI |
| Unsafe borrow prevention | 100% | Block HF < 1.2 with warning |
| Guest user block | 100% | Educational response only |
| Multi-language support | 4 languages | en, es, pt, zh tested |
| Shortcut discovery | >50% via shortcuts | Track usage analytics |
| Leverage loop clarity | 3 clear approval steps | User can track "Step 2/3" |

### Security Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| No batch processing | 0 instances | Code audit verified |
| User signature required | 100% of transactions | Every execute_data needs Privy |
| Authorization checks | 100% of endpoints | Test unauthorized access |
| Rate limiting | 10 queries/min per user | Load testing |
| Input sanitization | 100% of inputs | Security testing |

---

## 🚨 Critical Path Items (Cannot Proceed Without)

### Week 1 Blockers (P0 - CRITICAL)

1. **BalanceChecker Implementation**
   - **Blocks:** All transaction approvals
   - **Risk:** Users see approval UI for transactions they can't afford
   - **Owner:** Backend Engineer
   - **Dependencies:** Portfolio MCP or Web3 adapter

2. **Remove Aave Mocks**
   - **Blocks:** Aave integration
   - **Risk:** Aave feature appears to work but doesn't execute
   - **Owner:** Backend Engineer
   - **Dependencies:** Aave V3 subgraph access, testnet setup

3. **HealthFactorValidator**
   - **Blocks:** Borrow feature
   - **Risk:** Users could get liquidated immediately after borrowing
   - **Owner:** Backend Engineer + Domain Expert
   - **Dependencies:** Accurate price oracle data

### Week 2 Dependencies

- Week 1 completion (balance validation must work before DB persistence)
- Database migration approval
- Repository pattern established

### Week 3 Dependencies

- Agent configuration format finalized
- Knowledge base schema defined
- Shortcuts endpoint structure confirmed

---

## 📊 Effort Distribution by Priority

```
Total Effort: ~35 days of work
With parallel work: 4-5 weeks calendar time

P0 (Critical - Week 1):     11 days (31%)
P1 (High - Weeks 2-3):      17 days (49%)
P2 (Medium - Week 4):        7 days (20%)

Breakdown by Component:
- Backend Infrastructure:   40% (14 days)
- Database & Persistence:   20% (7 days)
- Agent Configuration:      20% (7 days)
- Testing & QA:            15% (5 days)
- Documentation:            5% (2 days)
```

---

## 🔄 Continuous Monitoring

### Daily Standups (15 min)

**Check:**
- [ ] Any P0 blockers?
- [ ] Test coverage still >90% domain?
- [ ] Any new security concerns?
- [ ] User approval flow still working?

### Weekly Reviews (1 hour)

**Review:**
- [ ] Progress vs timeline
- [ ] Quality metrics (test coverage, code review)
- [ ] User feedback from staging
- [ ] Adjust priorities if needed

### Key Metrics Dashboard

Track in real-time:
- Balance validation rate (target: 100%)
- Health factor validation rate (target: 100%)
- Transaction success rate (target: >95%)
- Average approval time (target: <30s)
- Error rate (target: <0.1%)

---

## 📚 References

**Gap Analysis Documents:**
- [GAP_ANALYSIS.md](./GAP_ANALYSIS.md) - Backend implementation gaps
- [AGENT_PROMPTS_GAP.md](./AGENT_PROMPTS_GAP.md) - Agent configuration gaps
- [USER_APPROVAL_GAP.md](./USER_APPROVAL_GAP.md) - User approval flow gaps
- [CONTEXT_MANAGEMENT_GAP.md](./CONTEXT_MANAGEMENT_GAP.md) - Context management gaps

**Original Specifications:**
- [architecture.md](./architecture.md) - Hexagonal architecture design
- [implementation_plan.md](./implementation_plan.md) - Original 7-week plan
- [database_schema.md](./database_schema.md) - Complete database schema
- [agent_prompts.md](./agent_prompts.md) - Agent prompt specifications

**Related Documentation:**
- SWAP_SYSTEM_SPEC.md - Similar multi-step approval pattern
- CHAT_ARCHITECTURE.md - Agent coordination patterns
- deployment-dockerization-spec.md - Infrastructure requirements

---

## ✅ Next Actions

### Immediate (This Week)

1. **Development Team Review** (1-2 days)
   - Review all 4 gap analysis documents
   - Clarify any ambiguities
   - Get sign-off on revised timeline

2. **Sprint Planning** (1 day)
   - Break down Week 1 tasks into tickets
   - Assign owners for P0 items
   - Set up development environment

3. **Begin Week 1 Implementation** (5 days)
   - Start with BalanceChecker (Days 1-2)
   - Remove Aave mocks (Days 3-5)
   - Implement HealthFactorValidator (Days 6-7)

### Week 2 Planning

- Review Week 1 deliverables
- Adjust Week 2 plan if needed
- Begin CQRS implementation
- Start database migrations

---

**Document Status:** ✅ Complete - Ready for Team Review
**Next Review Date:** After Week 1 completion
**Owner:** Development Team Lead
**Last Updated:** 2026-01-27

---

**For questions or updates, consult the gap analysis documents or contact the development team lead.**
