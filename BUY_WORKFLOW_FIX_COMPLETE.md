# Buy Crypto Workflow Fix - Complete Implementation

**Date**: 2026-01-27
**Root Cause**: conversations_router.py was using legacy BuyHandler instead of BuyWorkflowAgent for authenticated users
**Solution**: Hybrid Approach (Solution C) - BuyWorkflowAgent for authenticated users, BuyHandler for guests

---

## Problem Summary

### Bug Description

When authenticated users try to buy crypto, the workflow loops back instead of showing the execute button with payment provider integration (Privy).

**Example Flow (BROKEN)**:
```
Step 1: User → "Buy crypto"
        Agent → Shows available cryptos (ETH, USDC, USDT, BTC)

Step 2: User → "USDC"
        Agent → "How much would you like to spend?"

Step 3: User → "100"
        Agent → "Which cryptocurrency would you like to buy?" ❌ LOOPS BACK
        Expected: Show execute button with Privy modal
```

### Root Cause Analysis

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py` (lines 1351-1464)

**Issue 1: Wrong Handler Used**
- Router was using legacy `BuyHandler` for ALL authenticated users
- `BuyWorkflowAgent` (AGNO-based) was fully implemented but never called
- This created an architectural mismatch

**Issue 2: State Persistence Bug in BuyHandler**
```python
# Line 1410 - READS from wrong field
if context.pending_buy_info:
    previous_buy_info = BuyInfo.from_dict(context.pending_buy_info)

# Line 1660 (in metadata write) - WRITES to different field
metadata["buy_info"] = buy_info
```

The handler writes to `metadata["buy_info"]` but reads from `context.pending_buy_info`, causing state loss between turns.

---

## Solution Implemented: Hybrid Approach (Solution C)

### Overview

- ✅ **Authenticated users**: Use `BuyWorkflowAgent` (AGNO-based, proper workflow)
- ✅ **Guest users**: Keep `BuyHandler` (informational flow only)
- ✅ **Backward compatible**: No breaking changes to guest chat
- ✅ **Execute data**: Properly extracted from workflow metadata

### Why This Solution?

**Alternative Solutions Rejected**:
- **Solution A** (Quick fix state persistence): Perpetuates legacy code, technical debt
- **Solution B** (Full migration to BuyWorkflowAgent): Higher risk, more testing needed for guests

**Solution C Benefits**:
1. Proper architecture for authenticated users (AGNO-based workflows)
2. Backward compatibility for guests
3. Lower implementation risk
4. Matches pattern used by swap_workflow and lending_workflow
5. Proper execute_data generation for Privy integration

---

## Implementation Details

### Code Changes

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Lines Changed**: 1351-1464 (114 lines replaced)

### Before (Legacy BuyHandler)

```python
elif intent_result.intent.value.startswith("BUY"):
    from app.application.chat.handlers.buy_handler import BuyHandler, BuyInfo

    if user.is_guest:
        # Guest informative flow
        ...
    else:
        # ❌ WRONG: Using BuyHandler for authenticated users
        buy_handler = BuyHandler(...)

        # State persistence bug
        previous_buy_info = None
        if context.pending_buy_info:  # ❌ Wrong field
            previous_buy_info = BuyInfo.from_dict(context.pending_buy_info)

        # Metadata writes to different field
        metadata["buy_info"] = buy_info  # ❌ Wrong field
