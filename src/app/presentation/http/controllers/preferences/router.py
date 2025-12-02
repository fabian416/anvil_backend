"""
User preferences router.
"""

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.schemas.preferences import (
    UserPreferencesResponse,
    UpdateRiskToleranceRequest,
    UpdateChainPreferencesRequest,
    UpdateNotificationPreferencesRequest,
    SaveSearchRequest,
    SavedSearchResponse,
)
from app.application.preferences.user_preferences_service import UserPreferencesService


def create_preferences_router() -> APIRouter:
    router = APIRouter(
        prefix="/users/me/preferences",
        tags=["preferences"],
    )

    @router.get(
        "",
        status_code=status.HTTP_200_OK,
        response_model=UserPreferencesResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_preferences(
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> UserPreferencesResponse:
        """
        Get user's complete preferences.

        Returns all preference categories:
        - Risk tolerance
        - Preferred chains
        - Search settings
        - Notification settings
        - Display settings
        """
        user = await current_user.get_current_user()
        prefs = await preferences_service.get_user_preferences(UUID(str(user.id)))

        return UserPreferencesResponse(
            user_id=str(prefs.user_id),
            risk_tolerance=prefs.risk_tolerance,
            preferred_chains=prefs.preferred_chains,
            preferred_categories=prefs.preferred_categories,
            excluded_protocols=[str(pid) for pid in prefs.excluded_protocols],
            favorite_protocols=[str(pid) for pid in prefs.favorite_protocols],
            search_settings={
                "default_similarity_threshold": prefs.search_settings.default_similarity_threshold,
                "default_risk_filter": prefs.search_settings.default_risk_filter,
                "search_history_enabled": prefs.search_settings.search_history_enabled,
            },
            notification_settings={
                "risk_alerts_enabled": prefs.notification_settings.risk_alerts_enabled,
                "push_enabled": prefs.notification_settings.push_enabled,
                "min_severity": prefs.notification_settings.min_severity,
            },
            default_currency=prefs.default_currency,
            theme=prefs.theme,
        )

    @router.put(
        "/risk-tolerance",
        status_code=status.HTTP_200_OK,
        response_model=UserPreferencesResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_risk_tolerance(
        request: UpdateRiskToleranceRequest,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> UserPreferencesResponse:
        """
        Update user's risk tolerance level.

        Args:
            risk_tolerance: conservative/moderate/aggressive
        """
        user = await current_user.get_current_user()
        prefs = await preferences_service.update_risk_tolerance(
            UUID(str(user.id)), request.risk_tolerance
        )

        return UserPreferencesResponse.from_entity(prefs)

    @router.put(
        "/chains",
        status_code=status.HTTP_200_OK,
        response_model=UserPreferencesResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_chain_preferences(
        request: UpdateChainPreferencesRequest,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> UserPreferencesResponse:
        """Update user's preferred blockchain chains."""
        user = await current_user.get_current_user()
        prefs = await preferences_service.update_chain_preferences(
            UUID(str(user.id)), request.preferred_chains
        )

        return UserPreferencesResponse.from_entity(prefs)

    @router.post(
        "/search/saved",
        status_code=status.HTTP_201_CREATED,
        response_model=SavedSearchResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def save_search(
        request: SaveSearchRequest,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> SavedSearchResponse:
        """Save a search preset for quick access."""
        user = await current_user.get_current_user()
        saved = await preferences_service.save_search(
            UUID(str(user.id)),
            request.name,
            request.query,
            request.filters,
        )

        return SavedSearchResponse(
            id=str(saved.id),
            name=saved.name,
            query=saved.query,
            filters=saved.filters,
            created_at=saved.created_at.isoformat(),
        )

    @router.delete(
        "/search/saved/{search_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def delete_saved_search(
        search_id: UUID,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> None:
        """Delete a saved search preset."""
        user = await current_user.get_current_user()
        await preferences_service.delete_saved_search(UUID(str(user.id)), search_id)

    @router.post(
        "/favorites/protocols/{protocol_id}",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def add_favorite_protocol(
        protocol_id: UUID,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> dict:
        """Add protocol to favorites."""
        user = await current_user.get_current_user()
        await preferences_service.add_favorite_protocol(UUID(str(user.id)), protocol_id)
        return {"success": True}

    @router.delete(
        "/favorites/protocols/{protocol_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def remove_favorite_protocol(
        protocol_id: UUID,
        current_user: FromDishka[CurrentUserService],
        preferences_service: FromDishka[UserPreferencesService],
    ) -> None:
        """Remove protocol from favorites."""
        user = await current_user.get_current_user()
        await preferences_service.remove_favorite_protocol(UUID(str(user.id)), protocol_id)

    return router
