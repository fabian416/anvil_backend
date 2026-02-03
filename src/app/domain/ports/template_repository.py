"""
Template repository port.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities.chat.conversation_template import ConversationTemplate


class TemplateRepository(ABC):
    """
    Port for conversation template persistence.

    Domain-defined interface for storing and retrieving conversation templates.
    """

    @abstractmethod
    async def get_by_id(self, template_id: UUID) -> Optional[ConversationTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            ConversationTemplate or None if not found
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ConversationTemplate]:
        """
        Get template by name.

        Args:
            name: Template name

        Returns:
            ConversationTemplate or None if not found
        """
        pass

    @abstractmethod
    async def get_available_for_user(
        self,
        user_id: UUID,
        category: Optional[str] = None,
    ) -> List[ConversationTemplate]:
        """
        Get templates available for user (public + user's private).

        Args:
            user_id: User identifier
            category: Optional category filter

        Returns:
            List of available templates
        """
        pass

    @abstractmethod
    async def get_by_creator(self, user_id: UUID) -> List[ConversationTemplate]:
        """
        Get templates created by user.

        Args:
            user_id: User identifier

        Returns:
            List of user's templates
        """
        pass

    @abstractmethod
    async def save(self, template: ConversationTemplate) -> ConversationTemplate:
        """
        Save or update template.

        Args:
            template: Template to save

        Returns:
            Saved template
        """
        pass

    @abstractmethod
    async def delete(self, template_id: UUID) -> bool:
        """
        Delete template.

        Args:
            template_id: Template identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_popular_templates(
        self, limit: int = 10
    ) -> List[ConversationTemplate]:
        """
        Get most popular templates by usage count.

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of popular templates
        """
        pass
