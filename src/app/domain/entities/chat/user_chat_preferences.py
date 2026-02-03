"""
User chat preferences entity.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, UTC


@dataclass
class UserChatPreferences:
    """
    User preferences for chat behavior and display.

    Manages response style, agent preferences, notifications,
    organization, privacy, and accessibility settings.
    """

    id: UUID
    user_id: UUID

    # Response style
    response_style: str = "detailed"  # "brief", "detailed", "technical", "executive"
    verbosity_level: int = 3  # 1-5
    include_sources: bool = True
    include_confidence_scores: bool = False

    # Agent preferences
    preferred_agents: Dict[str, List[str]] = field(default_factory=dict)
    # Query type → Agent preferences. e.g., {"risk": ["risk_analyzer"], "yield": ["yield_optimizer"]}
    agent_fallback_order: List[str] = field(default_factory=list)

    # Notification preferences
    mention_notifications: bool = True
    all_message_notifications: bool = False
    summary_notifications: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["email"])

    # Conversation organization
    auto_tagging: bool = True
    folder_structure: Dict[str, List[str]] = field(default_factory=dict)
    favorites: List[UUID] = field(default_factory=list)

    # Privacy settings
    conversation_retention_days: Optional[int] = None  # None = keep forever
    auto_delete_after_days: Optional[int] = None
    analytics_opt_in: bool = True

    # Accessibility
    screen_reader_optimized: bool = False
    keyboard_shortcuts_enabled: bool = True
    high_contrast_mode: bool = False
    font_size: str = "medium"  # "small", "medium", "large"

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create_default(cls, user_id: UUID) -> "UserChatPreferences":
        """
        Create default preferences for new user.

        Args:
            user_id: User identifier

        Returns:
            UserChatPreferences with default settings
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
        )

    def update_response_style(
        self, style: str, verbosity: Optional[int] = None
    ) -> None:
        """
        Update response style preferences.

        Args:
            style: Response style ("brief", "detailed", "technical", "executive")
            verbosity: Optional verbosity level 1-5
        """
        self.response_style = style
        if verbosity is not None:
            self.verbosity_level = max(1, min(5, verbosity))
        self.updated_at = datetime.now(UTC)

    def set_agent_preference(self, query_type: str, agents: List[str]) -> None:
        """
        Set preferred agents for a query type.

        Args:
            query_type: Type of query (e.g., "risk", "yield", "portfolio")
            agents: List of preferred agent names in priority order
        """
        self.preferred_agents[query_type] = agents
        self.updated_at = datetime.now(UTC)

    def add_to_favorites(self, conversation_id: UUID) -> None:
        """Add conversation to favorites."""
        if conversation_id not in self.favorites:
            self.favorites.append(conversation_id)
            self.updated_at = datetime.now(UTC)

    def remove_from_favorites(self, conversation_id: UUID) -> None:
        """Remove conversation from favorites."""
        if conversation_id in self.favorites:
            self.favorites.remove(conversation_id)
            self.updated_at = datetime.now(UTC)

    def update_privacy_settings(
        self,
        retention_days: Optional[int] = None,
        auto_delete_days: Optional[int] = None,
        analytics_opt_in: Optional[bool] = None,
    ) -> None:
        """
        Update privacy settings.

        Args:
            retention_days: Days to retain conversations
            auto_delete_days: Days before auto-deletion
            analytics_opt_in: Whether to participate in analytics
        """
        if retention_days is not None:
            self.conversation_retention_days = retention_days
        if auto_delete_days is not None:
            self.auto_delete_after_days = auto_delete_days
        if analytics_opt_in is not None:
            self.analytics_opt_in = analytics_opt_in
        self.updated_at = datetime.now(UTC)

    def update_accessibility_settings(
        self,
        screen_reader: Optional[bool] = None,
        keyboard_shortcuts: Optional[bool] = None,
        high_contrast: Optional[bool] = None,
        font_size: Optional[str] = None,
    ) -> None:
        """
        Update accessibility settings.

        Args:
            screen_reader: Enable screen reader optimization
            keyboard_shortcuts: Enable keyboard shortcuts
            high_contrast: Enable high contrast mode
            font_size: Font size preference
        """
        if screen_reader is not None:
            self.screen_reader_optimized = screen_reader
        if keyboard_shortcuts is not None:
            self.keyboard_shortcuts_enabled = keyboard_shortcuts
        if high_contrast is not None:
            self.high_contrast_mode = high_contrast
        if font_size is not None:
            self.font_size = font_size
        self.updated_at = datetime.now(UTC)

    def get_preferred_agent_for_query(self, query_type: str) -> Optional[str]:
        """
        Get preferred agent for query type.

        Args:
            query_type: Type of query

        Returns:
            Preferred agent name or None
        """
        agents = self.preferred_agents.get(query_type, [])
        return agents[0] if agents else None
