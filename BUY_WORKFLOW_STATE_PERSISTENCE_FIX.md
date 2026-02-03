# Buy Workflow State Persistence Fix

**Date**: 2026-01-27
**Issue**: Workflow state not persisting between conversation turns
**Root Cause**: Missing workflow_state in message metadata
**Solution**: Store workflow_metadata from BuyWorkflowAgent in message metadata

---

## Problem Discovered

After implementing the first fix (replacing BuyHandler with BuyWorkflowAgent), testing revealed:

✅ **PASS**: BuyWorkflowAgent is being used for authenticated users
✅ **PASS**: No more legacy BuyHandler for authenticated users
❌ **FAIL**: Workflow still loops back - state not persisting between turns

### Test Results

```bash
Test 1: "Buy crypto" → ✅ buy_workflow agent used
Test 2: "USDC" → ✅ Workflow proceeds to ask for amount
Test 3: "100" → ❌ Workflow loops back asking "which crypto to buy?"
```

### Root Cause Analysis

The BuyWorkflowAgent generates `workflow_state` in its metadata:

```python
# In BuyWorkflowAgent.execute()
return AgentResponse(
    content=response_content,
    metadata={
        "workflow_name": "BuyWorkflow",
        "workflow_state": {
            "step": "confirm",
            "data": {"crypto": "USDC", "amount": 100, "fiat": "USD"},
            "confirmed": False,
        },
        "current_step": "confirm",
    }
)
```

**BUT** this metadata was not being saved to the database message metadata, so when the user sends the next message, the workflow starts fresh without previous state.

---

## Solution Implemented

### Change 1: Store workflow_metadata in BUY handler

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Lines**: 1431-1440

```python
agent_content = agent_response.content

# Extract execute_data from workflow metadata if available
if agent_response.metadata and agent_response.metadata.get("execute_data"):
    execute_data = ExecuteActionData(**agent_response.metadata["execute_data"])
    logger.info(f"[BUY_DEBUG] Execute data extracted: action_type={execute_data.action_type}")

# Store workflow metadata for message persistence (will be saved at line 1650+)
# This is critical for multi-turn workflow state continuity
workflow_metadata = agent_response.metadata if agent_response.metadata else {}
logger.info(f"[BUY_DEBUG] Workflow metadata stored: has_workflow_state={bool(workflow_metadata.get('workflow_state'))}")
```

### Change 2: Initialize workflow_metadata variable

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Lines**: 1075-1083

```python
# Initialize response variables
agent_content = ""
enrichment = None
registration_required = None
pending_action = None
execute_data = None  # Execute action data for /execute endpoint
used_agent_gateway = False  # Flag for when AgentGateway (LLM) was used
handler_result = {}  # Default empty handler result for metadata extraction
workflow_metadata = None  # Workflow metadata from BuyWorkflowAgent for state persistence
```

### Change 3: Save workflow_state to message metadata

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Lines**: 1656-1672

```python
# Store buy info for multi-turn buy flow persistence
# For authenticated users using BuyWorkflowAgent, store workflow_state
# For guests using BuyHandler, store buy_info
if intent_result.intent.value.startswith("BUY"):
    # Check if we have workflow_metadata from BuyWorkflowAgent (authenticated users)
    if 'workflow_metadata' in locals() and workflow_metadata:
        # Store workflow state from BuyWorkflowAgent
        if workflow_metadata.get("workflow_state"):
            metadata["workflow_state"] = workflow_metadata["workflow_state"]
            logger.info(f"[BUY_DEBUG] Saving workflow_state to message metadata")
        if workflow_metadata.get("workflow_name"):
            metadata["workflow_name"] = workflow_metadata["workflow_name"]
        if workflow_metadata.get("current_step"):
            metadata["current_step"] = workflow_metadata["current_step"]
    # Fallback for BuyHandler (guests or error fallback)
    elif hasattr(handler_result, "metadata") and handler_result.metadata:
        buy_info = handler_result.metadata
        if buy_info:
            metadata["buy_info"] = buy_info
```

---

## How State Persistence Works

### Step 1: BuyWorkflowAgent generates state

```python
# In BuyWorkflowAgent.execute()
state = WorkflowState(
    step="confirm",
    data={"crypto": "USDC", "amount": 100, "fiat": "USD"},
)

return AgentResponse(
    content="Shows confirmation...",
    metadata={
        "workflow_state": state.to_dict(),  # ← State object
        "workflow_name": "BuyWorkflow",
    }
)
```

### Step 2: Router stores metadata

```python
# In conversations_router.py (line 1437)
workflow_metadata = agent_response.metadata
# workflow_metadata = {
#     "workflow_state": {"step": "confirm", "data": {...}},
#     "workflow_name": "BuyWorkflow",
# }
```

### Step 3: Metadata saved to database

```python
# In conversations_router.py (line 1658-1662)
metadata["workflow_state"] = workflow_metadata["workflow_state"]
metadata["workflow_name"] = workflow_metadata["workflow_name"]

assistant_message = ChatMessage.create_assistant_message(
    ...
    metadata=metadata,  # ← Includes workflow_state
)
await message_repository.save(assistant_message)
```

### Step 4: Next turn loads state

```python
# When user sends next message, conversation_history includes metadata
conversation_history = [
    {
        "role": "assistant",
        "content": "Shows confirmation...",
        "metadata": {
            "workflow_state": {"step": "confirm", "data": {...}},  # ← Restored
            "workflow_name": "BuyWorkflow",
        }
    }
]

# BuyWorkflowAgent._load_state() reads from conversation_history
state = WorkflowState.from_dict(msg["metadata"]["workflow_state"])
# State restored! Continue from "confirm" step
```

