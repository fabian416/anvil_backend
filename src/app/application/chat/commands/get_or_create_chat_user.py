"""Get or Create Chat User Command.

Handles getting existing or creating new authenticated chat users based on
legacy user ID.
"""

import logging
from uuid import UUID, uuid4

from app.domain.chat.entities import ChatUser
from app.domain.ports.chat_repository import ChatUserRepository

logger = logging.getLogger(__name__)


class GetOrCreateChatUserCommand:
    """Command to get or create authenticated chat user."""

    def __init__(self, chat_user_repository: ChatUserRepository):
        """Initialize command.

        Args:
            chat_user_repository: Repository for chat user persistence
        """
        self._repo = chat_user_repository

    async def execute(
        self, user_id: int, email: str, subscription_tier: str = "free"
    ) -> ChatUser:
        """Get existing or create new chat user.

        Args:
            user_id: Legacy users table ID (INTEGER)
            email: User email address
            subscription_tier: Subscription tier (free, premium, enterprise)

        Returns:
            ChatUser entity (existing or newly created)
        """
        # Try to get existing chat user
        existing = await self._repo.get_by_user_id(user_id)
        if existing:
            logger.debug(f"Found existing chat user for user_id={user_id}")

            # Update subscription tier if changed
            if existing.subscription_tier != subscription_tier:
                logger.info(
                    f"Updating subscription tier for user_id={user_id}: "
                    f"{existing.subscription_tier} -> {subscription_tier}"
                )
                existing.update_subscription_tier(subscription_tier)
                await self._repo.update(existing)

            # Update last seen
            await self._repo.update_last_seen(existing.id_)

            return existing

        # Create new chat user
        logger.info(f"Creating new chat user for user_id={user_id}")

        chat_user = ChatUser(
            id_=uuid4(),
            user_id=user_id,
            email=email,
            subscription_tier=subscription_tier,
        )

        return await self._repo.create(chat_user)
