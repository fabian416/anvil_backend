"""
Auth router for the hexagonal architecture.
"""

from fastapi import APIRouter
from app.presentation.http.controllers.auth.upgrade_to_admin import create_upgrade_to_admin_router
from app.presentation.http.controllers.auth.change_role import create_change_role_router


def create_auth_router() -> APIRouter:
    """
    Create the auth router with all auth-related endpoints.
    """
    router = APIRouter(prefix="/auth", tags=["auth"])
    
    # Include sub-routers
    router.include_router(create_upgrade_to_admin_router())
    router.include_router(create_change_role_router())
    
    return router
