"""
Authentication context utilities.

Provides helper functions for getting current user information in FastAPI endpoints.
"""

from fastapi import Security
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService


@inject
async def get_current_user_id(
    current_user_service: FromDishka[CurrentUserService],
    authorization: str = Security(bearer_scheme),
) -> int:
    """
    Get current authenticated user ID.

    FastAPI dependency that extracts the current user ID from the authenticated session.

    Args:
        current_user_service: Injected current user service
        authorization: Bearer token from request

    Returns:
        Current user ID as integer

    Raises:
        AuthenticationError: If user is not authenticated
        AuthorizationError: If user is not found
    """
    user = await current_user_service.get_current_user()
    return user.id_.value
