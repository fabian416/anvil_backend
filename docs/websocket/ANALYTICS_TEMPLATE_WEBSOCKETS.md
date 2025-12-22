# Analytics and Template Execution WebSocket Handlers

This document provides comprehensive documentation for the analytics and template execution WebSocket handlers.

## Overview

Two new WebSocket handlers have been implemented following the hexagonal architecture pattern:

1. **Analytics WebSocket Handler** (`analytics_handler.py`)
   - Real-time analytics metrics streaming
   - Performance alerts
   - Cost threshold notifications
   - Dashboard data updates

2. **Template Execution WebSocket Handler** (`template_handler.py`)
   - Step-by-step execution progress
   - Real-time step results
   - Pause/resume controls
   - Completion notifications

## File Locations

```
src/app/presentation/http/websocket/
├── analytics_handler.py          # Analytics WebSocket handler
├── template_handler.py            # Template execution WebSocket handler
└── connection_manager.py          # Shared connection manager

src/app/presentation/http/controllers/
├── analytics/websocket_router.py  # Analytics router example
└── templates/websocket_router.py  # Template router example
```

## Architecture

Both handlers follow the established hexagonal architecture patterns:

- **Presentation Layer**: WebSocket handlers manage HTTP/WebSocket connections
- **Application Layer**: Uses repositories (ports) for data access
- **Infrastructure Layer**: JWT authentication, connection management
- **Dependency Injection**: Dishka for DI (not FastAPI's built-in)

## Analytics WebSocket Handler

### Endpoint

```
/ws/analytics/{user_id}?token=<jwt_token>
```

### Features

- Real-time metrics updates
- Performance alerts (response time thresholds)
- Cost alerts (spend thresholds)
- Quality alerts (quality score thresholds)
- Analytics snapshots on demand
- Subscription-based updates

### Client Messages

#### Subscribe to Updates

```json
{
    "type": "subscribe",
    "subscriptions": ["metrics", "alerts", "performance", "costs", "quality"]
}
```

Subscription types:
- `metrics`: Real-time metrics updates
- `alerts`: All alert types
- `performance`: Performance-related alerts only
- `costs`: Cost-related alerts only
- `quality`: Quality-related alerts only

#### Unsubscribe

```json
{
    "type": "unsubscribe",
    "subscriptions": ["metrics"]
}
```

#### Request Snapshot

```json
{
    "type": "request_snapshot",
    "start_date": "2025-01-01T00:00:00Z",  // optional, defaults to 30 days ago
    "end_date": "2025-12-16T00:00:00Z"      // optional, defaults to now
}
```

#### Heartbeat

```json
{
    "type": "ping"
}
```

### Server Messages

#### Metrics Update

```json
{
    "type": "metrics_update",
    "data": {
        "id": "uuid",
        "conversation_id": "uuid",
        "user_id": "uuid",
        "message_count": 25,
        "avg_response_time_ms": 1234.5,
        "total_cost_usd": 5.23,
        "quality_score": 0.85,
        "agent_usage": {
            "research_agent": {
                "invocations": 10,
                "avg_time_ms": 2500.0,
                "success_rate": 0.95
            }
        }
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Cost Alert

```json
{
    "type": "cost_alert",
    "severity": "warning",
    "message": "Conversation cost ($12.50) exceeded threshold ($10.00)",
    "data": {
        "conversation_id": "uuid",
        "total_cost": 12.50,
        "threshold": 10.00,
        "cost_by_agent": {
            "gpt4_agent": 8.50,
            "claude_agent": 4.00
        }
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Performance Alert

```json
{
    "type": "performance_alert",
    "severity": "warning",
    "message": "P95 response time (5500ms) exceeded threshold (5000ms)",
    "data": {
        "conversation_id": "uuid",
        "p95_response_time_ms": 5500.0,
        "avg_response_time_ms": 2300.0,
        "threshold": 5000.0
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Quality Alert

```json
{
    "type": "quality_alert",
    "severity": "info",
    "message": "Quality score (0.45) below threshold (0.50)",
    "data": {
        "conversation_id": "uuid",
        "quality_score": 0.45,
        "sentiment_score": 0.60,
        "satisfaction_score": 0.55,
        "threshold": 0.50
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Snapshot Response

```json
{
    "type": "snapshot",
    "data": {
        "aggregate": {
            "total_conversations": 150,
            "total_messages": 3500,
            "total_cost_usd": 245.50,
            "avg_messages_per_conversation": 23.3,
            "avg_response_time_ms": 1850.0,
            "most_used_agent": "research_agent"
        },
        "daily": [
            {
                "date": "2025-12-15",
                "conversation_count": 5,
                "message_count": 125,
                "total_cost_usd": 15.75
            }
        ],
        "agent_stats": {
            "research_agent": {
                "total_invocations": 450,
                "avg_execution_time_ms": 2500.0,
                "avg_success_rate": 0.95
            }
        },
        "cost_breakdown": {
            "research_agent": 125.50,
            "analysis_agent": 120.00
        },
        "date_range": {
            "start": "2025-11-16T00:00:00Z",
            "end": "2025-12-16T00:00:00Z"
        }
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

### Configuration

Alert thresholds can be configured in the handler initialization:

```python
handler = AnalyticsWebSocketHandler(
    analytics_repository=analytics_repo,
    jwt_processor=jwt_processor,
)

# Customize thresholds
handler.cost_threshold_usd = 15.0  # Alert when cost > $15
handler.response_time_threshold_ms = 3000.0  # Alert when response > 3s
handler.quality_threshold = 0.6  # Alert when quality < 0.6
```

## Template Execution WebSocket Handler

### Endpoint

```
/ws/template/{execution_id}?token=<jwt_token>
```

### Features

- Real-time step execution updates
- Progress tracking
- Step results streaming
- Pause/resume controls
- Cancel execution
- Multi-client support (all subscribers see same updates)

### Client Messages

#### Pause Execution

```json
{
    "type": "pause"
}
```

#### Resume Execution

```json
{
    "type": "resume"
}
```

#### Cancel Execution

```json
{
    "type": "cancel"
}
```

#### Heartbeat

```json
{
    "type": "ping"
}
```

### Server Messages

#### Connection Established

```json
{
    "type": "connected",
    "message": "Connected to template execution stream",
    "execution_id": "uuid",
    "execution_state": {
        "id": "uuid",
        "template_id": "uuid",
        "conversation_id": "uuid",
        "user_id": "uuid",
        "status": "in_progress",
        "current_step_index": 2,
        "completion_rate": 0.66,
        "step_results": [...]
    },
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Step Started

```json
{
    "type": "step_started",
    "step_index": 0,
    "agent_name": "research_agent",
    "description": "Research market trends for Q4 2025",
    "timestamp": "2025-12-16T12:00:00Z"
}
```

#### Step Progress (Optional)

```json
{
    "type": "step_progress",
    "step_index": 0,
    "progress": 0.5,  // 0.0 to 1.0
    "message": "Processing 500/1000 records...",
    "timestamp": "2025-12-16T12:00:15Z"
}
```

#### Step Completed

```json
{
    "type": "step_completed",
    "step_result": {
        "step_index": 0,
        "agent_name": "research_agent",
        "response": "Market analysis shows strong growth in...",
        "execution_time_seconds": 45,
        "success": true,
        "error_message": null,
        "metadata": {
            "data_points_analyzed": 1000,
            "confidence_score": 0.92
        }
    },
    "execution_state": {
        "id": "uuid",
        "status": "in_progress",
        "current_step_index": 1,
        "completion_rate": 0.33,
        "step_results": [...]
    },
    "timestamp": "2025-12-16T12:00:45Z"
}
```

#### Step Failed

```json
{
    "type": "step_failed",
    "step_index": 2,
    "agent_name": "analysis_agent",
    "error_message": "API rate limit exceeded. Retry after 60 seconds.",
    "timestamp": "2025-12-16T12:02:30Z"
}
```

#### Execution Paused

```json
{
    "type": "execution_paused",
    "message": "Execution paused by user",
    "execution_state": {
        "id": "uuid",
        "status": "paused",
        "current_step_index": 2,
        "paused_at": "2025-12-16T12:03:00Z"
    },
    "timestamp": "2025-12-16T12:03:00Z"
}
```

#### Execution Resumed

```json
{
    "type": "execution_resumed",
    "message": "Execution resumed by user",
    "execution_state": {
        "id": "uuid",
        "status": "in_progress",
        "current_step_index": 2,
        "paused_at": null
    },
    "timestamp": "2025-12-16T12:04:00Z"
}
```

#### Execution Completed

```json
{
    "type": "execution_completed",
    "message": "Template execution completed successfully",
    "execution_state": {
        "id": "uuid",
        "status": "completed",
        "completion_rate": 1.0,
        "execution_time_seconds": 180,
        "completed_at": "2025-12-16T12:05:00Z",
        "step_results": [
            {
                "step_index": 0,
                "agent_name": "research_agent",
                "response": "...",
                "success": true
            },
            {
                "step_index": 1,
                "agent_name": "analysis_agent",
                "response": "...",
                "success": true
            }
        ]
    },
    "timestamp": "2025-12-16T12:05:00Z"
}
```

#### Execution Failed

```json
{
    "type": "execution_failed",
    "message": "Template execution failed",
    "error_message": "Critical error in step 2: Database connection lost",
    "execution_state": {
        "id": "uuid",
        "status": "failed",
        "current_step_index": 2,
        "completed_at": "2025-12-16T12:03:00Z"
    },
    "timestamp": "2025-12-16T12:03:00Z"
}
```

#### Execution Cancelled

```json
{
    "type": "execution_cancelled",
    "message": "Execution cancelled by user",
    "execution_state": {
        "id": "uuid",
        "status": "failed",
        "completed_at": "2025-12-16T12:03:30Z"
    },
    "timestamp": "2025-12-16T12:03:30Z"
}
```

## Integration with Dishka

### Provider Setup

Create a provider for the WebSocket handlers:

```python
from dishka import Provider, Scope, provide
from app.presentation.http.websocket.analytics_handler import (
    AnalyticsWebSocketHandler,
)
from app.presentation.http.websocket.template_handler import (
    TemplateExecutionWebSocketHandler,
)


class WebSocketProvider(Provider):
    scope = Scope.APP

    @provide
    def provide_analytics_handler(
        self,
        analytics_repo: AnalyticsRepository,
        jwt_processor: JwtAccessTokenProcessor,
    ) -> AnalyticsWebSocketHandler:
        return AnalyticsWebSocketHandler(
            analytics_repository=analytics_repo,
            jwt_processor=jwt_processor,
        )

    @provide
    def provide_template_execution_handler(
        self,
        execution_repo: TemplateExecutionRepository,
        jwt_processor: JwtAccessTokenProcessor,
    ) -> TemplateExecutionWebSocketHandler:
        return TemplateExecutionWebSocketHandler(
            execution_repository=execution_repo,
            jwt_processor=jwt_processor,
        )
```

### Router Registration

Add routers to your FastAPI application:

```python
from app.presentation.http.controllers.analytics.websocket_router import (
    create_analytics_websocket_router,
)
from app.presentation.http.controllers.templates.websocket_router import (
    create_template_execution_websocket_router,
)

# Create routers
analytics_ws_router = create_analytics_websocket_router()
template_ws_router = create_template_execution_websocket_router()

# Register with FastAPI
app.include_router(analytics_ws_router, prefix="/api/v1")
app.include_router(template_ws_router, prefix="/api/v1")
```

## Usage Examples

### JavaScript/TypeScript Client (Analytics)

```typescript
class AnalyticsWebSocketClient {
    private ws: WebSocket;

    connect(userId: string, token: string) {
        this.ws = new WebSocket(
            `ws://localhost:8000/api/v1/analytics/ws/${userId}?token=${token}`
        );

        this.ws.onopen = () => {
            console.log('Connected to analytics stream');

            // Subscribe to updates
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                subscriptions: ['metrics', 'alerts']
            }));
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'metrics_update':
                    this.handleMetricsUpdate(message.data);
                    break;
                case 'cost_alert':
                    this.handleCostAlert(message);
                    break;
                case 'performance_alert':
                    this.handlePerformanceAlert(message);
                    break;
                case 'snapshot':
                    this.handleSnapshot(message.data);
                    break;
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from analytics stream');
        };
    }

    requestSnapshot(startDate?: string, endDate?: string) {
        this.ws.send(JSON.stringify({
            type: 'request_snapshot',
            start_date: startDate,
            end_date: endDate
        }));
    }

    disconnect() {
        this.ws.close();
    }

    private handleMetricsUpdate(data: any) {
        // Update dashboard with new metrics
        console.log('Metrics updated:', data);
    }

    private handleCostAlert(alert: any) {
        // Show alert notification
        console.warn('Cost alert:', alert.message);
    }

    private handlePerformanceAlert(alert: any) {
        // Show performance warning
        console.warn('Performance alert:', alert.message);
    }

    private handleSnapshot(data: any) {
        // Update dashboard with snapshot data
        console.log('Snapshot received:', data);
    }
}
```

### Python Client (Template Execution)

```python
import asyncio
import websockets
import json

