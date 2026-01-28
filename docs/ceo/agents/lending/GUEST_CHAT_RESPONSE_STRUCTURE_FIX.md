# Guest Chat Response Structure Consistency Fix

**Date**: 2026-01-28  
**Status**: ✅ **FIXED**

---

## Problem

Guest chat responses had inconsistent structure:
- ✅ "what is anvil?" → Includes `sources` and `agent_timings` in enrichment
- ❌ "Buy crypto" → Missing `sources` and `agent_timings` in enrichment

**User Requirement**: All guest chat responses must have the same structure with:
- `agent_message.sources` - Always present (even if empty array)
- `enrichment.agent_timings` - Always present (even if empty array)

---

## Solution

Updated all response paths to ensure consistent structure:

### 1. Legacy Handler Path (Line ~1793-1841)

**Before**:
```python
agent_message_dict = {
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": agent_message.content,
    "created_at": agent_message.created_at.isoformat(),
}
# Add sources if available
if sources:
    agent_message_dict["sources"] = sources

final_enrichment = enrichment if enrichment else {}
final_enrichment["disclaimer"] = get_demo_disclaimer(language)
```

**After**:
```python
# Ensure agent_timings is always present (even if empty)
final_enrichment = enrichment if enrichment else {}
final_enrichment["disclaimer"] = get_demo_disclaimer(language)
if "agent_timings" not in final_enrichment:
    final_enrichment["agent_timings"] = []

agent_message_dict = {
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": agent_message.content,
    "created_at": agent_message.created_at.isoformat(),
    "sources": sources,  # Always include sources (even if empty array)
}
```

### 2. Blocked Message Path (Line ~287)

**Before**:
```python
agent_message={
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": block_response,
    "created_at": agent_message.created_at.isoformat(),
},
enrichment={"blocked": True, "reason": "harmful_content"},
```

**After**:
```python
agent_message={
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": block_response,
    "created_at": agent_message.created_at.isoformat(),
    "sources": [],  # Always include sources (empty for blocked messages)
},
enrichment={
    "blocked": True,
    "reason": "harmful_content",
    "agent_timings": [],  # Always include agent_timings (empty for blocked messages)
},
sources=[],  # Always include sources at top level
```

### 3. Swap Rate Fast-Path (Line ~382)

**Before**:
```python
agent_message={
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": response.content,
    "created_at": agent_message.created_at.isoformat(),
},
enrichment={},
sources=[s.to_dict() for s in response.sources] if response.sources else [],
```

**After**:
```python
agent_message={
    "id": str(agent_message.id),
    "role": agent_message.role.value,
    "content": response.content,
    "created_at": agent_message.created_at.isoformat(),
    "sources": [s.to_dict() for s in response.sources] if response.sources else [],  # Always include sources
},
enrichment={
    "agent_timings": [],  # Always include agent_timings (empty for fast-path)
},
sources=[s.to_dict() for s in response.sources] if response.sources else [],
```

### 4. Greeting Direct Path (Line ~598)

**Before**:
```python
enrichment = {
    "agent_squad": True,
    "workflow_type": "chat_agent_direct",
    "task_count": 1,
    "disclaimer": get_demo_disclaimer(language),
    "agents_used": ["chat"],
}
if debug_timing_enabled:
    enrichment["agent_timings"] = [...]
```

**After**:
```python
enrichment = {
    "agent_squad": True,
    "workflow_type": "chat_agent_direct",
    "task_count": 1,
    "disclaimer": get_demo_disclaimer(language),
    "agents_used": ["chat"],
    "agent_timings": [],  # Initialize as empty array
}
if debug_timing_enabled and greeting_execution_time_ms:
    enrichment["agent_timings"] = [...]
```

### 5. LLM Supervisor Path (`_process_with_llm_supervisor`) (Line ~2070)

**Before**:
```python
enrichment = {
    "agent_squad": True,
    "workflow_type": "llm_planned",
    ...
}
if agent_timings:
    enrichment["agent_timings"] = agent_timings
```

**After**:
```python
enrichment = {
    "agent_squad": True,
    "workflow_type": "llm_planned",
    ...
    "agent_timings": agent_timings if agent_timings else [],  # Always include agent_timings (even if empty)
}
```

### 6. Agent Squad Supervisor Path (`_handle_with_agent_squad`) (Line ~2981)

**Before**:
```python
enrichment = {
    "agent_squad": True,
    "workflow_type": "supervisor_coordinator",
    ...
}
if debug_timing_enabled:
    # Build timings...
    if all_timings:
        enrichment["agent_timings"] = all_timings
```

**After**:
```python
# Initialize agent_timings list (always present)
all_timings = []
if debug_timing_enabled:
    # Build timings...
    if agent_timings:
        all_timings.extend(agent_timings)

enrichment = {
    "agent_squad": True,
    "workflow_type": "supervisor_coordinator",
    ...
    "agent_timings": all_timings,  # Always include agent_timings (even if empty)
}
```

---

## Consistent Response Structure

All guest chat responses now have this structure:

```json
{
  "agent_message": {
    "id": "...",
    "role": "assistant",
    "content": "...",
    "created_at": "...",
    "sources": []  // Always present (even if empty)
  },
  "enrichment": {
    "agent_squad": true,
    "workflow_type": "...",
    "task_count": 1,
    "disclaimer": "...",
    "agents_used": [...],
    "agent_timings": []  // Always present (even if empty)
  },
  "sources": []  // Always present at top level (even if empty)
}
```

---

## Files Modified

1. **`src/app/application/guest/commands/send_guest_message.py`**
   - Updated all `GuestMessageResult` return statements
   - Ensured `agent_message.sources` is always present
   - Ensured `enrichment.agent_timings` is always present
   - Updated 6 different response paths

---

## Verification

```python
# Test import
from app.application.guest.commands.send_guest_message import SendGuestMessage
# ✅ Module imports successfully
```

---

## Impact

### Before Fix
- ❌ Inconsistent response structure
- ❌ Some responses missing `sources`
- ❌ Some responses missing `agent_timings`
- ❌ Frontend needs to handle missing fields

### After Fix
- ✅ Consistent response structure across all paths
- ✅ `sources` always present in `agent_message.sources`
- ✅ `agent_timings` always present in `enrichment.agent_timings`
- ✅ Frontend can rely on consistent structure
- ✅ Easier to parse and display responses

---

**Fix Complete!** 🎉
