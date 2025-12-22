"""
User chat preferences repository adapter.

SQLAlchemy implementation of UserPreferencesRepository port.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select


from app.domain.preferences.ports.user_preferences_repository import UserPreferencesRepository
from app.domain.value_objects.chat.preferences import (
    UserChatPreferences,
    VerbosityLevel,
    ToneStyle,
    ResponseFormat,
    NotificationPreferences,
    DisplayPreferences,
)


class UserPreferencesRepositoryAdapter(UserPreferencesRepository):
    """
    SQLAlchemy adapter for user chat preferences.

    Implements persistence for user preferences using PostgreSQL.
    """

    def __init__(self, session: MainAsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_preferences(self, user_id: UUID) -> Optional[UserChatPreferences]:
        """
        Get user's chat preferences.

        Args:
            user_id: User identifier

        Returns:
            UserChatPreferences or None if not found
        """
        # Query preferences from database
        stmt = select(UserChatPreferencesModel).where(
            UserChatPreferencesModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Convert database model to domain value object
        return self._to_domain(model)

    async def save_preferences(self, preferences: UserChatPreferences) -> bool:
        """
        Save user's chat preferences.

        Args:
            preferences: User preferences to save

        Returns:
            True if saved successfully
        """
        try:
            # Check if preferences already exist
            stmt = select(UserChatPreferencesModel).where(
                UserChatPreferencesModel.user_id == preferences.user_id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing preferences
                self._update_model(existing, preferences)
            else:
                # Create new preferences
                model = self._to_model(preferences)
                self._session.add(model)

            await self._session.commit()
            return True

        except Exception:
            await self._session.rollback()
            return False

    async def update_preferences(self, preferences: UserChatPreferences) -> bool:
        """
        Update existing user preferences.

        Args:
            preferences: Updated preferences

        Returns:
            True if updated successfully
        """
        return await self.save_preferences(preferences)

    async def delete_preferences(self, user_id: UUID) -> bool:
        """
        Delete user's chat preferences.

        Args:
            user_id: User identifier

        Returns:
            True if deleted successfully
        """
        try:
            stmt = select(UserChatPreferencesModel).where(
                UserChatPreferencesModel.user_id == user_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.commit()
                return True

            return False

        except Exception:
            await self._session.rollback()
            return False

    def _to_domain(self, model: "UserChatPreferencesModel") -> UserChatPreferences:
        """
        Convert database model to domain value object.

        Args:
            model: Database model

        Returns:
            UserChatPreferences domain object
        """
        return UserChatPreferences(
            user_id=model.user_id,
            verbosity_level=VerbosityLevel(model.verbosity_level),
            tone_style=ToneStyle(model.tone_style),
            response_format=ResponseFormat(model.response_format),
            preferred_language=model.preferred_language,
            timezone=model.timezone,
            include_code_examples=model.include_code_examples,
            include_references=model.include_references,
            notifications=NotificationPreferences(
                conversation_updates=model.notification_conversation_updates,
                agent_responses=model.notification_agent_responses,
                daily_summary=model.notification_daily_summary,
                insight_alerts=model.notification_insight_alerts,
            ),
            display=DisplayPreferences(
                theme=model.display_theme,
                font_size=model.display_font_size,
                show_timestamps=model.display_show_timestamps,
                show_agent_names=model.display_show_agent_names,
                markdown_rendering=model.display_markdown_rendering,
            ),
            favorite_agents=model.favorite_agents or [],
            blocked_agents=model.blocked_agents or [],
            custom_instructions=model.custom_instructions,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, preferences: UserChatPreferences) -> "UserChatPreferencesModel":
        """
        Convert domain value object to database model.

        Args:
            preferences: Domain preferences

        Returns:
            Database model
        """
        return UserChatPreferencesModel(
            user_id=preferences.user_id,
            verbosity_level=preferences.verbosity_level.value,
            tone_style=preferences.tone_style.value,
            response_format=preferences.response_format.value,
            preferred_language=preferences.preferred_language,
            timezone=preferences.timezone,
            include_code_examples=preferences.include_code_examples,
            include_references=preferences.include_references,
            notification_conversation_updates=preferences.notifications.conversation_updates,
            notification_agent_responses=preferences.notifications.agent_responses,
            notification_daily_summary=preferences.notifications.daily_summary,
            notification_insight_alerts=preferences.notifications.insight_alerts,
            display_theme=preferences.display.theme,
            display_font_size=preferences.display.font_size,
            display_show_timestamps=preferences.display.show_timestamps,
            display_show_agent_names=preferences.display.show_agent_names,
            display_markdown_rendering=preferences.display.markdown_rendering,
            favorite_agents=preferences.favorite_agents,
            blocked_agents=preferences.blocked_agents,
            custom_instructions=preferences.custom_instructions,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at,
        )

    def _update_model(
        self,
        model: "UserChatPreferencesModel",
        preferences: UserChatPreferences,
    ) -> None:
        """
        Update database model from domain value object.

        Args:
            model: Database model to update
            preferences: Domain preferences
        """
        model.verbosity_level = preferences.verbosity_level.value
        model.tone_style = preferences.tone_style.value
        model.response_format = preferences.response_format.value
        model.preferred_language = preferences.preferred_language
        model.timezone = preferences.timezone
        model.include_code_examples = preferences.include_code_examples
        model.include_references = preferences.include_references
        model.notification_conversation_updates = preferences.notifications.conversation_updates
        model.notification_agent_responses = preferences.notifications.agent_responses
        model.notification_daily_summary = preferences.notifications.daily_summary
        model.notification_insight_alerts = preferences.notifications.insight_alerts
        model.display_theme = preferences.display.theme
        model.display_font_size = preferences.display.font_size
        model.display_show_timestamps = preferences.display.show_timestamps
        model.display_show_agent_names = preferences.display.show_agent_names
        model.display_markdown_rendering = preferences.display.markdown_rendering
        model.favorite_agents = preferences.favorite_agents
        model.blocked_agents = preferences.blocked_agents
        model.custom_instructions = preferences.custom_instructions
        model.updated_at = preferences.updated_at


# =============================================================================
# DATABASE MODEL
# =============================================================================


from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ARRAY, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.adapters.types import MainAsyncSession


@mapping_registry.mapped
class UserChatPreferencesModel:
    """
    SQLAlchemy model for user chat preferences.

    Maps to 'user_chat_preferences' table in PostgreSQL.
    """

    __tablename__ = "user_chat_preferences"

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)

    # Response preferences
    verbosity_level: Mapped[str] = mapped_column(String(20), nullable=False)
    tone_style: Mapped[str] = mapped_column(String(20), nullable=False)
    response_format: Mapped[str] = mapped_column(String(20), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    include_code_examples: Mapped[bool] = mapped_column(Boolean, nullable=False)
    include_references: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Notification preferences
    notification_conversation_updates: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notification_agent_responses: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notification_daily_summary: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notification_insight_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Display preferences
    display_theme: Mapped[str] = mapped_column(String(20), nullable=False)
    display_font_size: Mapped[int] = mapped_column(Integer, nullable=False)
    display_show_timestamps: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_show_agent_names: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_markdown_rendering: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Agent preferences
    favorite_agents: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    blocked_agents: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)

    # Custom instructions
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
