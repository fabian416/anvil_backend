# Intent Detection WebSocket Integration Guide

**Status**: Schemas Complete | WebSocket Integration Needed
**Date**: December 16, 2025

---

## Summary

The Intent Detection API is fully complete and functional. WebSocket message schemas have been created. This guide provides the remaining steps to integrate real-time intent detection into the WebSocket chat handler.

---

## Completed Work

✅ Intent Detection API endpoints (all working)
✅ WebSocket message schemas (`IntentSuggestionMessage`)
✅ DI configuration for `AdvancedIntentDetector`
✅ Imports added to `chat_handler.py`

---

## Remaining Implementation Steps

### Step 1: Add AdvancedIntentDetector to WebSocket Endpoint

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `chat_websocket_handler` (line 82)

Add `intent_detector` parameter:

```python
@router.websocket("/ws/chat/{conversation_id}")
@inject
async def chat_websocket_handler(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str = Query(..., description="JWT authentication token"),
    identity_provider: FromDishka[IdentityProvider] = None,
    user_gateway: FromDishka[UserCommandGateway] = None,
    session_store: FromDishka[SessionStore] = None,
    orchestration_service: FromDishka[AgentOrchestrationService] = None,
    intent_detector: FromDishka[AdvancedIntentDetector] = None,  # <- ADD THIS
):
```

### Step 2: Pass Intent Detector to Message Loop

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `chat_websocket_handler` (line 171)

Update the message loop call:

```python
# Main message loop
await _handle_message_loop(
    websocket=websocket,
    user=user,
    conversation_id=conversation_id,
    session_id=session_id,
    orchestration_service=orchestration_service,
    intent_detector=intent_detector,  # <- ADD THIS
)
```

### Step 3: Update Message Loop Signature

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `_handle_message_loop` (line 215)

Add intent_detector parameter:

```python
async def _handle_message_loop(
    websocket: WebSocket,
    user: User,
    conversation_id: UUID,
    session_id: str,
    orchestration_service: Optional[AgentOrchestrationService],
    intent_detector: Optional[AdvancedIntentDetector],  # <- ADD THIS
) -> None:
```

### Step 4: Pass Intent Detector to Chat Message Handler

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `_handle_message_loop` (line 252)

Update the chat message handler call:

```python
# Handle chat message
if message_type == WebSocketMessageType.MESSAGE:
    await _handle_chat_message(
        websocket=websocket,
        user=user,
        conversation_id=conversation_id,
        session_id=session_id,
        data=data,
        orchestration_service=orchestration_service,
        intent_detector=intent_detector,  # <- ADD THIS
    )
    continue
```

### Step 5: Update Chat Message Handler Signature

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `_handle_chat_message` (line 282)

Add intent_detector parameter:

```python
async def _handle_chat_message(
    websocket: WebSocket,
    user: User,
    conversation_id: UUID,
    session_id: str,
    data: Dict[str, Any],
    orchestration_service: Optional[AgentOrchestrationService],
    intent_detector: Optional[AdvancedIntentDetector],  # <- ADD THIS
) -> None:
```

### Step 6: Add Intent Detection Logic

**File**: `src/app/presentation/http/websocket/chat_handler.py`
**Function**: `_handle_chat_message` (after line 315, before sending typing indicator)

Add intent detection and suggestion sending:

```python
        logger.info(
            f"[WS Chat] User {user.id}: {message_request.content[:100]}... "
            f"(conversation={conversation_id})"
        )

        # Detect intent and send suggestions
        if intent_detector:
            try:
                # Detect intent from message
                intent = await intent_detector.detect_intent_while_typing(
                    partial_message=message_request.content,
                    conversation_context=None,  # TODO: Load from conversation_id
                )

                # Send intent suggestion to client
                intent_msg = IntentSuggestionMessage(
                    intent_type=intent.intent_type.value,
                    confidence=intent.confidence,
                    confidence_level=intent.confidence_level.value,
                    suggested_agent=intent.suggested_agent,
                    agent_reasoning=intent.reasoning,
                    extracted_entities=intent.extracted_entities or {},
                    autocomplete_suggestions=[],  # Could be populated from autocomplete service
                    is_high_confidence=intent.is_high_confidence,
                )
                await websocket.send_json(intent_msg.model_dump(mode="json"))

                logger.info(
                    f"[WS Chat] Sent intent suggestion: {intent.intent_type.value} "
                    f"(confidence={intent.confidence:.2f})"
                )

            except Exception as e:
                # Log but don't fail the message processing
                logger.warning(
                    f"[WS Chat] Intent detection failed: {e}",
                    exc_info=True,
                )

        # Send typing indicator (existing code continues...)
        typing_msg = TypingIndicatorMessage(
```