```

### After (BuyWorkflowAgent for Authenticated)

```python
elif intent_result.intent.value.startswith("BUY"):
    if user.is_guest:
        # Keep legacy informative handler for guests
        from app.application.chat.services.intent_detector import ChatIntent
        handler_result = await handler_service.handle_intent(...)
    else:
        # ✅ Use BuyWorkflowAgent for authenticated users
        from app.infrastructure.adapters.agent_squad.agents.workflows.buy_workflow_agent import BuyWorkflowAgent
        from app.domain.value_objects.message_content import MessageContent
        from app.domain.value_objects.agent_squad.conversation_context import ConversationContext

        # Build conversation history
        conversation_history = []
        if context.messages:
            recent_messages = context.messages[:10]
            for msg in reversed(recent_messages):
                msg_dict = {
                    "role": msg.role.value,
                    "content": msg.content,
                }
                if hasattr(msg, 'metadata') and msg.metadata:
                    msg_dict["metadata"] = msg.metadata
                conversation_history.append(msg_dict)

        # Build user metadata
        user_metadata = {
            "user_id": int(user.identifier),
            "wallet_address": wallet_address,
            "language": request_body.language,
            "is_authenticated": True,
        }

        # Create conversation context
        conversation_context = ConversationContext(
            conversation_history=conversation_history,
            user_metadata=user_metadata,
        )

        # Execute BuyWorkflowAgent
        buy_workflow = BuyWorkflowAgent(llm_client=llm_gateway)
        agent_response = await buy_workflow.execute(
            conversation_id=conversation_id,
            message=MessageContent(request_body.content),
            conversation_context=conversation_context,
        )

        agent_content = agent_response.content

        # ✅ Extract execute_data from workflow metadata
        if agent_response.metadata and agent_response.metadata.get("execute_data"):
            execute_data = ExecuteActionData(**agent_response.metadata["execute_data"])

        enrichment = {
            "workflow_agent": "buy_workflow",
            "tools_used": agent_response.tools_used,
        }

        # No pending_action - workflows handle state internally
        pending_action = None
```

---

## BuyWorkflowAgent Architecture

### Workflow Steps

**File**: `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`

**Inherits from**: `BaseWorkflowAgent` (AGNO-based pattern)

**Steps**:
1. **PARSE_REQUEST**: Extract crypto, amount, and fiat currency from user message
2. **FETCH_DATA** (Validate): Check supported assets and networks
3. **CONFIRM**: Show purchase details and wait for confirmation
4. **EXECUTE**: Generate execute_data for Privy on-ramp modal

### Execute Data Format

```python
execute_data = {
    "action_type": "fund_wallet",
    "provider": "privy",
    "amount": "100",
    "fiat": "USD",
    "crypto": "USDC",
    "chain": "base",
}
```

### Supported Cryptocurrencies

- **ETH** (Ethereum) - Ξ
- **USDC** (USD Coin) - 💵
- **USDT** (Tether) - 💵
- **BTC** (Bitcoin) - ₿
- **SOL** (Solana) - ◎
- **MATIC** (Polygon) - 🟣

### Supported Fiat Currencies

- USD, EUR, GBP, CAD, AUD

### Supported Networks

- Base, Ethereum, Polygon, Arbitrum

---

## Expected Flow (FIXED)

### Complete Workflow

```
Step 1: User → "Buy crypto"
        Agent → Shows available cryptos (ETH, USDC, USDT, BTC)
        State: step=parse_request

Step 2: User → "USDC"
        Agent → "How much would you like to spend?"
        State: step=parse_request, data.crypto=USDC

Step 3: User → "100"
        Agent → Shows confirmation quote with APY/details
        State: step=confirm, data={crypto: USDC, amount: 100, fiat: USD}

Step 4: User → "yes" or "confirm"
        Agent → "✅ Opening purchase flow..." + execute button
        State: step=execute, execute_data={...}
        Frontend: Privy modal opens for payment
```

### All-in-One Input

```
User → "buy 100 dollars of ETH"
Agent → Shows confirmation quote
       "💳 Buying $100 of ETH. Confirm?"
State: step=confirm, data={crypto: ETH, amount: 100, fiat: USD}
```

### User Modifications

```
Step 1: User → "buy 100 dollars of ETH"
Step 2: Agent → Shows confirmation quote
Step 3: User → "actually make it 200"
        Agent → Updates quote to $200
        State: data.amount updated to 200
```

---

## Testing Instructions

### Manual Testing

**Endpoint**: `POST https://testanvilcrypto.ddnsking.com/api/v1/conversations/{conversation_id}/messages`

**Headers**:
```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

**Test Case 1: Complete Flow**
```bash
# Step 1: Start buy flow
curl -X POST "https://testanvilcrypto.ddnsking.com/api/v1/conversations/57d4832f-c37e-4938-9b10-15457eae9c40/messages" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Buy crypto",
    "language": "en"
  }'

# Expected: Shows available cryptos

# Step 2: Select crypto
curl -X POST "..." \
  -d '{
    "content": "USDC",
    "language": "en"
  }'

# Expected: Asks for amount

# Step 3: Provide amount
curl -X POST "..." \
  -d '{
    "content": "100",
    "language": "en"
  }'

