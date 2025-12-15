"""
User preferences repository port.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.chat.user_chat_preferences import UserChatPreferences


class UserPreferencesRepository(ABC):
    """
    Port for user preferences persistence.

    Domain-defined interface for storing and retrieving user chat preferences.
    """

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[UserChatPreferences]:
        """
        Get user preferences by user ID.

        Args:
            user_id: User identifier

        Returns:
            UserChatPreferences or None if not found
        """
        pass

    @abstractmethod
    async def get_by_id(self, preferences_id: UUID) -> Optional[UserChatPreferences]:
        """
        Get preferences by ID.

        Args:
            preferences_id: Preferences identifier

        Returns:
            UserChatPreferences or None if not found
        """
        pass

    @abstractmethod
    async def save(self, preferences: UserChatPreferences) -> UserChatPreferences:
        """
        Save or update user preferences.

        Args:
            preferences: UserChatPreferences to save

        Returns:
            Saved UserChatPreferences
        """
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Delete user preferences.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found
        """
        pass
