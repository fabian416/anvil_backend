"""
User chat preferences service.

Manages user preference updates through natural language commands.
"""

import logging
import re
from typing import Optional, List
from uuid import UUID

from app.domain.entities.chat.user_chat_preferences import UserChatPreferences
from app.domain.ports.user_preferences_repository import UserPreferencesRepository

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """
    Service for managing user chat preferences through natural language.

    Instead of PUT /api/v1/preferences, users say:
    - "Make responses more brief"
    - "Always use Risk Analyzer for risk questions"
    - "Enable high contrast mode"
    """

    def __init__(self, preferences_repository: UserPreferencesRepository):
        """
        Initialize preferences service.

        Args:
            preferences_repository: Repository for user preferences
        """
        self._repository = preferences_repository

    async def process_preference_command(
        self,
        user_id: UUID,
        command: str,
    ) -> tuple[bool, str]:
        """
        Process natural language preference update command.

        Args:
            user_id: User identifier
            command: Natural language command (e.g., "make responses brief")

        Returns:
            Tuple of (success, response_message)
        """
        # Load user preferences
        preferences = await self._repository.get_by_user_id(user_id)
        if not preferences:
            preferences = UserChatPreferences.create_default(user_id)

        # Detect and process command
        command_lower = command.lower()

        # Response style commands
        if any(keyword in command_lower for keyword in ["brief", "concise", "short"]):
            return await self._update_response_style(
                preferences, "brief", "I'll keep my responses brief and to the point."
            )
        elif any(keyword in command_lower for keyword in ["detailed", "verbose", "thorough"]):
            return await self._update_response_style(
                preferences, "detailed", "I'll provide detailed, comprehensive responses."
            )
        elif "technical" in command_lower:
            return await self._update_response_style(
                preferences, "technical", "I'll use technical language and include implementation details."
            )
        elif "executive" in command_lower:
            return await self._update_response_style(
                preferences, "executive", "I'll provide executive summaries focused on key insights."
            )

        # Verbosity level commands
        elif "verbosity" in command_lower:
            level = self._extract_number(command, default=3)
            preferences.update_response_style(preferences.response_style, level)
            await self._repository.save(preferences)
            return True, f"Verbosity level set to {level}/5."

        # Agent preference commands
        elif "always use" in command_lower or "prefer" in command_lower:
            return await self._process_agent_preference(preferences, command)

        # Privacy commands
        elif "auto-delete" in command_lower or "auto delete" in command_lower:
            days = self._extract_number(command, default=30)
            preferences.update_privacy_settings(auto_delete_days=days)
            await self._repository.save(preferences)
            return True, f"Conversations will auto-delete after {days} days."

        elif "retention" in command_lower:
            days = self._extract_number(command, default=90)
            preferences.update_privacy_settings(retention_days=days)
            await self._repository.save(preferences)
            return True, f"Conversation retention set to {days} days."

        elif "analytics opt-out" in command_lower or "disable analytics" in command_lower:
            preferences.update_privacy_settings(analytics_opt_in=False)
            await self._repository.save(preferences)
            return True, "Analytics disabled. Your data won't be used for analytics."

        elif "analytics opt-in" in command_lower or "enable analytics" in command_lower:
            preferences.update_privacy_settings(analytics_opt_in=True)
            await self._repository.save(preferences)
            return True, "Analytics enabled. This helps us improve the system."

        # Accessibility commands
        elif "high contrast" in command_lower:
            enable = "enable" in command_lower or "on" in command_lower
            preferences.update_accessibility_settings(high_contrast=enable)
            await self._repository.save(preferences)
            status = "enabled" if enable else "disabled"
            return True, f"High contrast mode {status}."

        elif "screen reader" in command_lower:
            enable = "enable" in command_lower or "on" in command_lower
            preferences.update_accessibility_settings(screen_reader=enable)
            await self._repository.save(preferences)
            status = "enabled" if enable else "disabled"
            return True, f"Screen reader optimization {status}."

        elif "font size" in command_lower:
            size = "small" if "small" in command_lower else \
                   "large" if "large" in command_lower else "medium"
            preferences.update_accessibility_settings(font_size=size)
            await self._repository.save(preferences)
            return True, f"Font size set to {size}."

        # Show current preferences
        elif "show preferences" in command_lower or "my preferences" in command_lower:
            return True, self._format_preferences_summary(preferences)

        else:
            return False, (
                "I didn't understand that preference command. Try:\n"
                "- 'Make responses more brief/detailed/technical/executive'\n"
                "- 'Set verbosity to 3'\n"
                "- 'Always use Risk Analyzer for risk questions'\n"
                "- 'Auto-delete conversations after 30 days'\n"
                "- 'Enable high contrast mode'\n"
                "- 'Show my preferences'"
            )

    async def _update_response_style(
        self,
        preferences: UserChatPreferences,
        style: str,
        message: str,
    ) -> tuple[bool, str]:
        """Update response style preference."""
        preferences.update_response_style(style)
        await self._repository.save(preferences)
        return True, message

    async def _process_agent_preference(
        self,
        preferences: UserChatPreferences,
        command: str,
    ) -> tuple[bool, str]:
        """Process agent preference command."""
        # Extract agent and query type
        # Example: "Always use Risk Analyzer for risk questions"
        agent_mapping = {
            "risk analyzer": "risk_analyzer",
            "yield optimizer": "yield_optimizer",
            "portfolio manager": "portfolio_manager",
            "security auditor": "security_auditor",
            "hunter ai": "hunter_ai",
        }

        query_type_mapping = {
            "risk": "risk",
            "yield": "yield",
            "portfolio": "portfolio",
            "security": "security",
            "trading": "trading",
        }

        agent_name = None
        for name, key in agent_mapping.items():
            if name in command.lower():
                agent_name = key
                break

        query_type = None
        for qtype, key in query_type_mapping.items():
            if qtype in command.lower():
                query_type = key
                break

        if agent_name and query_type:
            preferences.set_agent_preference(query_type, [agent_name])
            await self._repository.save(preferences)
            return True, f"I'll prefer {agent_name.replace('_', ' ').title()} for {query_type} questions."
        else:
            return False, (
                "Please specify both an agent and query type. Example:\n"
                "'Always use Risk Analyzer for risk questions'"
            )

    def _extract_number(self, text: str, default: int) -> int:
        """Extract first number from text."""
        match = re.search(r'\d+', text)
        return int(match.group()) if match else default

    def _format_preferences_summary(self, preferences: UserChatPreferences) -> str:
        """Format preferences as readable summary."""
        lines = [
            "┌─ ⚙️  Your Chat Preferences ─┐",
            "",
            "**Response Style:**",
            f"  • Style: {preferences.response_style.title()}",
            f"  • Verbosity: {preferences.verbosity_level}/5",
            f"  • Include sources: {'Yes' if preferences.include_sources else 'No'}",
            "",
            "**Agent Preferences:**",
        ]

        if preferences.preferred_agents:
            for query_type, agents in preferences.preferred_agents.items():
                agent_names = ", ".join([a.replace("_", " ").title() for a in agents])
                lines.append(f"  • {query_type.title()}: {agent_names}")
        else:
            lines.append("  • No agent preferences set")

        lines.extend([
            "",
            "**Privacy:**",
            f"  • Retention: {preferences.conversation_retention_days or 'Forever'} days",
            f"  • Auto-delete: {preferences.auto_delete_after_days or 'Disabled'} days",
            f"  • Analytics: {'Enabled' if preferences.analytics_opt_in else 'Disabled'}",
            "",
            "**Accessibility:**",
            f"  • Screen reader: {'On' if preferences.screen_reader_optimized else 'Off'}",
            f"  • High contrast: {'On' if preferences.high_contrast_mode else 'Off'}",
            f"  • Font size: {preferences.font_size.title()}",
            "",
            "To change any setting, just ask! Example:",
            "'Make responses more brief' or 'Enable high contrast mode'",
            "└─────────────────────────────────────┘",
        ])

        return "\n".join(lines)

    async def get_preferences(self, user_id: UUID) -> Optional[UserChatPreferences]:
        """
        Get user preferences.

        Args:
            user_id: User identifier

        Returns:
            UserChatPreferences or None
        """
        return await self._repository.get_by_user_id(user_id)

    async def create_default_preferences(self, user_id: UUID) -> UserChatPreferences:
        """
        Create default preferences for new user.

        Args:
            user_id: User identifier

        Returns:
            UserChatPreferences with defaults
        """
        preferences = UserChatPreferences.create_default(user_id)
        await self._repository.save(preferences)
        return preferences
