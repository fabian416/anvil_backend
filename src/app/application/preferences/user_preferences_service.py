"""User preferences management service."""

from typing import Optional
from uuid import UUID

from app.domain.entities.user_preferences import (
    UserPreferences,
    SearchPreferences,
    NotificationPreferences,
    SavedSearch,
)


class UserPreferencesService:
    """
    Manage user preferences for search, notifications, and personalization.

    This service provides CRUD operations for user preferences and
    applies them to search results and notifications.
    """

    def __init__(self):
        """Initialize preferences service."""
        # TODO: Inject preferences repository once created
        pass

    async def get_user_preferences(self, user_id: UUID) -> UserPreferences:
        """
        Get user preferences, creating defaults if none exist.

        Args:
            user_id: User UUID

        Returns:
            User preferences
        """
        # TODO: Load from repository
        # For now, return defaults
        return UserPreferences(user_id=user_id)

    async def update_risk_tolerance(
        self, user_id: UUID, risk_tolerance: str
    ) -> UserPreferences:
        """
        Update user's risk tolerance.

        Args:
            user_id: User UUID
            risk_tolerance: conservative/moderate/aggressive

        Returns:
            Updated preferences
        """
        prefs = await self.get_user_preferences(user_id)
        prefs.update_risk_tolerance(risk_tolerance)

        # TODO: Save to repository
        return prefs

    async def update_chain_preferences(
        self, user_id: UUID, preferred_chains: list[str]
    ) -> UserPreferences:
        """Update user's preferred chains."""
        prefs = await self.get_user_preferences(user_id)
        prefs.preferred_chains = preferred_chains
        prefs.updated_at = prefs.updated_at  # Would auto-update in entity

        # TODO: Save
        return prefs

    async def update_notification_preferences(
        self, user_id: UUID, notification_settings: NotificationPreferences
    ) -> UserPreferences:
        """Update notification preferences."""
        prefs = await self.get_user_preferences(user_id)
        prefs.notification_settings = notification_settings

        # TODO: Save
        return prefs

    async def save_search(
        self, user_id: UUID, name: str, query: str, filters: dict
    ) -> SavedSearch:
        """Save a search preset."""
        prefs = await self.get_user_preferences(user_id)
        saved_search = prefs.search_settings.add_saved_search(name, query, filters)

        # TODO: Save preferences
        return saved_search

    async def delete_saved_search(
        self, user_id: UUID, search_id: UUID
    ) -> bool:
        """Delete a saved search."""
        prefs = await self.get_user_preferences(user_id)
        removed = prefs.search_settings.remove_saved_search(search_id)

        # TODO: Save preferences if removed
        return removed

    async def add_favorite_protocol(
        self, user_id: UUID, protocol_id: UUID
    ) -> UserPreferences:
        """Add protocol to favorites."""
        prefs = await self.get_user_preferences(user_id)
        prefs.add_favorite(protocol_id)

        # TODO: Save
        return prefs

    async def remove_favorite_protocol(
        self, user_id: UUID, protocol_id: UUID
    ) -> UserPreferences:
        """Remove protocol from favorites."""
        prefs = await self.get_user_preferences(user_id)
        prefs.remove_favorite(protocol_id)

        # TODO: Save
        return prefs

    async def exclude_protocol(
        self, user_id: UUID, protocol_id: UUID
    ) -> UserPreferences:
        """Exclude protocol from searches."""
        prefs = await self.get_user_preferences(user_id)
        prefs.exclude_protocol(protocol_id)

        # TODO: Save
        return prefs

    async def include_protocol(
        self, user_id: UUID, protocol_id: UUID
    ) -> UserPreferences:
        """Remove protocol from exclusion list."""
        prefs = await self.get_user_preferences(user_id)
        prefs.include_protocol(protocol_id)

        # TODO: Save
        return prefs
