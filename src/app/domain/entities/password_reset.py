"""
PasswordReset entity for the hexagonal architecture.
Based on the BaseAPI PasswordReset model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.base import Entity
from app.domain.value_objects.password_reset_id import PasswordResetId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.reset_token import ResetToken
from app.domain.value_objects.expiration_time import ExpirationTime
from app.domain.value_objects.reset_status import ResetStatus
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class PasswordReset(Entity[PasswordResetId]):
    """
    PasswordReset entity representing a password reset in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    token: ResetToken
    expires_at: ExpirationTime
    is_used: ResetStatus
    created_at: CreatedAt
    updated_at: UpdatedAt