async def monitor_template_execution(execution_id: str, token: str):
    uri = f"ws://localhost:8000/api/v1/templates/ws/{execution_id}?token={token}"

    async with websockets.connect(uri) as websocket:
        print("Connected to template execution stream")

        # Receive connection message
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Current state: {data['execution_state']['status']}")

        # Monitor execution
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data['type'] == 'step_started':
                print(f"Step {data['step_index']}: {data['agent_name']} started")

            elif data['type'] == 'step_progress':
                progress = data['progress'] * 100
                print(f"Step {data['step_index']}: {progress:.0f}% - {data['message']}")

            elif data['type'] == 'step_completed':
                result = data['step_result']
                print(f"Step {result['step_index']}: Completed in {result['execution_time_seconds']}s")
                print(f"Response: {result['response'][:100]}...")

            elif data['type'] == 'step_failed':
                print(f"Step {data['step_index']}: Failed - {data['error_message']}")

            elif data['type'] == 'execution_completed':
                print("Execution completed successfully!")
                break

            elif data['type'] == 'execution_failed':
                print(f"Execution failed: {data['error_message']}")
                break

# Usage
asyncio.run(monitor_template_execution(
    execution_id="550e8400-e29b-41d4-a716-446655440000",
    token="your_jwt_token"
))
```

## Error Handling

Both handlers implement comprehensive error handling:

### Connection Errors

- Invalid/expired JWT: Connection closed with `WS_1008_POLICY_VIOLATION`
- Access denied: Connection closed with `WS_1008_POLICY_VIOLATION`
- Internal errors: Connection closed with `WS_1011_INTERNAL_ERROR`

### Runtime Errors

All runtime errors are sent as error messages:

```json
{
    "type": "error",
    "error": "Error description",
    "code": "error_code"
}
```

Error codes:
- `unknown_type`: Unknown message type
- `invalid_subscription`: Invalid subscription type
- `invalid_date`: Invalid date format
- `snapshot_error`: Failed to generate snapshot
- `not_found`: Execution not found
- `invalid_state`: Invalid execution state for operation
- `pause_error`, `resume_error`, `cancel_error`: Operation failed
- `internal_error`: Internal server error

## Performance Considerations

1. **Connection Limits**: Each handler uses a shared `ConnectionManager` for efficient connection tracking
2. **Broadcasting**: Messages are only sent to subscribed users
3. **Memory**: Subscriptions are cleaned up on disconnect
4. **Scalability**: For production, consider using Redis pub/sub for multi-instance deployments

## Testing

### Unit Tests

```python
import pytest
from app.presentation.http.websocket.analytics_handler import (
    AnalyticsWebSocketHandler,
)

