"""
Search history router.
"""

from typing import Annotated, Optional
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security, Query

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.application.search import SearchHistoryService


def create_search_router() -> APIRouter:
    router = APIRouter(
        prefix="/user/search",
        tags=["search"],
    )

    @router.get(
        "/history",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_search_history(
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
        limit: int = Query(10, le=50),
        search_type: Optional[str] = Query(None),
    ) -> dict:
        """
        Get user's recent search history.

        Query Parameters:
        - limit: Maximum number of entries (default 10, max 50)
        - search_type: Optional filter by type (graphrag, protocol, token, general)

        Returns recent searches sorted by date (newest first).
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        history = await search_service.get_recent_searches(
            user_id,
            limit=limit,
            search_type=search_type,
        )

        return {
            "history": [
                {
                    "id": str(entry.id),
                    "query": entry.query,
                    "type": entry.search_type,
                    "results_count": entry.results_count,
                    "filters": entry.filters_applied,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in history
            ],
            "total": len(history),
        }

    @router.get(
        "/suggestions",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_search_suggestions(
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
        prefix: str = Query(..., min_length=1),
        limit: int = Query(5, le=10),
    ) -> dict:
        """
        Get search suggestions based on user's history.

        Query Parameters:
        - prefix: Search prefix to match (required, min 1 char)
        - limit: Maximum suggestions (default 5, max 10)

        Returns suggested queries starting with prefix.
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        suggestions = await search_service.get_search_suggestions(
            user_id,
            prefix=prefix,
            limit=limit,
        )

        return {
            "suggestions": suggestions,
            "prefix": prefix,
        }

    @router.get(
        "/popular",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_popular_queries(
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
        limit: int = Query(5, le=20),
        days: int = Query(30, le=90),
    ) -> dict:
        """
        Get user's most popular search queries.

        Query Parameters:
        - limit: Maximum queries (default 5, max 20)
        - days: Look back period in days (default 30, max 90)

        Returns most frequently searched queries.
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        popular = await search_service.get_popular_queries(
            user_id,
            limit=limit,
            days=days,
        )

        return {
            "popular_queries": popular,
            "period_days": days,
        }

    @router.delete(
        "/history/{search_id}",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def delete_search_entry(
        search_id: UUID,
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
    ) -> dict:
        """Delete a specific search entry."""
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        deleted = await search_service.delete_search(user_id, search_id)

        return {
            "success": deleted,
            "message": "Search deleted" if deleted else "Search not found",
        }

    @router.delete(
        "/history",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def clear_search_history(
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
        search_type: Optional[str] = Query(None),
    ) -> dict:
        """
        Clear user's search history.

        Query Parameters:
        - search_type: Optional - clear only specific type

        Clears all history if no type specified.
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        count = await search_service.clear_history(user_id, search_type)

        return {
            "success": True,
            "cleared_count": count,
            "message": f"Cleared {count} searches",
        }

    @router.get(
        "/analytics",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_search_analytics(
        current_user: FromDishka[CurrentUserService],
        search_service: FromDishka[SearchHistoryService],
        days: int = Query(30, le=90),
    ) -> dict:
        """
        Get search analytics for user.

        Query Parameters:
        - days: Look back period (default 30, max 90)

        Returns analytics including search counts, types, and patterns.
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        analytics = await search_service.get_search_analytics(user_id, days)

        return {
            "analytics": analytics,
            "period_days": days,
        }

    return router
