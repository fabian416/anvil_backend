# WebSocket Handlers Quick Reference

## Endpoints

### Analytics WebSocket
```
ws://localhost:8000/api/v1/analytics/ws/{user_id}?token={jwt_token}
```

### Template Execution WebSocket
```
ws://localhost:8000/api/v1/templates/ws/{execution_id}?token={jwt_token}
```

## Analytics Messages

### Subscribe
```json
{"type": "subscribe", "subscriptions": ["metrics", "alerts"]}
```

### Request Snapshot
```json
{"type": "request_snapshot", "start_date": "2025-01-01T00:00:00Z"}
```

### Alerts Received
```json
{"type": "cost_alert", "severity": "warning", "message": "...", "data": {...}}
{"type": "performance_alert", "severity": "warning", "message": "...", "data": {...}}
{"type": "quality_alert", "severity": "info", "message": "...", "data": {...}}
```

## Template Execution Messages

### Control
```json
{"type": "pause"}
{"type": "resume"}
{"type": "cancel"}
```

### Events Received
```json
{"type": "step_started", "step_index": 0, "agent_name": "..."}
{"type": "step_progress", "step_index": 0, "progress": 0.5}
{"type": "step_completed", "step_result": {...}}
{"type": "execution_completed", "execution_state": {...}}
```

## File Locations

```
src/app/presentation/http/websocket/
├── analytics_handler.py          # Analytics handler
├── template_handler.py            # Template handler
└── connection_manager.py          # Shared manager

src/app/presentation/http/controllers/
├── analytics/websocket_router.py  # Analytics router
└── templates/websocket_router.py  # Template router

docs/websocket/
├── ANALYTICS_TEMPLATE_WEBSOCKETS.md  # Full documentation
├── IMPLEMENTATION_SUMMARY.md         # Implementation details
└── QUICK_REFERENCE.md                # This file
```

## JavaScript Client Example

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analytics/ws/user_123?token=jwt');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        subscriptions: ['metrics', 'alerts']
    }));
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log(msg.type, msg);
};
```

## Python Client Example

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/api/v1/templates/ws/execution_id?token=jwt"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            print(data['type'], data)

asyncio.run(connect())
```

## Testing

```bash
# Syntax check
python3 -m py_compile src/app/presentation/http/websocket/analytics_handler.py

# Connection stats
curl http://localhost:8000/api/v1/analytics/ws/stats

# Test connection with websocat
websocat "ws://localhost:8000/api/v1/analytics/ws/user_123?token=jwt"
```

## Common Patterns

### Analytics Dashboard

```javascript
// Connect and subscribe to all updates
ws.send(JSON.stringify({
    type: 'subscribe',
    subscriptions: ['metrics', 'alerts', 'performance', 'costs']
}));

// Request initial snapshot
ws.send(JSON.stringify({
    type: 'request_snapshot'
}));
```

### Template Execution Monitor

```javascript
// Receive connection with current state
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'connected') {
        console.log('Current state:', msg.execution_state);
    }

    if (msg.type === 'step_completed') {
        console.log('Step done:', msg.step_result);
    }
};

// Pause execution
ws.send(JSON.stringify({type: 'pause'}));
```

## Error Codes

- `unknown_type` - Unknown message type
- `invalid_subscription` - Invalid subscription type
- `invalid_date` - Invalid date format
- `snapshot_error` - Failed to generate snapshot
- `not_found` - Execution not found
- `invalid_state` - Invalid execution state
- `pause_error` - Failed to pause
- `resume_error` - Failed to resume
- `cancel_error` - Failed to cancel
- `internal_error` - Internal server error

## Alert Thresholds (Default)

```python
cost_threshold_usd = 10.0           # Alert when cost > $10
response_time_threshold_ms = 5000.0 # Alert when response > 5s
quality_threshold = 0.5             # Alert when quality < 0.5
```

## Statistics Endpoints

```bash
# Analytics stats
GET /api/v1/analytics/ws/stats

# Template stats
GET /api/v1/templates/ws/stats
```

Response:
```json
{
    "active_connections": 5,
    "active_users": 5,
    "total_connections": 127,
    "total_messages_sent": 3456
}
```
