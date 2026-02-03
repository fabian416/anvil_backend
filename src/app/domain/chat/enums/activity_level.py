"""
Activity level classification for context-aware agents.

Classifies users based on their interaction frequency.
"""

from enum import Enum


class ActivityLevel(Enum):
    """
    User activity level classification.

    Levels:
        VERY_ACTIVE: 5+ sessions in last 7 days - power user
        ACTIVE: 2-4 sessions in last 7 days - engaged user
        WEEKLY_ACTIVE: 1 session in last 7 days - casual user
        MONTHLY_ACTIVE: 1+ sessions in last 30 days (not weekly) - occasional
        INACTIVE: No activity in 30+ days - dormant
        REACTIVATED: Was inactive, now active again - returning
        NEW: Less than 7 days since registration - new user
    """

    VERY_ACTIVE = "very_active"
    ACTIVE = "active"
    WEEKLY_ACTIVE = "weekly_active"
    MONTHLY_ACTIVE = "monthly_active"
    INACTIVE = "inactive"
    REACTIVATED = "reactivated"
    NEW = "new"

    @classmethod
    def calculate(
        cls,
        days_since_registration: int,
        sessions_7d: int,
        sessions_30d: int,
        was_inactive: bool = False,
    ) -> "ActivityLevel":
        """
        Calculate activity level from session metrics.

        Args:
            days_since_registration: Days since user first registered
            sessions_7d: Number of chat sessions in last 7 days
            sessions_30d: Number of chat sessions in last 30 days
            was_inactive: Whether user was previously marked inactive

        Returns:
            ActivityLevel classification
        """
        # New users (< 7 days)
        if days_since_registration < 7:
            return cls.NEW

        # Reactivated users (was inactive, now has activity)
        if was_inactive and sessions_7d > 0:
            return cls.REACTIVATED

        # Very active (5+ sessions/week)
        if sessions_7d >= 5:
            return cls.VERY_ACTIVE

        # Active (2-4 sessions/week)
        if sessions_7d >= 2:
            return cls.ACTIVE

        # Weekly active (1 session/week)
        if sessions_7d >= 1:
            return cls.WEEKLY_ACTIVE

        # Monthly active (1+ in 30 days but not weekly)
        if sessions_30d >= 1:
            return cls.MONTHLY_ACTIVE

        # Inactive (no activity in 30+ days)
        return cls.INACTIVE

    @property
    def is_engaged(self) -> bool:
        """Check if user is considered engaged (active enough for retention)."""
        return self in (
            ActivityLevel.VERY_ACTIVE,
            ActivityLevel.ACTIVE,
            ActivityLevel.WEEKLY_ACTIVE,
            ActivityLevel.NEW,
            ActivityLevel.REACTIVATED,
        )

    @property
    def needs_reengagement(self) -> bool:
        """Check if user needs re-engagement efforts."""
        return self in (ActivityLevel.MONTHLY_ACTIVE, ActivityLevel.INACTIVE)

    @property
    def is_returning(self) -> bool:
        """Check if user is returning after inactivity."""
        return self == ActivityLevel.REACTIVATED

    def get_prompt_enhancement(self) -> str:
        """Get LLM prompt enhancement for this activity level."""
        enhancements = {
            ActivityLevel.VERY_ACTIVE: """
⚡ POWER USER (Very Active - 5+ sessions/week):
- Skip basic explanations
- Get straight to the point
- Offer advanced options
- Assume familiarity with DeFi concepts
""",
            ActivityLevel.ACTIVE: """
✅ ENGAGED USER (Active - 2-4 sessions/week):
- Balanced explanations
- Suggest new features they haven't tried
- Build on their experience
""",
            ActivityLevel.WEEKLY_ACTIVE: """
📊 CASUAL USER (Weekly Active):
- Moderate explanations
- Remind of key features
- Keep interactions efficient
""",
            ActivityLevel.MONTHLY_ACTIVE: """
📉 OCCASIONAL USER (Monthly Active):
- More context in responses
- Highlight what's new
- Gentle re-engagement
""",
            ActivityLevel.INACTIVE: """
😴 DORMANT USER (Inactive 30+ days):
- Welcome them back warmly
- Summarize changes since last visit
- Start with simple actions
- Don't overwhelm
""",
            ActivityLevel.REACTIVATED: """
🎉 RETURNING USER (Reactivated):
- Acknowledge their return
- Show portfolio changes while away
- Ease them back in
- Celebrate their return
""",
            ActivityLevel.NEW: """
🆕 NEW USER (< 7 days):
- Extra helpful and educational
- Guide through first actions
- Explain concepts clearly
- Be patient and encouraging
""",
        }
        return enhancements.get(self, "")