# Expected: ✅ Shows confirmation with execute button
# Response should include:
# - routing.agents_used: ["buy_workflow"]
# - execute: { action_type: "fund_wallet", provider: "privy", ... }
```

**Test Case 2: All-in-One**
```bash
curl -X POST "..." \
  -d '{
    "content": "buy 100 dollars of ETH",
    "language": "en"
  }'

# Expected: ✅ Shows confirmation with execute button immediately
```

**Test Case 3: Guest User (Should Still Work)**
```bash
# Guest endpoint
curl -X POST "https://testanvilcrypto.ddnsking.com/api/v1/guest/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "buy crypto",
    "language": "en"
  }'

# Expected: ✅ Informational response + registration prompt
```

### Validation Criteria

**✅ PASS Criteria**:
1. `routing.agents_used` contains `"buy_workflow"` (not `"buy_handler"`)
2. Response includes `execute` field with `action_type: "fund_wallet"`
3. Execute data includes: `provider`, `amount`, `crypto`, `fiat`, `chain`
4. No looping back to "which crypto to buy?" after amount provided
5. Guest users still get informational flow with registration prompt

**❌ FAIL Indicators**:
1. Response contains `"buy_handler"` for authenticated users
2. No `execute` field in response after confirmation
3. Workflow loops back to previous step
4. Guest users broken (get workflow instead of info)
5. Error messages in logs about missing workflow state

---

## Integration Tests

### Test File Structure

```
tests/integration/user/
├── test_buy_workflow.py          # NEW: Buy workflow tests (recommended)
├── test_user_agent_squad_advanced.py
└── test_user_hunter_advanced.py
```

### Recommended Test Cases

**Test 1: Complete Multi-Step Flow**
```python
@pytest.mark.asyncio
async def test_buy_workflow_complete_flow(client, conversation_id):
    """Test complete buy workflow: select crypto → amount → confirm."""

    # Step 1: Start flow
    response1 = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Buy crypto", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response1.status_code == 200
    assert "buy_workflow" in response1.json()["routing"]["agents_used"]

    # Step 2: Select crypto
    response2 = await client.post(...)
    # Assert no looping, proceeds to next step

    # Step 3: Provide amount
    response3 = await client.post(...)
    # Assert execute_data present
    assert response3.json()["execute"] is not None
    assert response3.json()["execute"]["action_type"] == "fund_wallet"
```

**Test 2: All-in-One Input**
```python
@pytest.mark.asyncio
async def test_buy_workflow_all_in_one(client, conversation_id):
    """Test buy with all parameters in one message."""

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "buy 100 dollars of ETH", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should show confirmation immediately
    assert "buy_workflow" in data["routing"]["agents_used"]
    assert "confirm" in data["agent_message"]["content"].lower()
