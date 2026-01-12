# Authenticated Chat Test Enhancement Plan

**Objective**: Expand authenticated chat integration tests from 22 to 50+ comprehensive test cases covering all intents, multi-step flows, and production quality checks.

**Target File**: `tests/integration/chat/test_authenticated_chat_comprehensive.py`

---

## Current Coverage (22 Tests)

### ✅ Existing Test Classes
1. **TestAuthenticatedChatEndpoint** (2 tests)
   - Endpoint requires authentication
   - Authenticated users can send messages

2. **TestAuthenticatedMultiStepFlows** (2 tests)
   - Lending flow
   - Swap flow

3. **TestAuthenticatedVsGuestBehavior** (3 tests)
   - No signup prompts
   - Real data (not demo)
   - Higher rate limits

4. **TestAuthenticatedIntents** (4 tests)
   - Balance, Portfolio, Activity, Receive

5. **TestAuthenticatedMultiLanguage** (3 tests)
   - Spanish, Portuguese, Chinese

6. **TestAuthenticatedDatabasePersistence** (2 tests)
   - Conversations with user_id
   - Messages stored

7. **TestAuthenticatedErrorHandling** (3 tests)
   - Empty messages, Invalid language, Nonexistent conversation

8. **Comprehensive Validation** (3 tests)
   - No demo data, No signup prompts, Real wallet

---

## Additional Coverage Needed (30+ Tests)

### 1. Hunter AI Intents (6 tests) ⭐ NEW
**Class**: `TestAuthenticatedHunterAI`

| Test | Description | Example Query |
|------|-------------|---------------|
| test_sentiment_analysis | Hunter AI sentiment for BTC/ETH/SOL | "What's the sentiment for BTC?" |
| test_price_prediction | Price forecasts with confidence | "Predict ETH price" |
| test_risk_signals | Market risk warnings | "Risk signals for SOL" |
| test_trading_signals | Buy/sell entry points | "Should I buy BTC?" |
| test_pattern_recognition | Chart patterns & TA | "Chart patterns for ETH" |
| test_portfolio_optimization | MPT-based portfolio allocation | "Optimize my portfolio" |

**Key Validations**:
- Hunter AI enrichment present
- Real data (not fake sentiment scores)
- Proper intent routing to `hunter_ai` handler
- No demo disclaimers

---

### 2. ULTRA Intents (4 tests) ⭐ NEW
**Class**: `TestAuthenticatedULTRA`

| Test | Description | Example Query |
|------|-------------|---------------|
| test_arbitrage_discovery | Cross-DEX arbitrage opportunities | "Find arbitrage opportunities" |
| test_flash_loans | Flash loan protocol selection | "Best flash loan for USDC" |
| test_mev_protection | MEV-protected execution | "Execute with Flashbots" |
| test_auto_executor | Trading bot control | "Start trading bot" |

**Key Validations**:
- ULTRA enrichment with opportunity data
- Real protocols and rates
- Executable action data present
- Proper routing to `ultra` handler

---

### 3. GraphRAG Intents (3 tests) ⭐ NEW
**Class**: `TestAuthenticatedGraphRAG`

| Test | Description | Example Query |
|------|-------------|---------------|
| test_protocol_search | Find protocols by criteria | "Find low-risk staking protocols" |
| test_risk_assessment | Protocol safety analysis | "Is Aave safe?" |
| test_similar_protocols | Alternative recommendations | "Protocols like Uniswap" |

**Key Validations**:
- GraphRAG enrichment with protocol data
- Real protocol names and risk scores
- Routing to `graphrag_search` handler

---

### 4. Agent Squad Orchestration (2 tests) ⭐ NEW
**Class**: `TestAuthenticatedAgentSquad`

| Test | Description | Example Query |
|------|-------------|---------------|
| test_specialist_task | Route to specialist agent | "Best USDC yield strategy" |
| test_complex_workflow | Multi-agent coordination | "Create balanced portfolio strategy" |

**Key Validations**:
- Routing to `agent_orchestrator` handler
- Suggested agent specified (defi_yield, portfolio, etc.)
- Complex task breakdown

---

### 5. DeFi Shortcuts (8 tests) ⭐ NEW
**Class**: `TestAuthenticatedDeFiShortcuts`

| Test | Description | Example Query |
|------|-------------|---------------|
| test_lending_shortcut | Direct lending deposit | "Deposit USDC on Morpho" |
| test_money_market_shortcut | Rate comparison | "Compare lending rates" |
| test_swap_shortcut | DEX swap (non-major tokens) | "Swap DAI to LINK" |
| test_moonpay_swap_shortcut | Major token swap | "Swap BTC to ETH" |
| test_balance_shortcut | Wallet balance check | "What's my balance?" |
| test_portfolio_shortcut | Portfolio overview | "Show my portfolio" |
| test_activity_shortcut | Transaction history | "Show my activity" |
| test_receive_shortcut | Receive funds | "Show my wallet address" |

**Key Validations**:
- Correct intent routing
- No signup prompts (authenticated)
- Real wallet data shown
- Proper handler selection

---

### 6. Multi-Step Flow Validation (15 tests) ⭐ NEW
**Class**: `TestAuthenticatedMultiStepFlowsComplete`

#### LENDING Flow (5 tests)
| Step | Test | Validation |
|------|------|------------|
| 1 | test_lending_step1_asset_selection | Ask for asset, show supported assets |
| 2 | test_lending_step2_amount_input | Ask for amount after asset selected |
| 3 | test_lending_step3_vault_display | Show best vaults with APY |
| 4 | test_lending_step4_confirmation | Ask for confirmation with details |
| 5 | test_lending_step5_execution | Return executable action data |