@pytest.mark.asyncio
async def test_analytics_handler_authentication(
    analytics_repo,
    jwt_processor,
):
    handler = AnalyticsWebSocketHandler(
        analytics_repository=analytics_repo,
        jwt_processor=jwt_processor,
    )

    # Test valid token
    user = await handler.authenticate_user("valid_token")
    assert user is not None

    # Test invalid token
    user = await handler.authenticate_user("invalid_token")
    assert user is None
```

### Integration Tests

```python
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

def test_analytics_websocket_connection(client: TestClient, auth_token: str):
    with client.websocket_connect(
        f"/api/v1/analytics/ws/user_123?token={auth_token}"
    ) as websocket:
        # Receive connection message
        data = websocket.receive_json()
        assert data['type'] == 'connected'

        # Subscribe
        websocket.send_json({
            'type': 'subscribe',
            'subscriptions': ['metrics']
        })

        # Receive subscription confirmation
        data = websocket.receive_json()
        assert data['type'] == 'subscribed'
```

## Monitoring

Get connection statistics:

```bash
# Analytics WebSocket stats
curl http://localhost:8000/api/v1/analytics/ws/stats

# Template execution WebSocket stats
curl http://localhost:8000/api/v1/templates/ws/stats
```

Response:

```json
{
    "active_connections": 5,
    "total_subscriptions": 15,
    "users_with_subscriptions": 5,
    "connection_manager_stats": {
        "active_connections": 5,
        "active_users": 5,
        "total_connections": 127,
        "total_messages_sent": 3456
    }
}
```

## Security

1. **Authentication**: All connections require valid JWT token
2. **Authorization**: Users can only access their own data
3. **Connection Limits**: Consider implementing rate limiting
4. **Token Expiry**: Connections are closed when tokens expire
5. **Input Validation**: All client messages are validated

## Future Enhancements

- Redis pub/sub for multi-instance scaling
- Rate limiting per user
- Message history/replay
- Compression for large messages
- Binary protocol support (e.g., MessagePack)
- Connection pooling
- Automatic reconnection with backoff
