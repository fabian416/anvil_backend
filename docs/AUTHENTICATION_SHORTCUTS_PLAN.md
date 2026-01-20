# Authentication Shortcuts Fix Plan

## Overview
This plan addresses authentication requirements for all restricted shortcuts that require user sign-in. Following the CTO methodology framework and the same pattern used for the PORTFOLIO fix.

## Methodology (From cto.md)

### Phase 1: Problem Decomposition & Root Cause Analysis

**Assumption Questioning:**
- What is the actual requirement? → Guest users should see sign-in messages for restricted features
- What unverified assumptions? → All shortcuts are being handled correctly
- Which constraints might be pseudo-constraints? → None - authentication is a hard requirement

**Root Cause Identification:**
- Restricted intents are being routed to Agent Squad Supervisor
- Supervisor coordinator is calling restricted agents for guest users
- Agents are not checking authentication status before execution
- System prompts don't explicitly handle authentication requirements

**Solution Space Mapping:**
- System invariant: Guest users cannot access wallet data
- Design degrees of freedom: How to detect and handle restricted intents
- Hard constraints: Authentication required for wallet operations
- Soft constraints: User experience (clear messaging)

### Phase 2: Solution Generation & Trade-off Analysis

**Solution Options:**

1. **Solution A: Intent Detection Before Agent Squad** (Current approach)
   - Technical Benefits: Early detection, prevents unnecessary agent calls
   - Implementation Cost: Medium (update intent detection)
   - Risk: Low (already partially implemented)

2. **Solution B: Agent-Level Authentication Checks** (Alternative)
   - Technical Benefits: Defense in depth, agent-specific handling
   - Implementation Cost: High (update all agents)
   - Risk: Medium (may miss some agents)

3. **Solution C: Supervisor Coordinator Detection** (Chosen)
   - Technical Benefits: Centralized, consistent, prevents agent calls
   - Implementation Cost: Low (update prompts only)
   - Risk: Low (follows existing pattern)

**Chosen Solution: C** - Update supervisor coordinator and CHAT agent prompts

### Phase 3: Risk Assessment & Validation Design

**Cognitive Limitation Analysis:**
- May overlook: Edge cases where queries match multiple intents
- Assumes: LLM correctly identifies restricted intents
- Requires validation: Test all restricted shortcuts

**Technical Debt Assessment:**
- Rapid implementation: Prompt-based detection (may need refinement)
- Long-term: Consider adding explicit authentication checks in agents

**Validation Strategy:**
- Test each restricted shortcut with guest user
- Verify correct sign-in message appears
- Verify restricted agents are NOT called
- Verify only CHAT agent executes

## Restricted Intents (Require Authentication)

Based on `RESTRICTED_INTENTS` in `send_guest_message.py`:

1. ✅ **PORTFOLIO** - Fixed
2. ⚠️ **BALANCE** - Needs fix
3. ⚠️ **ACTIVITY** - Needs fix
4. ⚠️ **RECEIVE** - Needs fix
5. ⚠️ **BUY** - Needs fix
6. ⚠️ **SEND** - Needs fix

## Implementation Plan

### Phase 1: Analysis & Testing ✅
- [x] Identify all restricted intents
- [x] Map shortcuts to intents
- [x] Test current behavior
- [x] Document issues

### Phase 2: Code Updates ✅
- [x] Update supervisor coordinator planning prompt
- [x] Update CHAT agent system prompt
- [x] Remove PORTFOLIO from GUEST_ACCESSIBLE_AGENTS
- [ ] Test all shortcuts

### Phase 3: Verification ⚠️
- [ ] Test BALANCE shortcut
- [ ] Test ACTIVITY shortcut
- [ ] Test RECEIVE shortcut
- [ ] Test BUY shortcut
- [ ] Test SEND shortcut
- [ ] Verify all show correct sign-in messages
- [ ] Verify no restricted agents called

## Detailed Fixes

### 1. BALANCE Intent
- **Shortcut**: "Balance", "What's my balance?", "Check my balance"
- **Keywords**: "my balance", "what's my balance", "check my balance", "how much do I have", "wallet balance"
- **Message**: "To view your wallet balance, please sign in or create an account. Balance features require authentication to access your wallet data."
- **Status**: ⚠️ Needs testing

### 2. ACTIVITY Intent
- **Shortcut**: "Activity", "Show my transactions", "Transaction history"
- **Keywords**: "my transactions", "transaction history", "show my activity", "recent activity", "my activity"
- **Message**: "To view your transaction history, please sign in or create an account. Activity features require authentication to access your wallet data."
- **Status**: ⚠️ Needs testing

### 3. RECEIVE Intent
- **Shortcut**: "Receive", "My address", "Wallet address"
- **Keywords**: "my address", "wallet address", "receive crypto", "deposit address", "QR code", "I want to receive"
- **Message**: "To get your wallet address or QR code, please sign in or create an account. Wallet address features require authentication to access your wallet data."
- **Status**: ⚠️ Needs testing

### 4. BUY Intent
- **Shortcut**: "Buy", "Buy crypto", "Purchase Bitcoin"
- **Keywords**: "buy crypto", "purchase bitcoin", "buy with card", "how to buy ETH", "I want to buy", "buy with fiat"
- **Message**: "To buy crypto with fiat, please sign in or create an account. Buy features require authentication to access payment methods."
- **Status**: ⚠️ Needs testing

### 5. SEND Intent
- **Shortcut**: "Send", "Send crypto", "Transfer tokens"
- **Keywords**: "send crypto", "transfer tokens", "send to wallet", "send to friend", "I want to send", "transfer crypto"
- **Message**: "To send crypto or transfer tokens, please sign in or create an account. Send features require authentication to access your wallet for transactions."
- **Status**: ⚠️ Needs testing

## Files Modified

1. ✅ `src/app/domain/services/agent_squad/supervisor_coordinator.py`
   - Added detection rules for all restricted intents in `_build_planning_prompt()`
   - Priority order: BALANCE → ACTIVITY → RECEIVE → BUY → SEND → PORTFOLIO

2. ✅ `src/app/infrastructure/adapters/agent_squad/agents/chat_agent_openai.py`
   - Added authentication requirement handling for all restricted intents

3. ✅ `src/app/application/guest/commands/send_guest_message.py`
   - Removed PORTFOLIO from GUEST_ACCESSIBLE_AGENTS

## Testing Checklist

For each restricted shortcut:
- [ ] Test with guest user
- [ ] Verify correct sign-in message appears (intent-specific)
- [ ] Verify restricted agent is NOT called
- [ ] Verify only CHAT agent executes
- [ ] Verify response is clear and actionable

## Success Criteria

- ✅ All restricted shortcuts show sign-in requirement
- ✅ No restricted agents called for guest users
- ✅ Clear, consistent, intent-specific sign-in messages
- ✅ Shortcuts endpoint still works (public)
- ✅ Authenticated users can still use shortcuts

## Next Steps

1. Test all 5 remaining shortcuts
2. Verify fixes work correctly
3. Refine detection if messages are incorrect
4. Document final results
