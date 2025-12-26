"""
Admin Routes Aggregator.

All admin endpoints are mounted under /api/v1/admin/

Structure:
- /api/v1/admin/users - User management
- /api/v1/admin/llm - LLM configuration & management
- /api/v1/admin/agents - Agent configuration
- /api/v1/admin/stats - System statistics
- /api/v1/admin/retry - Retry management
- /api/v1/admin/distillation - Distillation management
- /api/v1/admin/projects - Project management
- /api/v1/admin/security - Security dashboard & OWASP scan results
- /api/v1/admin/chat - Chat analytics dashboard
"""

from fastapi import APIRouter


def create_admin_router() -> APIRouter:
    """Create the aggregated admin router."""
    router = APIRouter(
        prefix="/admin",
        tags=["Admin"],
    )

    # Import routers here to avoid circular imports
    from app.presentation.http.controllers.admin.user.router import create_users_router
    from app.presentation.http.controllers.admin.llm.router import create_llm_admin_router
    from app.presentation.http.controllers.admin.agent.router import create_admin_agent_router
    from app.presentation.http.controllers.admin.stats.router import create_admin_stats_router
    from app.presentation.http.controllers.admin.retry.router import router as retry_router
    from app.presentation.http.controllers.admin.distillation_router import router as distillation_admin_router
    from app.presentation.http.controllers.admin.distillation_validation_router import router as distillation_validation_router
    from app.presentation.http.controllers.admin.projects_router import router as projects_admin_router
    from app.presentation.http.controllers.telemetry.router import router as telemetry_router
    from app.presentation.http.controllers.admin.security_dashboard_router import router as security_dashboard_router
    from app.presentation.http.controllers.admin.chat_dashboard import router as chat_dashboard_router

    # Include all admin routers - they already have their own prefixes
    # But we need to strip /admin/ from their prefixes since we're adding it here
    router.include_router(create_users_router())  # /users
    router.include_router(create_llm_admin_router())  # /llm
    router.include_router(create_admin_agent_router())  # /agents
    router.include_router(create_admin_stats_router())  # /stats
    router.include_router(retry_router)  # /retry
    router.include_router(distillation_admin_router)  # /distillation
    router.include_router(distillation_validation_router)  # /distillation/validation
    router.include_router(projects_admin_router)  # /projects
    router.include_router(telemetry_router)  # /telemetry
    router.include_router(security_dashboard_router)  # /security
    router.include_router(chat_dashboard_router)  # /chat

    return router
