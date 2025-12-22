"""
Template execution WebSocket router.

Provides WebSocket endpoints for real-time template execution streaming.
"""

from fastapi import APIRouter, WebSocket, Query
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.websocket.template_handler import (
    TemplateExecutionWebSocketHandler,
)


def create_template_execution_websocket_router() -> APIRouter:
    """
    Create WebSocket router for template execution.

    Returns:
        APIRouter with WebSocket endpoint
    """
    router = APIRouter(
        prefix="/templates",
        tags=["template-websocket"],
    )

    @router.websocket("/ws/{execution_id}")
    @inject
    async def template_execution_websocket(
        websocket: WebSocket,
        execution_id: str,
        token: str = Query(..., description="JWT authentication token"),
        handler: FromDishka[TemplateExecutionWebSocketHandler] = None,
    ):
        """
        WebSocket endpoint for real-time template execution streaming.

        Connect to receive step-by-step progress updates, results, and control execution.

        Path Parameters:
        - execution_id: Template execution identifier (UUID)

        Query Parameters:
        - token: JWT authentication token

        Client Messages:
        ```json
        // Pause execution
        {
            "type": "pause"
        }

        // Resume paused execution
        {
            "type": "resume"
        }

        // Cancel execution
        {
            "type": "cancel"
        }

        // Heartbeat
        {
            "type": "ping"
        }
        ```

        Server Messages:
        ```json
        // Step started
        {
            "type": "step_started",
            "step_index": 0,
            "agent_name": "research_agent",
            "description": "Research market trends",
            "timestamp": "2025-12-16T12:00:00Z"
        }

        // Step progress (optional)
        {
            "type": "step_progress",
            "step_index": 0,
            "progress": 0.5,  // 0.0 to 1.0
            "message": "Processing data...",
            "timestamp": "2025-12-16T12:00:05Z"
        }

        // Step completed
        {
            "type": "step_completed",
            "step_result": {
                "step_index": 0,
                "agent_name": "research_agent",
                "response": "Research findings...",
                "execution_time_seconds": 45,
                "success": true,
                "metadata": {...}
            },
            "execution_state": {
                "id": "uuid",
                "status": "in_progress",
                "current_step_index": 1,
                "completion_rate": 0.33,
                ...
            },
            "timestamp": "2025-12-16T12:00:45Z"
        }

        // Step failed
        {
            "type": "step_failed",
            "step_index": 0,
            "agent_name": "research_agent",
            "error_message": "API timeout",
            "timestamp": "2025-12-16T12:00:45Z"
        }

        // Execution paused
        {
            "type": "execution_paused",
            "message": "Execution paused by user",
            "execution_state": {...},
            "timestamp": "2025-12-16T12:01:00Z"
        }

        // Execution resumed
        {
            "type": "execution_resumed",
            "message": "Execution resumed by user",
            "execution_state": {...},
            "timestamp": "2025-12-16T12:02:00Z"
        }

        // Execution completed
        {
            "type": "execution_completed",
            "message": "Template execution completed successfully",
            "execution_state": {
                "id": "uuid",
                "status": "completed",
                "completion_rate": 1.0,
                "execution_time_seconds": 180,
                "step_results": [...]
            },
            "timestamp": "2025-12-16T12:03:00Z"
        }

        // Execution failed
        {
            "type": "execution_failed",
            "message": "Template execution failed",
            "error_message": "Critical error in step 2",
            "execution_state": {...},
            "timestamp": "2025-12-16T12:03:00Z"
        }

        // Execution cancelled
        {
            "type": "execution_cancelled",
            "message": "Execution cancelled by user",
            "execution_state": {...},
            "timestamp": "2025-12-16T12:03:00Z"
        }
        ```

        Execution Flow:
        1. Connect to WebSocket with execution_id
        2. Receive "connected" message with current execution state
        3. Receive "step_started" when each step begins
        4. Optionally receive "step_progress" updates during step execution
        5. Receive "step_completed" or "step_failed" when step finishes
        6. Repeat steps 3-5 for all template steps
        7. Receive "execution_completed" or "execution_failed" when done
        8. Can send "pause", "resume", or "cancel" at any time

        Notes:
        - User must own the execution to connect
        - Multiple clients can connect to same execution
        - All connected clients receive the same updates
        - Execution continues even if all clients disconnect
        """
        await handler.handle_connection(websocket, execution_id, token)

    @router.get("/ws/stats")
    @inject
    async def get_template_execution_websocket_stats(
        handler: FromDishka[TemplateExecutionWebSocketHandler] = None,
    ):
        """
        Get template execution WebSocket connection statistics.

        Returns:
            Connection and execution subscription statistics
        """
        return handler.get_statistics()

    return router