---

## Testing the Integration

### 1. Manual WebSocket Test

```python
# test_intent_websocket.py
import asyncio
import websockets
import json

async def test_intent_detection():
    uri = "ws://localhost:8000/api/v1/ws/chat/{conversation_id}?token={jwt_token}"

    async with websockets.connect(uri) as websocket:
        # Send message
        message = {
            "type": "message",
            "content": "Show me analytics for AAVE protocol"
        }
        await websocket.send(json.dumps(message))

        # Receive messages
        async for msg in websocket:
            data = json.loads(msg)
            if data["type"] == "intent_suggestion":
                print(f"Intent: {data['intent_type']}")
                print(f"Confidence: {data['confidence']}")
                print(f"Suggested Agent: {data['suggested_agent']}")
                print(f"Reasoning: {data['agent_reasoning']}")
                break

asyncio.run(test_intent_detection())
```

### 2. Integration Test

**Create**: `tests/integration/websocket/test_intent_detection.py`

```python
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_intent_detection_websocket(client: TestClient, auth_token: str):
    """Test intent detection via WebSocket."""
    conversation_id = uuid4()

    with client.websocket_connect(
        f"/api/v1/ws/chat/{conversation_id}?token={auth_token}"
    ) as websocket:
        # Send message
        websocket.send_json({
            "type": "message",
            "content": "Show me AAVE analytics"
        })

        # Receive intent suggestion
        data = websocket.receive_json()
        assert data["type"] == "intent_suggestion"
        assert data["intent_type"] == "SHOW_ANALYTICS"
        assert data["confidence"] > 0.7
        assert data["suggested_agent"] is not None
```

---

## Frontend Integration Example

```typescript
// React WebSocket Hook with Intent Detection
import { useEffect, useState } from 'react';

interface IntentSuggestion {
  intent_type: string;
  confidence: number;
  suggested_agent: string | null;
  agent_reasoning: string | null;
  extracted_entities: Record<string, any>;
  autocomplete_suggestions: string[];
  is_high_confidence: boolean;
}

export function useChatWithIntents(conversationId: string, token: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [intentSuggestion, setIntentSuggestion] = useState<IntentSuggestion | null>(null);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/api/v1/ws/chat/${conversationId}?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'intent_suggestion') {
        setIntentSuggestion(data);

        // Show intent badge in UI
        if (data.is_high_confidence) {
          showIntentBadge(data.intent_type, data.suggested_agent);
        }
      }
    };

    setSocket(ws);
    return () => ws.close();
  }, [conversationId, token]);

  const sendMessage = (content: string) => {
    socket?.send(JSON.stringify({
      type: 'message',
      content
    }));
  };

  return { sendMessage, intentSuggestion };
}
```

---

## Success Criteria

After implementing the above steps:

✅ WebSocket sends `IntentSuggestionMessage` before processing each user message
✅ Intent detection happens in < 200ms (logged in chat_handler)
✅ High confidence intents (>0.8) trigger UI suggestions
✅ Extracted entities are included in intent message
✅ Intent detection failures are logged but don't block message processing
✅ Integration tests pass

---

## Estimated Time

- **Step 1-5**: Adding DI parameters and function signatures: ~15 minutes
- **Step 6**: Intent detection logic integration: ~30 minutes
- **Testing**: Manual + integration tests: ~45 minutes
- **Frontend Integration**: React hooks and UI components: ~1-2 hours

**Total**: ~2-3 hours for complete integration

---

## Next Steps After Completion

1. Monitor intent detection performance in production
2. Add caching for frequently detected intents
3. Train/improve intent classification patterns based on usage
4. Add autocomplete suggestions population
5. Implement conversation context loading for better predictions

---

## Notes

- Intent detection is non-blocking - failures are logged but don't stop message processing
- Suggestions are sent BEFORE agent processing begins
- High confidence suggestions can auto-trigger agent selection in UI
- Intent caching (via Redis) reduces latency for repeated patterns
