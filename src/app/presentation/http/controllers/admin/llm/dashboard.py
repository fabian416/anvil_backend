"""
Dashboard Admin Endpoints.

Aggregated endpoints optimized for dashboard rendering.
"""

from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class DashboardResponse(BaseModel):
    """Dashboard data response."""

    success: bool = True
    data: Dict[str, Any]


class ExportRequest(BaseModel):
    """Export request."""

    format: str  # csv, pdf
    data_type: str  # requests, costs, rankings
    period: str = "30d"
    filters: Optional[Dict[str, Any]] = None


# ============================================================================
# WEBSOCKET CONNECTIONS
# ============================================================================


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection broken, will be removed on next disconnect
                pass


# Global connection manager
manager = ConnectionManager()


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get(
    "",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_data(period: str = "24h"):
    """
    Get complete dashboard data.

    Optimized endpoint that returns all data needed
    for the dashboard in a single request:
    - System health summary
    - Provider status cards
    - Model rankings
    - Metrics summary
    - Cost summary
    - Recent requests
    - Active alerts

    **Query Parameters**:
    - `period`: 1h, 24h, 7d, 30d

    **Permission**: `llm.read`
    """
    # TODO: Implement GetDashboardData query
    from app.application.llm.queries.get_dashboard_data import GetDashboardData

    query = GetDashboardData()
    data = await query.execute(period=period)

    return DashboardResponse(
        data={
            "system_health": data.system_health,
            "providers": data.providers,
            "top_models": data.top_models[:5],  # Top 5 for dashboard
            "metrics_summary": data.metrics_summary,
            "cost_summary": data.cost_summary,
            "recent_requests": data.recent_requests[:10],  # Last 10 requests
            "active_alerts": data.active_alerts,
            "last_updated": datetime.utcnow().isoformat(),
        }
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Sends real-time updates to connected clients:
    - New requests
    - Status changes
    - Alerts
    - Metric updates

    **Usage**:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/admin/llm/dashboard/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Update UI
    };
    ```
    """
    await manager.connect(websocket)

    try:
        # Send initial status
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and send updates
        while True:
            # Wait for client messages (ping/pong)
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=30.0
                )

                # Echo back (for ping/pong)
                if message == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

            except asyncio.TimeoutError:
                # Send heartbeat every 30 seconds
                await websocket.send_json(
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post(
    "/export",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def export_data(request: ExportRequest):
    """
    Export dashboard data.

    Generates downloadable exports in CSV or PDF format.

    **Request Body**:
    ```json
    {
      "format": "csv",
      "data_type": "requests",
      "period": "30d",
      "filters": {
        "provider": "vertex_ai",
        "agent_type": "swap_agent"
      }
    }
    ```

    **Permission**: `llm.read`
    """
    # TODO: Implement export functionality
    # Generate CSV or PDF based on request

    return DashboardResponse(
        data={
            "export_id": "export-uuid",
            "format": request.format,
            "data_type": request.data_type,
            "status": "generating",
            "download_url": f"/admin/llm/dashboard/export/export-uuid/download",
            "expires_at": (
                datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            ),
        }
    )


@router.get(
    "/health",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def dashboard_health():
    """
    Dashboard health check.

    Quick health check endpoint for monitoring.

    **Permission**: None (public)
    """
    return DashboardResponse(
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": "healthy",
                "cache": "healthy",
                "websocket": "healthy",
            },
        }
    )


# ============================================================================
# HELPER FUNCTIONS FOR WEBSOCKET BROADCASTING
# ============================================================================


async def broadcast_request_update(request_data: Dict[str, Any]):
    """
    Broadcast new request to all connected clients.

    Call this from orchestrator after each request.
    """
    await manager.broadcast(
        {
            "type": "request_update",
            "data": request_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def broadcast_alert(alert_data: Dict[str, Any]):
    """
    Broadcast alert to all connected clients.

    Call this when budget thresholds are reached or circuit breakers trip.
    """
    await manager.broadcast(
        {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def broadcast_metrics_update(metrics_data: Dict[str, Any]):
    """
    Broadcast metrics update to all connected clients.

    Call this periodically (e.g., every minute) to update metrics.
    """
    await manager.broadcast(
        {
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