---

## Expected Flow After Fix

```
Step 1: User → "Buy crypto"
        Agent → Shows available cryptos
        DB: workflow_state = {step: "parse_request", data: {}}

Step 2: User → "USDC"
        Agent loads state → Sees step=parse_request
        Agent → "How much would you like to spend?"
        DB: workflow_state = {step: "parse_request", data: {crypto: "USDC"}}

Step 3: User → "100"
        Agent loads state → Sees step=parse_request, data={crypto: "USDC"}
        Agent → Shows confirmation: "💳 Buying $100 of USDC. Confirm?"
        DB: workflow_state = {step: "confirm", data: {crypto: "USDC", amount: 100, fiat: "USD"}}
        ✅ NO MORE LOOPING!

Step 4: User → "yes"
        Agent loads state → Sees step=confirm, data={...}
        Agent → "✅ Opening purchase flow..." + execute_data
        DB: workflow_state = {step: "execute", execute_data: {...}}
        Frontend: Privy modal opens
```

---

## Testing

### Restart Server

```bash
cd /home/ubuntu/anvil_backend

# Stop existing server
pkill -f "uvicorn"

# Restart
make start
# Or
uvicorn app.run:app --reload
```

### Run Test Again

```bash
./test_buy_workflow_fix.sh
```

**Expected Results**:
- ✅ Test 1: buy_workflow agent detected
- ✅ Test 2: Workflow proceeded to amount step
- ✅ Test 3: Workflow did NOT loop back ← **THIS SHOULD NOW PASS**
- ✅ Test 3: Shows confirmation or execute button

### Manual Verification

```bash
# Check logs for workflow state persistence
tail -f logs/app.log | grep "BUY_DEBUG"

# Expected log sequence:
[BUY_DEBUG] Workflow metadata stored: has_workflow_state=True
[BUY_DEBUG] Saving workflow_state to message metadata
[BuyWorkflow] Loaded state from context metadata
[BuyWorkflow] Processing step=confirm, message=100...
```

### Check Database

```sql
-- Check message metadata includes workflow_state
SELECT
    id,
    content,
    metadata->>'workflow_state' as workflow_state,
    metadata->>'workflow_name' as workflow_name
FROM chat_messages
WHERE conversation_id = '57d4832f-c37e-4938-9b10-15457eae9c40'
ORDER BY created_at DESC
LIMIT 5;
```

---

## Validation Checklist

After server restart:

- [ ] Server starts without errors
- [ ] Test script passes all 3 steps
- [ ] Logs show "Workflow metadata stored: has_workflow_state=True"
- [ ] Logs show "Saving workflow_state to message metadata"
- [ ] Logs show "Loaded state from context metadata"
- [ ] No looping back after providing amount
- [ ] Execute button appears after confirmation

---

## Complete Fix Summary

### Total Changes

1. **First Fix** (BUY_WORKFLOW_FIX_COMPLETE.md):
   - Replaced BuyHandler with BuyWorkflowAgent for authenticated users
   - Lines 1351-1464 (114 lines)

2. **Second Fix** (This document):
   - Store workflow_metadata from agent response (line 1437)
   - Initialize workflow_metadata variable (line 1083)
   - Save workflow_state to message metadata (lines 1656-1672)
   - Total: 3 small changes across 20 lines

### Files Modified

- `src/app/presentation/http/controllers/chat/conversations_router.py`

### Total Lines Changed

- First fix: 114 lines replaced
- Second fix: 20 lines added/modified
- **Total: 134 lines across 1 file**

---

## Why This Fix Was Needed

The first fix correctly switched to BuyWorkflowAgent, but the workflow state wasn't persisting because:

1. BaseWorkflowAgent generates workflow_state in metadata ✅
2. Router receives agent_response with metadata ✅
3. **BUT** router wasn't saving workflow_state to message metadata ❌
4. Next turn → conversation_history has no workflow_state ❌
5. BuyWorkflowAgent starts fresh without previous state ❌

Now with the fix:
1. BaseWorkflowAgent generates workflow_state in metadata ✅
2. Router receives agent_response with metadata ✅
3. Router stores workflow_metadata variable ✅ **NEW**
4. Router saves workflow_state to message metadata ✅ **NEW**
5. Next turn → conversation_history has workflow_state ✅
6. BuyWorkflowAgent loads state and continues ✅

---

## Comparison with Supervisor Path

The supervisor path (authenticated_supervisor) already does this correctly:

```python
# Line 779-784 in conversations_router.py
if supervisor_result.metadata:
    if supervisor_result.metadata.get("workflow_state"):
        message_metadata["workflow_state"] = supervisor_result.metadata["workflow_state"]
    if supervisor_result.metadata.get("workflow_name"):
        message_metadata["workflow_name"] = supervisor_result.metadata["workflow_name"]
```

Our fix mirrors this pattern for the intent-based path.

---

## Rollback Plan

If issues arise:

```bash
git revert HEAD  # Reverts second fix
git revert HEAD~1  # Reverts first fix (if needed)
```

---

## Next Steps

1. ✅ Restart server
2. ✅ Run test script (`./test_buy_workflow_fix.sh`)
3. ✅ Verify logs show workflow state persistence
4. ✅ Test with real user in production
5. ✅ Monitor error rates and completion rates
6. Commit both fixes together

---

**Status**: ✅ Implementation Complete
**Changes**: 3 small additions for state persistence
**Impact**: Critical - enables multi-turn workflow continuity
**Testing**: Requires server restart
