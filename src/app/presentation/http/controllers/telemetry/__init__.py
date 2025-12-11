"""
Telemetry API Endpoints.

Provides endpoints for:
- API telemetry metrics
- Prometheus metrics export
- Distributed tracing
- Health and performance monitoring
"""

from app.presentation.http.controllers.telemetry.router import router as telemetry_router

__all__ = ["telemetry_router"]
