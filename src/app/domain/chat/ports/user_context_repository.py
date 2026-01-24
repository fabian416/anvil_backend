"""
Repository port for UserContextAware entity.

Defines the interface for user context persistence operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.chat.entities.user_context_aware import UserContextAware


class UserContextRepository(Protocol):
    """
    Repository protocol for user context awareness data.
    
    This repository handles persistence of pre-computed user context
    data used for context-aware agent responses.
    """
    
    async def get_by_id(self, context_id: UUID) -> UserContextAware | None:
        """
        Get user context by its ID.
        
        Args:
            context_id: The context record ID
            
        Returns:
            UserContextAware entity or None if not found
        """
        ...
    
    async def get_by_chat_user_id(self, chat_user_id: UUID) -> UserContextAware | None:
        """
        Get user context by chat user ID.
        
        Args:
            chat_user_id: The chat user's UUID
            
        Returns:
            UserContextAware entity or None if not found
        """
        ...
    
    async def get_by_legacy_user_id(self, legacy_user_id: int) -> UserContextAware | None:
        """
        Get user context by legacy user ID (INTEGER).
        
        Args:
            legacy_user_id: The legacy user's ID
            
        Returns:
            UserContextAware entity or None if not found
        """
        ...
    
    async def save(self, context: UserContextAware) -> UserContextAware:
        """
        Save or update user context.
        
        If the context has an existing ID, it will be updated.
        Otherwise, a new record will be created.
        
        Args:
            context: The user context entity to save
            
        Returns:
            The saved user context entity
        """
        ...
    
    async def delete(self, context_id: UUID) -> bool:
        """
        Delete user context by ID.
        
        Args:
            context_id: The context record ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def get_eligible_for_update(
        self,
        before: datetime,
        limit: int = 100,
    ) -> list[UserContextAware]:
        """
        Get user contexts eligible for update.
        
        Returns contexts where next_update_eligible_at is before
        the specified timestamp, ordered by context_updated_at ASC
        (oldest first).
        
        Args:
            before: Cutoff timestamp for eligibility
            limit: Maximum number of records to return
            
        Returns:
            List of UserContextAware entities eligible for update
        """
        ...
    
    async def get_by_portfolio_state(
        self,
        portfolio_state: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """
        Get user contexts by portfolio state.
        
        Args:
            portfolio_state: The portfolio state to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of UserContextAware entities
        """
        ...
    
    async def get_by_activity_level(
        self,
        activity_level: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """
        Get user contexts by activity level.
        
        Args:
            activity_level: The activity level to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of UserContextAware entities
        """
        ...
    
    async def get_by_user_type(
        self,
        user_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """
        Get user contexts by user type.
        
        Args:
            user_type: The user type to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of UserContextAware entities
        """
        ...
    
    async def count_by_portfolio_state(self) -> dict[str, int]:
        """
        Count users by portfolio state.
        
        Returns:
            Dictionary mapping portfolio state to count
        """
        ...
    
    async def count_by_activity_level(self) -> dict[str, int]:
        """
        Count users by activity level.
        
        Returns:
            Dictionary mapping activity level to count
        """
        ...
    
    async def count_by_user_type(self) -> dict[str, int]:
        """
        Count users by user type.
        
        Returns:
            Dictionary mapping user type to count
        """
        ...
    
    async def get_inactive_users(
        self,
        days_inactive: int = 30,
        limit: int = 100,
    ) -> list[UserContextAware]:
        """
        Get users who have been inactive for specified days.
        
        Args:
            days_inactive: Minimum days since last activity
            limit: Maximum number of records to return
            
        Returns:
            List of inactive UserContextAware entities
        """
        ...
    
    async def exists_for_chat_user(self, chat_user_id: UUID) -> bool:
        """
        Check if context exists for a chat user.
        
        Args:
            chat_user_id: The chat user's UUID
            
        Returns:
            True if context exists, False otherwise
        """
        ...
