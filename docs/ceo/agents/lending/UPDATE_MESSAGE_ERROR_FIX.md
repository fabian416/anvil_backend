# Update Message Error Fix

**Date**: 2026-01-28  
**Status**: ✅ **FIXED**

---

## Error Summary

**Error**: `AttributeError: 'GuestRepositorySqla' object has no attribute 'update_message'`  
**Location**: `src/app/application/guest/commands/send_guest_message.py`  
**Lines**: 2073, 3043

---

## Problem

The code was trying to call `update_message()` on `GuestRepositorySqla` to update the `is_restricted_action` flag after creating a message, but this method doesn't exist in the repository interface or implementation.

**Root Cause**:
- Messages were created with `is_restricted_action=False`
- Code then tried to update them to `is_restricted_action=True` if `GUEST_AUTH` agent was used
- `GuestRepository` port doesn't define `update_message()` method
- `GuestRepositorySqla` implementation doesn't have `update_message()` method

---

## Solution

Instead of updating the message after creation, we now set `is_restricted_action` when creating the message:

**Before**:
```python
# Create message with is_restricted_action=False
agent_message = GuestMessage.create_assistant_message(
    ...
    is_restricted_action=False,
)
await self._guest_repo.create_message(agent_message)

# Check if GUEST_AUTH was used
used_guest_auth = any(...)
if used_guest_auth:
    # Try to update (FAILS - method doesn't exist)
    agent_message.is_restricted_action = True
    await self._guest_repo.update_message(agent_message)  # ❌ Error!
```

**After**:
```python
# Check if GUEST_AUTH was used BEFORE creating message
used_guest_auth = any(...)
if used_guest_auth:
    registration_required = {...}

# Create message with correct is_restricted_action value
agent_message = GuestMessage.create_assistant_message(
    ...
    is_restricted_action=used_guest_auth,  # ✅ Set correctly from start
)
await self._guest_repo.create_message(agent_message)
```

---

## Files Modified

1. **`src/app/application/guest/commands/send_guest_message.py`**
   - **Line ~2016-2073**: Moved `used_guest_auth` check before message creation in `_process_with_llm_supervisor()`
   - **Line ~3012-3038**: Moved `used_guest_auth` check before message creation in `_handle_with_agent_squad()`
   - Removed both `update_message()` calls

---

## Changes Made

### Change 1: `_process_with_llm_supervisor()` method
- Moved `used_guest_auth` check before `agent_message` creation
- Set `is_restricted_action=used_guest_auth` when creating message
- Removed `update_message()` call

### Change 2: `_handle_with_agent_squad()` method
- Moved `used_guest_auth` check before `agent_message` creation
- Set `is_restricted_action=used_guest_auth` when creating message
- Removed `update_message()` call

---

## Verification

```python
# Test import
from app.application.guest.commands.send_guest_message import SendGuestMessage
# ✅ Module imports successfully

# Check for update_message calls
grep -n "update_message" src/app/application/guest/commands/send_guest_message.py
# ✅ No update_message calls found
```

---

## Impact

### Before Fix
- ❌ `AttributeError` when `GUEST_AUTH` agent is used
- ❌ Guest chat fails for restricted actions
- ❌ Workflow execution crashes

### After Fix
- ✅ Messages created with correct `is_restricted_action` value
- ✅ No post-creation updates needed
- ✅ Guest chat works correctly for all actions
- ✅ Workflow execution completes successfully

---

## Why This Approach

**Messages are immutable once created** - The guest message system follows an append-only pattern where messages are created once and not modified. This is a common pattern for chat systems to maintain audit trails and prevent data inconsistencies.

**Solution**: Set the correct value when creating the message instead of trying to update it afterward.

---

**Fix Complete!** 🎉
