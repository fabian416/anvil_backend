"""
Template execution repository port.

Domain-defined interface for template execution persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat.template_execution import TemplateExecution


class TemplateExecutionRepository(ABC):
    """
    Port for template execution persistence.

    Abstracts storage and retrieval of template execution records.
    """

    @abstractmethod
    async def save(self, execution: TemplateExecution) -> TemplateExecution:
        """
        Save or update execution record.

        Args:
            execution: Execution entity to save

        Returns:
            Saved execution entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, execution_id: UUID) -> Optional[TemplateExecution]:
        """
        Get execution by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            TemplateExecution or None if not found
        """
        pass

    @abstractmethod
    async def get_by_template(self, template_id: UUID) -> List[TemplateExecution]:
        """
        Get all executions for a template.

        Args:
            template_id: Template identifier

        Returns:
            List of executions for the template
        """
        pass

    @abstractmethod
    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> List[TemplateExecution]:
        """
        Get all executions for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of executions for the conversation
        """
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: UUID, limit: int = 50
    ) -> List[TemplateExecution]:
        """
        Get executions for user.

        Args:
            user_id: User identifier
            limit: Maximum number of executions to return

        Returns:
            List of user's executions (most recent first)
        """
        pass

    @abstractmethod
    async def get_in_progress(self, limit: int = 100) -> List[TemplateExecution]:
        """
        Get in-progress executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of in-progress executions
        """
        pass

    @abstractmethod
    async def get_paused(self, user_id: UUID) -> List[TemplateExecution]:
        """
        Get paused executions for user.

        Args:
            user_id: User identifier

        Returns:
            List of paused executions
        """
        pass

    @abstractmethod
    async def delete(self, execution_id: UUID) -> bool:
        """
        Delete execution record.

        Args:
            execution_id: Execution identifier

        Returns:
            True if deleted, False if not found
        """
        pass
