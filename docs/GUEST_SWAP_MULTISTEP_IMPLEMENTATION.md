# Guest Multi-Step Swap Flow Implementation

**Date**: 2026-01-10
**Status**: ✅ COMPLETE

## Overview

Implemented a complete conversational multi-step swap flow for guest users that guides them through the swap process step-by-step with confirmation before execution.

## Flow Design

```
User: "swap"
Bot: "Which token do you want to swap FROM? (BTC, ETH, SOL, USDC)"
↓
User: "BTC"
Bot: "Which token do you want to receive? (BTC, ETH, SOL, USDC)"
↓
User: "ETH"
Bot: "How much BTC do you want to swap?"
↓
User: "1"
Bot: "1 BTC = 27.64 ETH. Exchange Rate: 27.64. Network Fee: $5.00"
     "Confirm? (yes/change amount to X/cancel)"
↓
User: "confirm"
Bot: "✅ Swap Confirmed! Sign up to complete this swap → /signup"
```

## Implementation Details

### 1. Multi-Step Handler (`moonpay_swap_multistep.py`)

**Location**: `src/app/application/guest/handlers/moonpay_swap_multistep.py`

**State Machine**:
- `swap_awaiting_from_token`: Waiting for user to specify FROM token
- `swap_awaiting_to_token`: Waiting for user to specify TO token
- `swap_awaiting_amount`: Waiting for user to specify amount
- `swap_awaiting_confirmation`: Waiting for user to confirm or edit

**Key Methods**:
- `handle_flow()`: Main flow orchestration
- `_handle_continuation()`: Process continuation from previous step
- `_ask_for_from_token()`: Request FROM token
- `_ask_for_to_token()`: Request TO token
- `_ask_for_amount()`: Request amount
- `_show_quote_and_confirm()`: Show quote and ask for confirmation
- `_execute_swap()`: Execute swap (requires auth)
- `_handle_edit()`: Handle edit requests (e.g., "change amount to 0.5")

**Return Format**:
```python
{
    "content": "Bot message content",
    "enrichment": {...},  # Optional metadata
    "requires_registration": bool,
    "pending_action": "swap_awaiting_X",  # Next state
    "swap_info": {  # Accumulated swap parameters
        "from_token": "btc",
        "to_token": "eth",
        "amount": "1"
    }
}
```

### 2. Database Schema Changes

**Migration**: `2026_01_10_2336-9331ebd70cc7_add_metadata_column_to_guest_messages.py`

Added `metadata` JSONB column to `guest_messages` table to store continuation state.

**Entity Update**: `src/app/domain/guest/entities/guest_message.py`
```python
@dataclass
class GuestMessage:
    # ... existing fields ...
    metadata: dict | None = field(default_factory=dict)
```

**SQLAlchemy Mapping**: `src/app/infrastructure/persistence_sqla/mappings/guest.py`
```python
# Note: 'metadata' is reserved in SQLAlchemy
extra_metadata = mapped_column("metadata", JSONB, default={}, server_default='{}')
```

### 3. State Persistence (`send_guest_message.py`)

**Continuation State Extraction**:
```python
async def _get_continuation_state(self, conversation_id: UUID):
    """Get continuation state from the last assistant message."""
    messages = await self._guest_repo.get_messages(conversation_id, limit=1)

    if not messages or messages[0].role.value != "assistant":
        return None, None, None

    metadata = messages[0].metadata or {}
    return (
        metadata.get("pending_action"),
        metadata.get("swap_info"),
        metadata.get("lending_info")
    )
```

**Handler Call with Continuation**:
```python
# Get continuation state
continuation_step, previous_swap_info, previous_lending_info = \
    await self._get_continuation_state(conversation.id)

# Pass to handler
handler_result = await self._handler_service.handle_intent(
    intent,
    content,
    language,
    context=context,
    continuation_step=continuation_step,
    previous_swap_info=previous_swap_info,
    previous_lending_info=previous_lending_info,
)

# Store in message metadata
message_metadata = {}
if handler_result.get("pending_action"):
    message_metadata["pending_action"] = handler_result["pending_action"]
if handler_result.get("swap_info"):
    message_metadata["swap_info"] = handler_result["swap_info"]

agent_message = GuestMessage.create_assistant_message(
    # ... other params ...
    metadata=message_metadata if message_metadata else None,
)
```

### 4. Handler Service Integration (`guest_handler_service.py`)

**Initialization**:
```python
self._moonpay_multistep = MoonPaySwapMultiStepHandler(moonpay_swap_handler) \
    if moonpay_swap_handler else None
```

**Handler Signature Update**:
```python
async def handle_intent(
    self,
    intent: ChatIntent,
    content: str,
    language: str = "en",
    context: str = "",
    is_authenticated: bool = False,
    continuation_step: str | None = None,  # NEW
    previous_lending_info: dict | None = None,
    previous_swap_info: dict | None = None,  # NEW
    user_id: int | None = None,
) -> dict[str, Any]:
```

