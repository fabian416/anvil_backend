"""
Admin LLM Orchestration Router.

Provides admin endpoints for managing LLM orchestration system.
"""

from fastapi import APIRouter
from fastapi_error_map import ErrorAwareRouter

from .dashboard import router as dashboard_router
from .providers import router as providers_router
from .models import router as models_router
from .rankings import router as rankings_router
from .telemetry import router as telemetry_router
from .budgets import router as budgets_router
from .circuit_breakers import router as circuit_breakers_router

# Create main admin LLM router
router = ErrorAwareRouter(
    prefix="/admin/llm",
    tags=["Admin - LLM Orchestration"],
)

# Include sub-routers
router.include_router(dashboard_router, prefix="/dashboard", tags=["Admin - Dashboard"])
router.include_router(providers_router, prefix="/providers", tags=["Admin - LLM Providers"])
router.include_router(models_router, prefix="/models", tags=["Admin - LLM Models"])
router.include_router(rankings_router, prefix="/rankings", tags=["Admin - LLM Rankings"])
router.include_router(telemetry_router, prefix="/telemetry", tags=["Admin - LLM Telemetry"])
router.include_router(budgets_router, prefix="/budgets", tags=["Admin - LLM Budgets"])
router.include_router(circuit_breakers_router, prefix="/circuit-breakers", tags=["Admin - Circuit Breakers"])