#### SWAP Flow (4 tests)
| Step | Test | Validation |
|------|------|------------|
| 1 | test_swap_step1_from_token | Ask for source token |
| 2 | test_swap_step2_to_token | Ask for destination token |
| 3 | test_swap_step3_amount | Ask for swap amount |
| 4 | test_swap_step4_confirmation | Show quote and ask confirmation |

#### SWAP_MOONPAY Flow (3 tests)
| Step | Test | Validation |
|------|------|------------|
| 1 | test_moonpay_step1_pair_selection | BTC↔ETH, ETH↔SOL, etc. |
| 2 | test_moonpay_step2_amount | Ask for amount to swap |
| 3 | test_moonpay_step3_confirmation | Show quote and fees |

#### BUY Flow (3 tests)
| Step | Test | Validation |
|------|------|------------|
| 1 | test_buy_step1_asset | Ask which crypto to buy |
| 2 | test_buy_step2_amount | Ask how much (fiat amount) |
| 3 | test_buy_step3_payment_method | Credit card, bank, Apple Pay |

---

### 7. Production Quality Checks (5 tests) ⭐ NEW
**Class**: `TestAuthenticatedProductionQuality`

| Test | Description | Validation |
|------|-------------|------------|
| test_response_formatting | Professional formatting | Markdown, bullet points, clear structure |
| test_emoji_usage | Visual appeal | Appropriate emojis for context |
| test_clear_ctas | Actionable next steps | "Confirm", "Cancel", "Edit" options |
| test_error_handling_graceful | Graceful degradation | Helpful error messages, not crashes |
| test_edge_cases | Unusual inputs | Handles typos, ambiguous queries |

---

### 8. Authenticated-Specific Validations (3 tests) ⭐ NEW
**Class**: `TestAuthenticatedSpecificBehavior`

| Test | Description | Validation |
|------|-------------|------------|
| test_no_rate_limit_banners | No guest warnings | Never shows "You have X messages left" |
| test_persistent_conversations | Conversation history | Can reference previous messages |
| test_wallet_integration | Real wallet access | Shows real balance, not placeholders |

---

## Summary: Test Count Breakdown

| Category | Tests | Status |
|----------|-------|--------|
| **Existing Tests** | 22 | ✅ Created |
| **Hunter AI** | 6 | 🔨 To Add |
| **ULTRA** | 4 | 🔨 To Add |
| **GraphRAG** | 3 | 🔨 To Add |
| **Agent Squad** | 2 | 🔨 To Add |
| **DeFi Shortcuts** | 8 | 🔨 To Add |
| **Multi-Step Flows** | 15 | 🔨 To Add |
| **Production Quality** | 5 | 🔨 To Add |
| **Auth-Specific** | 3 | 🔨 To Add |
| **TOTAL** | **68 Tests** | 🎯 Target: 50+ |

---

## Implementation Strategy

### Phase 1: Core Intent Coverage (13 tests)
1. Hunter AI intents (6)
2. ULTRA intents (4)
3. GraphRAG intents (3)

**Priority**: HIGH - Validates all major AI capabilities

---

### Phase 2: Multi-Step Flow Validation (15 tests)
1. LENDING flow (5 steps)
2. SWAP flow (4 steps)
3. SWAP_MOONPAY flow (3 steps)
4. BUY flow (3 steps)

**Priority**: HIGH - Core user journeys

---

### Phase 3: Shortcuts & Quality (16 tests)
1. DeFi shortcuts (8)
2. Production quality (5)
3. Auth-specific behavior (3)

**Priority**: MEDIUM - Polish and edge cases

---

## Expected Outcomes

### Test Results
- **50+ comprehensive tests** covering all authenticated chat capabilities
- **Flexible assertions** for AI response variations
- **Database validation** for all persistent data
- **Multi-step flow validation** with state management

### Identified Fixes Needed
After running the enhanced test suite, we expect to find:

1. **Endpoint Integration Issues**
   - chat_users (UUID) foreign key constraints
   - Authentication middleware validation
   - Rate limit configuration

2. **Intent Routing Gaps**
   - Missing handler implementations
   - Incorrect intent-to-handler mappings
   - LLM classification issues

3. **Multi-Step State Management**
   - Context carryover between requests
   - Flow reset logic
   - Step validation

4. **Data Integration**
   - Real wallet data fetching
   - Hunter AI data sources
   - ULTRA protocol integration

5. **Response Quality**
   - Formatting consistency
   - Error message clarity
   - CTA effectiveness

---

## Success Criteria

✅ **68 total tests** (50+ target achieved)
✅ **All intents covered** (Hunter, ULTRA, GraphRAG, Squad, DeFi)
✅ **Complete flow validation** (LENDING, SWAP, BUY, MOONPAY)
✅ **Production-ready quality** (formatting, errors, CTAs)
✅ **Authenticated behavior validated** (no signup, real data, high limits)

---

## Next Steps

1. ✅ Create this enhancement plan
2. 🔨 Implement Phase 1 (Core Intent Coverage)
3. 🔨 Implement Phase 2 (Multi-Step Flows)
4. 🔨 Implement Phase 3 (Shortcuts & Quality)
5. 🧪 Run full test suite
6. 📋 Document fixes needed
7. 🔧 Implement fixes
8. ✅ Verify all 68 tests passing