**Swap Intent Routing**:
```python
elif intent == ChatIntent.SWAP_MOONPAY:
    return await self._handle_moonpay_swap(
        content,
        language,
        is_authenticated,
        continuation_step,
        previous_swap_info,
    )
```

**MoonPay Handler Delegation**:
```python
async def _handle_moonpay_swap(
    self,
    content: str,
    language: str,
    is_authenticated: bool,
    continuation_step: str | None = None,
    previous_swap_info: dict | None = None,
) -> dict[str, Any]:
    # Use multi-step flow handler
    if self._moonpay_multistep:
        return await self._moonpay_multistep.handle_flow(
            content=content,
            language=language,
            is_authenticated=is_authenticated,
            continuation_step=continuation_step,
            previous_swap_info=previous_swap_info,
        )
```

## Testing

### State Machine Test

Created `test_swap_simple.py` to verify state transitions:

```
✅ swap → swap_awaiting_from_token
✅ BTC → swap_awaiting_to_token (from_token: btc)
✅ ETH → swap_awaiting_amount (from_token: btc, to_token: eth)
✅ 1 → swap_awaiting_confirmation (full swap info)
✅ confirm → requires_registration=True
```

All state transitions work correctly.

## Features

### ✅ Implemented

1. **Step-by-step parameter collection**
   - FROM token → TO token → Amount → Confirmation

2. **State persistence across messages**
   - Stores `pending_action` and `swap_info` in message metadata
   - Retrieves continuation state from last message

3. **Confirmation before execution**
   - Shows quote with exchange rate and fees
   - Requires explicit confirmation

4. **Edit capabilities**
   - "change amount to 0.5" - re-quotes with new amount
   - Can modify parameters mid-flow

5. **Multi-language support**
   - English and Spanish translations
   - Consistent with guest chat system

6. **Registration requirement**
   - Prompts guest to sign up for execution
   - Maintains UX flow consistency

### 🎯 Example Flow

```
User: swap
Bot: 🔄 Start Swap

Which token do you want to swap FROM?

Available tokens: BTC, ETH, SOL, USDC

👉 Sign up to execute this action → /signup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: BTC
Bot: 🔄 Swap BTC

Which token do you want to receive?

Available: BTC, ETH, SOL, USDC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: ETH
Bot: 🔄 Swap BTC → ETH

How much BTC do you want to swap?

Example: 1 or 0.5 or 100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: 1
Bot: 🌙 MoonPay Swap Quote

1 BTC = 27.64 ETH

Exchange Rate: 27.64
Network Fee: $5.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confirm this swap?

Reply:
• confirm or yes to proceed
• change amount to X to modify
• cancel to abort

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: confirm
Bot: ✅ Swap Confirmed!

👉 Sign up to complete this swap → /signup
```

## Files Modified

1. **NEW**: `src/app/application/guest/handlers/moonpay_swap_multistep.py` (370 lines)
2. **NEW**: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_01_10_2336-9331ebd70cc7_add_metadata_column_to_guest_messages.py`
3. **MODIFIED**: `src/app/domain/guest/entities/guest_message.py`
   - Added `metadata` field
   - Updated `create_assistant_message()` method
4. **MODIFIED**: `src/app/infrastructure/persistence_sqla/mappings/guest.py`
   - Added `extra_metadata` column mapping
5. **MODIFIED**: `src/app/application/guest/commands/send_guest_message.py`
   - Added `_get_continuation_state()` method
   - Updated handler call to pass continuation parameters
   - Extract and store metadata in messages
6. **MODIFIED**: `src/app/application/guest/handlers/guest_handler_service.py`
   - Added multi-step handler initialization
   - Updated `handle_intent()` signature
   - Updated swap intent routing

## Migration Applied

```bash
alembic upgrade head
# INFO  [alembic.runtime.migration] Running upgrade ac22693e3b44 -> 9331ebd70cc7, add_metadata_column_to_guest_messages
```

## Architecture Benefits

1. **Separation of Concerns**
   - Multi-step logic isolated in dedicated handler
   - State management in message metadata
   - Clean interface with command layer

2. **Extensibility**
   - Easy to add more multi-step flows (lending, staking, etc.)
   - Pattern can be reused for authenticated users
   - Edit capabilities extensible

3. **Testability**
   - State machine logic testable in isolation
   - Clear state transitions
   - Predictable behavior

4. **User Experience**
   - Guides users through complex operations
   - Prevents errors with step-by-step validation
   - Clear feedback at each step

## Next Steps (Optional)

1. Add more edit commands (change from token, change to token)
2. Add swap history viewing
3. Add price alerts for favorable rates
4. Add slippage tolerance configuration
5. Implement similar multi-step flows for lending, staking

## Related Documentation

- `docs/GUEST_CHAT_SYSTEM.md` - Guest chat architecture
- `docs/HUNTER_AI_DATA_SOURCES.md` - Data sources for quotes
- `docs/DEPRECATION_PLAN.md` - Legacy system migration
