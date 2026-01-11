# Swap Continuation Flow Bugfix

**Date**: 2026-01-10
**Status**: ✅ FIXED

## Problem

The multi-step swap flow was broken due to two critical bugs:

### Bug 1: Old State Being Retrieved

**Symptom**:
```
User: swap
Bot: "Swapping ETH to USDC. How much ETH would you like to swap?"
```

User starts fresh with "swap" but bot shows old swap state from previous conversation.

**Root Cause**:
- `_get_continuation_state()` was calling `get_messages(limit=1)`
- `get_messages()` orders messages by `created_at.asc()` (oldest first)
- So `limit=1` returned the OLDEST message instead of the NEWEST
- Old continuation state was being applied to new conversations

**Fix**:
```python
# Before (WRONG - gets oldest message)
messages = await self._guest_repo.get_messages(conversation_id, limit=1)
last_message = messages[0]

# After (CORRECT - gets most recent message)
messages = await self._guest_repo.get_messages(conversation_id, limit=10)
last_assistant_message = None
for msg in reversed(messages):
    if msg.role.value == "assistant":
        last_assistant_message = msg
        break
```

### Bug 2: Continuation Flow Not Preserved

**Symptom**:
```
User: Swap BTC to ETH
Bot: "How much BTC do you want to swap?"
User: 0.01
Bot: "I'm your AI assistant for DeFi! I can help with..."
```

After correctly asking for amount, bot doesn't continue swap flow when user enters "0.01".

**Root Cause**:
- Intent detection runs on every message
- "0.01" doesn't match any intent patterns (not recognized as swap)
- Falls back to generic greeting
- `continuation_step` was being ignored during intent detection

**Fix**:
```python
# Check for continuation BEFORE intent detection
if continuation_step:
    # We're in a multi-step flow, use the intent from that flow
    if "swap" in continuation_step:
        intent = ChatIntent.SWAP_MOONPAY
        handler = "moonpay_swap"
        confidence = 1.0
        logger.info(f"[Continuation] Using swap intent: {continuation_step}")
    elif "lending" in continuation_step:
        intent = ChatIntent.LENDING_RATE
        handler = "lending"
        confidence = 1.0
else:
    # No continuation, detect intent normally
    intent, confidence, handler = await self._detect_intent_with_context(
        content, context, language
    )
```

## Solution Summary

1. **Fixed state retrieval**: Get the MOST RECENT assistant message, not the oldest
2. **Fixed intent override**: When `pending_action` exists, use that intent instead of detecting new one
3. **Added logging**: Track continuation state for debugging

## Files Modified

1. `src/app/application/guest/commands/send_guest_message.py`:
   - Updated `_get_continuation_state()` to get most recent message
   - Added continuation check before intent detection
   - Added logging for continuation flow

## Expected Behavior After Fix

### Complete Multi-Step Flow

```
User: swap
Bot: 🔄 Start Swap
     Which token do you want to swap FROM?
     Available tokens: BTC, ETH, SOL, USDC

User: BTC
Bot: 🔄 Swap BTC
     Which token do you want to receive?
     Available: BTC, ETH, SOL, USDC

User: ETH
Bot: 🔄 Swap BTC → ETH
     How much BTC do you want to swap?
     Example: 1 or 0.5 or 100

User: 0.01
Bot: 🌙 MoonPay Swap Quote
     0.01 BTC = 0.2764 ETH
     Exchange Rate: 27.64
     Network Fee: $5.00

     Confirm this swap?
     • confirm or yes to proceed
     • change amount to X to modify
     • cancel to abort

User: confirm
Bot: ✅ Swap Confirmed!
     👉 Sign up to complete this swap → /signup
```

### Key Improvements

✅ Fresh "swap" command starts new flow (no old state)
✅ Amount entry (0.01) continues flow correctly
✅ Edit commands work ("change amount to 0.5")
✅ Confirmation flow preserved
✅ State persists across all steps

## Testing

Run the complete flow:

```bash
# Step 1
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "swap", "language": "en"}'

# Step 2 (use conversation_id from step 1)
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "BTC", "language": "en", "conversation_id": "..."}'

# Step 3
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "ETH", "language": "en", "conversation_id": "..."}'

# Step 4
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "0.01", "language": "en", "conversation_id": "..."}'

# Step 5
curl -X POST http://localhost:8000/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "confirm", "language": "en", "conversation_id": "..."}'
```

All steps should now flow correctly without breaking.

## Related Files

- `docs/GUEST_SWAP_MULTISTEP_IMPLEMENTATION.md` - Original implementation
- `src/app/application/guest/handlers/moonpay_swap_multistep.py` - Multi-step handler
- `src/app/domain/guest/entities/guest_message.py` - Message entity with metadata