```

**Test 3: Guest User Backward Compatibility**
```python
@pytest.mark.asyncio
async def test_buy_guest_informational_flow(client):
    """Test guest users still get informational flow."""

    response = await client.post(
        "/api/v1/guest/chat",
        json={"message": "buy crypto", "language": "en"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should NOT use buy_workflow for guests
    assert "buy_workflow" not in data.get("routing", {}).get("agents_used", [])
    assert data.get("registration_required") is not None
```

---

## Debugging

### Log Messages to Look For

**Successful Workflow**:
```
[BUY_DEBUG] Entering BUY handler section
[BUY_DEBUG] Intent: BUY
[BUY_DEBUG] User is_guest: False
[BUY_DEBUG] User is authenticated, using BuyWorkflowAgent
[BuyWorkflow] Processing step=parse_request, message=100...
[BuyWorkflow] Completed step=confirm, has_execute_data=True
[BUY_DEBUG] BuyWorkflowAgent completed
[BUY_DEBUG] Has execute_data: True
[BUY_DEBUG] Execute data extracted: action_type=fund_wallet
```

**Workflow State Continuation**:
```
[BuyWorkflow] Loaded state from context metadata
[BuyWorkflow] Processing step=confirm, message=yes...
[BuyWorkflow] Completed step=execute, has_execute_data=True
```

### Common Issues

**Issue 1: No execute_data Generated**

**Symptom**: Response has no `execute` field after user confirms

**Cause**: Workflow not reaching EXECUTE step or execute_data generation failed

**Debug**:
```bash
# Check logs for workflow state progression
grep "BuyWorkflow.*Completed step" logs/app.log

# Check for errors in execute_data generation
grep "execute_data" logs/app.log
```

**Issue 2: Workflow Loops Back**

**Symptom**: After providing amount, agent asks for crypto again

**Cause**: State not persisted between turns

**Debug**:
```bash
# Check if workflow_state is in message metadata
grep "workflow_state" logs/app.log

# Check if conversation_history includes metadata
grep "Include metadata for workflow continuation" logs/app.log
```

**Issue 3: Guest Users Broken**

**Symptom**: Guests get workflow agent instead of informational flow

**Cause**: Guest check not working correctly

**Debug**:
```bash
# Verify guest detection
grep "\[BUY_DEBUG\] User is_guest" logs/app.log

# Should show: User is_guest: True for guests
```

---

## Rollback Plan

If issues arise, rollback to previous version:

### Rollback Steps

1. **Revert commit**:
```bash
git revert HEAD
```

2. **Or restore old BuyHandler code**:
```bash
git diff HEAD~1 src/app/presentation/http/controllers/chat/conversations_router.py > buy_fix.patch
git checkout HEAD~1 -- src/app/presentation/http/controllers/chat/conversations_router.py
```

3. **Emergency hotfix** (if needed):
```python
# Line 1382: Replace BuyWorkflowAgent with old BuyHandler
else:
    # HOTFIX: Revert to BuyHandler temporarily
    from app.application.chat.handlers.buy_handler import BuyHandler
    buy_handler = BuyHandler(...)
    # ... rest of old code
```

### Rollback Impact

- Authenticated users will experience the looping bug again
- Guest users unaffected (no changes to guest flow)
- No data loss (metadata fields remain compatible)

---

## Related Files

### Core Implementation

- `src/app/presentation/http/controllers/chat/conversations_router.py` (lines 1351-1464)
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/base_workflow_agent.py`

### Legacy Handler (Still Used for Guests)

- `src/app/application/chat/handlers/buy_handler.py`

### Related Workflows (Same Pattern)

- `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/lending_workflow_agent.py`

### Domain Models

- `src/app/domain/value_objects/message_content.py`
- `src/app/domain/value_objects/agent_squad/conversation_context.py`

---

## Performance Impact

**Expected**: Minimal to no performance impact

### Metrics

- **Response Time**: Same as other workflow agents (~2-5 seconds)
- **Memory**: No significant change (workflow state stored in metadata)
- **Database**: No additional queries (same conversation_id and message pattern)

### Monitoring

Monitor these metrics after deployment:
- Average response time for BUY intent
- Error rate in buy_workflow
- Conversion rate (buy initiated → execute button shown)

---

## Next Steps

### Immediate (Post-Deployment)

1. ✅ Monitor logs for BuyWorkflowAgent execution
2. ✅ Verify execute_data generation in production
3. ✅ Test with real user JWT tokens
4. ✅ Check Privy modal integration

### Short-Term

1. Add integration tests (test_buy_workflow.py)
2. Add error tracking for workflow failures
3. Monitor user feedback on buy flow
4. Document Privy integration details

### Long-Term

1. Consider removing BuyHandler completely (if guest flow can be migrated)
2. Add analytics for buy workflow completion rates
3. Add support for more payment methods
4. Optimize parameter extraction with fine-tuned LLM

---

## Success Metrics

**✅ Fix Complete When**:

1. Authenticated users can complete buy flow without looping
2. Execute button appears after confirmation
3. Privy modal opens correctly with purchase details
4. Guest users still get informational flow
5. No increase in error rates
6. Logs show successful BuyWorkflowAgent execution

---

## Contact & Support

For issues or questions:
1. Check logs: `grep "BUY_DEBUG\|BuyWorkflow" logs/app.log`
2. Review this document: `BUY_WORKFLOW_FIX_COMPLETE.md`
3. Review CTO analysis: `cto.md` (methodology used)
4. Check error file: `buy-errors.m` (original bug report)

---

**Status**: ✅ Implementation Complete
**Solution**: Hybrid Approach (Solution C)
**Files Modified**: 1 (conversations_router.py, 114 lines)
**Backward Compatible**: Yes (guests unaffected)
**Test Coverage**: Manual testing required, integration tests recommended
